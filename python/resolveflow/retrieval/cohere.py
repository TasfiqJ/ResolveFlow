from __future__ import annotations

from typing import Any


class ProviderAdapterError(RuntimeError):
    def __init__(self, endpoint: str, model: str) -> None:
        super().__init__(f"{endpoint} provider request failed for {model}")
        self.endpoint = endpoint
        self.model = model


class CohereEmbedAdapter:
    """Cohere SDK adapter. Construction is explicit so fixture/CI paths cannot call it."""

    model = "embed-v4.0"

    def __init__(self, client: Any, dimension: int = 1024) -> None:
        self._client = client
        self._dimension = dimension

    def _embed(self, texts: tuple[str, ...], input_type: str) -> tuple[tuple[float, ...], ...]:
        try:
            response = self._client.embed(
                model=self.model,
                texts=list(texts),
                input_type=input_type,
                output_dimension=self._dimension,
                embedding_types=["float"],
            )
        except Exception as exc:
            raise ProviderAdapterError("embed", self.model) from exc
        values = response.embeddings.float
        return tuple(tuple(float(value) for value in vector) for vector in values)

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return self._embed(texts, "search_document")

    def embed_query(self, text: str) -> tuple[float, ...]:
        return self._embed((text,), "search_query")[0]


class CohereRerankAdapter:
    def __init__(self, client: Any, model: str) -> None:
        if model not in {"rerank-v4.0-fast", "rerank-v4.0-pro"}:
            raise ValueError("unsupported Rerank policy model")
        self._client = client
        self.model = model

    def rerank(
        self, query: str, documents: tuple[str, ...], top_n: int
    ) -> tuple[tuple[int, float], ...]:
        try:
            response = self._client.rerank(
                model=self.model, query=query, documents=list(documents), top_n=top_n
            )
        except Exception as exc:
            raise ProviderAdapterError("rerank", self.model) from exc
        return tuple((int(item.index), float(item.relevance_score)) for item in response.results)
