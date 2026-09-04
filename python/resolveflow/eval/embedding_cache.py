"""Disk-cached Embed v4 vectors.

The corpus is embedded exactly once. Both builds of the A/B read the same cached
vectors, so the guarded/unguarded comparison cannot be confounded by two
different embeddings of the same text, and no embed call is spent twice.

Cache keys are content checksums, so an edited document misses the cache and is
re-embedded, while an unchanged document never is.
"""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Any

from resolveflow.domain.hashing import checksum
from resolveflow.retrieval.cohere import read_float_embeddings

ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "data" / "corpus" / "embeddings"
# Cohere caps texts per embed request; batching keeps the corpus to one call.
MAX_TEXTS_PER_CALL = 96


def _l2_normalize(vector: Any, *, dimension: int, normalize: bool = True) -> tuple[float, ...]:
    """Unit-normalize so the retriever's dot product is exactly cosine similarity.

    Normalization is monotone in cosine, so it changes no ranking; it only makes
    the engine's existing dot-product assumption true for provider vectors.
    """
    if not isinstance(vector, list | tuple):
        raise ValueError("embedding vector must be an array")
    if len(vector) != dimension:
        raise ValueError("embedding vector dimension does not match cache policy")
    if any(isinstance(value, bool) or not isinstance(value, int | float) for value in vector):
        raise ValueError("embedding vector coordinates must be numeric")
    values = [float(value) for value in vector]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("embedding vector coordinates must be finite")
    norm = math.hypot(*values)
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("embedding vector must have a finite non-zero norm")
    return tuple(value / norm for value in values) if normalize else tuple(values)


class EmbeddingCacheMiss(RuntimeError):
    """Raised in offline mode when a vector is absent and no provider is allowed."""


class CachedEmbeddingAdapter:
    """EmbeddingPort backed by a JSON vector cache, falling through to Cohere.

    ``allow_provider=False`` turns the adapter into a strict replay: any cache
    miss raises instead of quietly spending an API call.
    """

    supports_deadline = True
    minimum_timeout_seconds = 1.0

    def __init__(
        self,
        cache_path: Path,
        *,
        client: Any | None = None,
        model: str = "embed-v4.0",
        dimension: int = 1024,
        allow_provider: bool = False,
    ) -> None:
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0:
            raise ValueError("embedding cache dimension must be a positive integer")
        self.model = model
        self.dimension = dimension
        self._cache_path = cache_path
        self._client = client
        self._allow_provider = allow_provider
        self._vectors: dict[str, tuple[float, ...]] = {}
        self._dirty = False
        self.provider_embed_calls = 0
        if cache_path.exists():
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or set(raw) != {
                "schema_version",
                "model",
                "dimension",
                "vector_count",
                "vectors",
            }:
                raise ValueError("embedding cache has an unexpected schema")
            if raw.get("schema_version") != "1.0":
                raise ValueError("embedding cache schema version is unsupported")
            if raw.get("model") != model:
                raise ValueError(f"embedding cache model mismatch: {raw.get('model')} != {model}")
            if raw.get("dimension") != dimension:
                raise ValueError("embedding cache dimension does not match configured policy")
            vectors = raw.get("vectors")
            if not isinstance(vectors, dict) or raw.get("vector_count") != len(vectors):
                raise ValueError("embedding cache vector count is inconsistent")
            if any(not re.fullmatch(r"sha256:[0-9a-f]{64}", key) for key in vectors):
                raise ValueError("embedding cache contains an invalid content key")
            self._vectors = {
                key: _l2_normalize(vector, dimension=self.dimension, normalize=False)
                for key, vector in vectors.items()
            }

    # -- keys ----------------------------------------------------------------

    @staticmethod
    def _key(text: str, input_type: str) -> str:
        return checksum({"input_type": input_type, "text": text})

    # -- persistence ---------------------------------------------------------

    def save(self) -> Path:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "model": self.model,
            "dimension": self.dimension,
            "vector_count": len(self._vectors),
            "vectors": {key: list(value) for key, value in sorted(self._vectors.items())},
        }
        self._cache_path.write_bytes(
            (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        self._dirty = False
        return self._cache_path

    @property
    def dirty(self) -> bool:
        return self._dirty

    def cached_vector_count(self) -> int:
        return len(self._vectors)

    def cache_hash(self) -> str:
        return checksum({key: list(value) for key, value in sorted(self._vectors.items())})

    # -- embedding -----------------------------------------------------------

    def _fetch(
        self, texts: tuple[str, ...], input_type: str, *, timeout_seconds: float | None = None
    ) -> None:
        missing = [text for text in texts if self._key(text, input_type) not in self._vectors]
        if not missing:
            return
        if not self._allow_provider or self._client is None:
            raise EmbeddingCacheMiss(
                f"{len(missing)} text(s) absent from the embedding cache and provider "
                f"calls are disabled for this run"
            )
        deadline = time.perf_counter() + timeout_seconds if timeout_seconds is not None else None
        if timeout_seconds is not None and timeout_seconds < self.minimum_timeout_seconds:
            raise TimeoutError("embedding deadline is below the SDK's one-second minimum")
        pending_vectors: dict[str, tuple[float, ...]] = {}
        for start in range(0, len(missing), MAX_TEXTS_PER_CALL):
            batch = missing[start : start + MAX_TEXTS_PER_CALL]
            remaining = deadline - time.perf_counter() if deadline is not None else None
            if remaining is not None and remaining < self.minimum_timeout_seconds:
                raise TimeoutError("embedding deadline exhausted before the next batch")
            request_options = (
                {"timeout_in_seconds": int(remaining), "max_retries": 0}
                if remaining is not None
                else None
            )
            response = self._client.embed(
                model=self.model,
                texts=list(batch),
                input_type=input_type,
                output_dimension=self.dimension,
                embedding_types=["float"],
                **({"request_options": request_options} if request_options is not None else {}),
            )
            self.provider_embed_calls += 1
            vectors = read_float_embeddings(response)
            if len(vectors) != len(batch):
                raise RuntimeError("embed response length does not match the request batch")
            for text, vector in zip(batch, vectors, strict=True):
                pending_vectors[self._key(text, input_type)] = _l2_normalize(
                    vector, dimension=self.dimension
                )
        self._vectors.update(pending_vectors)
        self._dirty = True

    def prewarm(
        self,
        *,
        documents: tuple[str, ...] = (),
        queries: tuple[str, ...] = (),
    ) -> int:
        """Embed every text in as few batched calls as possible.

        Call this once, before any run. Afterwards the corpus loader's
        one-text-at-a-time embed calls all hit the cache and cost nothing, which
        is the difference between two provider calls and thirty.

        Returns the number of provider calls this prewarm consumed.
        """
        before = self.provider_embed_calls
        if documents:
            self._fetch(tuple(dict.fromkeys(documents)), "search_document")
        if queries:
            self._fetch(tuple(dict.fromkeys(queries)), "search_query")
        return self.provider_embed_calls - before

    def embed_documents(
        self, texts: tuple[str, ...], *, timeout_seconds: float | None = None
    ) -> tuple[tuple[float, ...], ...]:
        self._fetch(texts, "search_document", timeout_seconds=timeout_seconds)
        return tuple(self._vectors[self._key(text, "search_document")] for text in texts)

    def embed_query(self, text: str, *, timeout_seconds: float | None = None) -> tuple[float, ...]:
        self._fetch((text,), "search_query", timeout_seconds=timeout_seconds)
        return self._vectors[self._key(text, "search_query")]
