from __future__ import annotations

from typing import Protocol


class EmbeddingPort(Protocol):
    model: str
    supports_deadline: bool

    def embed_documents(
        self, texts: tuple[str, ...], *, timeout_seconds: float | None = None
    ) -> tuple[tuple[float, ...], ...]: ...

    def embed_query(
        self, text: str, *, timeout_seconds: float | None = None
    ) -> tuple[float, ...]: ...


class RerankPort(Protocol):
    model: str
    supports_deadline: bool

    def rerank(
        self,
        query: str,
        documents: tuple[str, ...],
        top_n: int,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[tuple[int, float], ...]: ...
