from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def tokens(text: str) -> tuple[str, ...]:
    return tuple(TOKEN.findall(text.lower()))


class FixtureEmbeddingAdapter:
    """Deterministic local embedding used by default; values are not provider results."""

    model = "fixture-token-hash-1.0"
    dimension = 32

    def _embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimension
        for token in tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimension
            sign = 1.0 if digest[2] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return tuple(value / norm for value in vector)

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(self._embed(text) for text in texts)

    def embed_query(self, text: str) -> tuple[float, ...]:
        return self._embed(text)


class FixtureRerankAdapter:
    """Stable term-overlap reranker; it never represents a Cohere measurement."""

    model = "fixture-overlap-rerank-1.0"

    def rerank(
        self, query: str, documents: tuple[str, ...], top_n: int
    ) -> tuple[tuple[int, float], ...]:
        query_counts = Counter(tokens(query))
        scored: list[tuple[int, float]] = []
        for index, document in enumerate(documents):
            document_counts = Counter(tokens(document))
            overlap = sum(
                min(count, document_counts.get(token, 0)) for token, count in query_counts.items()
            )
            score = overlap / max(1, sum(query_counts.values()))
            scored.append((index, score))
        return tuple(sorted(scored, key=lambda item: (-item[1], item[0]))[:top_n])
