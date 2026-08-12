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
from pathlib import Path
from typing import Any

from resolveflow.domain.hashing import checksum

ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "data" / "corpus" / "embeddings"
# Cohere caps texts per embed request; batching keeps the corpus to one call.
MAX_TEXTS_PER_CALL = 96


def _l2_normalize(vector: Any) -> tuple[float, ...]:
    """Unit-normalize so the retriever's dot product is exactly cosine similarity.

    Normalization is monotone in cosine, so it changes no ranking; it only makes
    the engine's existing dot-product assumption true for provider vectors.
    """
    values = [float(value) for value in vector]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return tuple(value / norm for value in values)


class EmbeddingCacheMiss(RuntimeError):
    """Raised in offline mode when a vector is absent and no provider is allowed."""


class CachedEmbeddingAdapter:
    """EmbeddingPort backed by a JSON vector cache, falling through to Cohere.

    ``allow_provider=False`` turns the adapter into a strict replay: any cache
    miss raises instead of quietly spending an API call.
    """

    def __init__(
        self,
        cache_path: Path,
        *,
        client: Any | None = None,
        model: str = "embed-v4.0",
        dimension: int = 1024,
        allow_provider: bool = False,
    ) -> None:
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
            if raw.get("model") != model:
                raise ValueError(f"embedding cache model mismatch: {raw.get('model')} != {model}")
            self.dimension = int(raw.get("dimension", dimension))
            self._vectors = {
                key: tuple(float(value) for value in vector)
                for key, vector in raw["vectors"].items()
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
        self._cache_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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

    def _fetch(self, texts: tuple[str, ...], input_type: str) -> None:
        missing = [text for text in texts if self._key(text, input_type) not in self._vectors]
        if not missing:
            return
        if not self._allow_provider or self._client is None:
            raise EmbeddingCacheMiss(
                f"{len(missing)} text(s) absent from the embedding cache and provider "
                f"calls are disabled for this run"
            )
        for start in range(0, len(missing), MAX_TEXTS_PER_CALL):
            batch = missing[start : start + MAX_TEXTS_PER_CALL]
            response = self._client.embed(
                model=self.model,
                texts=list(batch),
                input_type=input_type,
                output_dimension=self.dimension,
                embedding_types=["float"],
            )
            self.provider_embed_calls += 1
            vectors = response.embeddings.float
            if len(vectors) != len(batch):
                raise RuntimeError("embed response length does not match the request batch")
            for text, vector in zip(batch, vectors, strict=True):
                self._vectors[self._key(text, input_type)] = _l2_normalize(vector)
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

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        self._fetch(texts, "search_document")
        return tuple(self._vectors[self._key(text, "search_document")] for text in texts)

    def embed_query(self, text: str) -> tuple[float, ...]:
        self._fetch((text,), "search_query")
        return self._vectors[self._key(text, "search_query")]
