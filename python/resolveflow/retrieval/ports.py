from __future__ import annotations

from typing import Protocol


class EmbeddingPort(Protocol):
    model: str

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...

    def embed_query(self, text: str) -> tuple[float, ...]: ...


class RerankPort(Protocol):
    model: str

    def rerank(
        self, query: str, documents: tuple[str, ...], top_n: int
    ) -> tuple[tuple[int, float], ...]: ...
