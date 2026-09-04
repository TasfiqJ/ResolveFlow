from __future__ import annotations

import math
from typing import Any

from resolveflow.eval.budget import BudgetExceeded


def read_float_embeddings(response: Any) -> Any:
    """Read float vectors out of an Embed v2 response.

    The SDK models the response field as ``float_`` with the wire alias
    ``"float"``, because ``float`` is a Python builtin. Reading ``.float``
    raises AttributeError -- which surfaces wrapped as a provider error, after
    the embed calls have already been spent. Read the real attribute, and keep
    fallbacks so a future SDK rename does not silently cost a run.
    """
    embeddings = getattr(response, "embeddings", None)
    if embeddings is None:
        raise AttributeError("embed response carried no embeddings")
    for name in ("float_", "float"):
        values = getattr(embeddings, name, None)
        if values is not None:
            return values
    if isinstance(embeddings, dict):
        values = embeddings.get("float") or embeddings.get("float_")
        if values is not None:
            return values
    raise AttributeError(
        "embed response exposed no float embeddings; "
        f"available: {sorted(type(embeddings).model_fields)}"
    )


class ProviderAdapterError(RuntimeError):
    def __init__(
        self,
        endpoint: str,
        model: str,
        *,
        failure_stage: str | None = None,
        provider_call_count: int = 0,
        provider_call_ms: float = 0.0,
    ) -> None:
        super().__init__(f"{endpoint} provider request failed for {model}")
        self.endpoint = endpoint
        self.model = model
        self.failure_stage = failure_stage
        self.provider_call_count = provider_call_count
        self.provider_call_ms = provider_call_ms


class CohereEmbedAdapter:
    """Cohere SDK adapter. Construction is explicit so fixture/CI paths cannot call it."""

    provider_backed = True
    minimum_timeout_seconds = 1.0

    def __init__(
        self,
        client: Any,
        dimension: int = 1024,
        *,
        model: str = "embed-v4.0",
        timeout_seconds: int = 30,
    ) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, int)
            or timeout_seconds <= 0
        ):
            raise ValueError("embed timeout_seconds must be a positive integer")
        self._client = client
        self._dimension = dimension
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.supports_deadline = True

    def _embed(
        self,
        texts: tuple[str, ...],
        input_type: str,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[tuple[float, ...], ...]:
        effective_timeout = min(
            self.timeout_seconds,
            int(timeout_seconds) if timeout_seconds is not None else self.timeout_seconds,
        )
        if effective_timeout <= 0:
            raise ProviderAdapterError("embed", self.model)
        try:
            response = self._client.embed(
                model=self.model,
                texts=list(texts),
                input_type=input_type,
                output_dimension=self._dimension,
                embedding_types=["float"],
                request_options={
                    "timeout_in_seconds": effective_timeout,
                    "max_retries": 0,
                },
            )
            raw_vectors = read_float_embeddings(response)
            if not isinstance(raw_vectors, list | tuple) or len(raw_vectors) != len(texts):
                raise ValueError("embed response cardinality does not match request")
            vectors: list[tuple[float, ...]] = []
            for raw_vector in raw_vectors:
                if not isinstance(raw_vector, list | tuple):
                    raise ValueError("embed response vector is not an array")
                if len(raw_vector) != self._dimension:
                    raise ValueError("embed response vector dimension does not match policy")
                if any(
                    isinstance(value, bool) or not isinstance(value, int | float)
                    for value in raw_vector
                ):
                    raise ValueError("embed response coordinates must be numeric")
                vector = tuple(float(value) for value in raw_vector)
                if any(not math.isfinite(value) for value in vector):
                    raise ValueError("embed response contains non-finite coordinates")
                norm = math.hypot(*vector)
                if not math.isfinite(norm) or norm <= 0.0:
                    raise ValueError("embed response vector must have a finite non-zero norm")
                vectors.append(vector)
            return tuple(vectors)
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise ProviderAdapterError("embed", self.model) from exc

    def embed_documents(
        self, texts: tuple[str, ...], *, timeout_seconds: float | None = None
    ) -> tuple[tuple[float, ...], ...]:
        return self._embed(texts, "search_document", timeout_seconds=timeout_seconds)

    def embed_query(self, text: str, *, timeout_seconds: float | None = None) -> tuple[float, ...]:
        return self._embed((text,), "search_query", timeout_seconds=timeout_seconds)[0]


class CohereRerankAdapter:
    provider_backed = True
    minimum_timeout_seconds = 1.0

    def __init__(
        self,
        client: Any,
        model: str,
        *,
        max_tokens_per_doc: int = 4096,
        timeout_seconds: int = 30,
    ) -> None:
        if model not in {"rerank-v4.0-fast", "rerank-v4.0-pro"}:
            raise ValueError("unsupported Rerank policy model")
        if (
            isinstance(max_tokens_per_doc, bool)
            or not isinstance(max_tokens_per_doc, int)
            or max_tokens_per_doc <= 0
        ):
            raise ValueError("max_tokens_per_doc must be a positive integer")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, int)
            or timeout_seconds <= 0
        ):
            raise ValueError("rerank timeout_seconds must be a positive integer")
        self._client = client
        self.model = model
        self.max_tokens_per_doc = max_tokens_per_doc
        self.timeout_seconds = timeout_seconds
        self.supports_deadline = True

    def rerank(
        self,
        query: str,
        documents: tuple[str, ...],
        top_n: int,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[tuple[int, float], ...]:
        if (
            isinstance(top_n, bool)
            or not isinstance(top_n, int)
            or top_n <= 0
            or top_n > len(documents)
        ):
            raise ValueError("top_n must be a positive integer no greater than document count")
        effective_timeout = min(
            self.timeout_seconds,
            int(timeout_seconds) if timeout_seconds is not None else self.timeout_seconds,
        )
        if effective_timeout <= 0:
            raise ProviderAdapterError("rerank", self.model)
        try:
            response = self._client.rerank(
                model=self.model,
                query=query,
                documents=list(documents),
                top_n=top_n,
                max_tokens_per_doc=self.max_tokens_per_doc,
                request_options={
                    "timeout_in_seconds": effective_timeout,
                    "max_retries": 0,
                },
            )
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise ProviderAdapterError("rerank", self.model) from exc
        try:
            results = tuple(response.results)
            if len(results) != top_n:
                raise ValueError("rerank result count must exactly match top_n")
            indexes: list[int] = []
            scores: list[float] = []
            seen_indexes: set[int] = set()
            for item in results:
                if isinstance(item.index, bool) or not isinstance(item.index, int):
                    raise ValueError("rerank result index must be an integer")
                index = item.index
                if index < 0 or index >= len(documents):
                    raise ValueError("rerank result index is outside the document payload")
                if index in seen_indexes:
                    raise ValueError("rerank result indexes must be unique")
                raw_score = item.relevance_score
                if isinstance(raw_score, bool) or not isinstance(raw_score, int | float):
                    raise ValueError("rerank relevance scores must be numeric")
                score = float(raw_score)
                if not math.isfinite(score) or not 0.0 <= score <= 1.0:
                    raise ValueError("rerank relevance scores must be finite and in [0, 1]")
                seen_indexes.add(index)
                indexes.append(index)
                scores.append(score)
            if any(left < right for left, right in zip(scores, scores[1:], strict=False)):
                raise ValueError("rerank results must be ordered by descending relevance")
            return tuple(zip(indexes, scores, strict=True))
        except Exception as exc:
            raise ProviderAdapterError("rerank", self.model) from exc
