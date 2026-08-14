from __future__ import annotations

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
    def __init__(self, endpoint: str, model: str) -> None:
        super().__init__(f"{endpoint} provider request failed for {model}")
        self.endpoint = endpoint
        self.model = model


class CohereEmbedAdapter:
    """Cohere SDK adapter. Construction is explicit so fixture/CI paths cannot call it."""

    def __init__(
        self,
        client: Any,
        dimension: int = 1024,
        *,
        model: str = "embed-v4.0",
    ) -> None:
        self._client = client
        self._dimension = dimension
        self.model = model

    def _embed(self, texts: tuple[str, ...], input_type: str) -> tuple[tuple[float, ...], ...]:
        try:
            response = self._client.embed(
                model=self.model,
                texts=list(texts),
                input_type=input_type,
                output_dimension=self._dimension,
                embedding_types=["float"],
            )
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise ProviderAdapterError("embed", self.model) from exc
        values = read_float_embeddings(response)
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
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise ProviderAdapterError("rerank", self.model) from exc
        return tuple((int(item.index), float(item.relevance_score)) for item in response.results)
