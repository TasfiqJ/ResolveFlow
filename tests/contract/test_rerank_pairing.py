from __future__ import annotations

from types import SimpleNamespace

import pytest
from resolveflow.retrieval.cohere import CohereRerankAdapter, ProviderAdapterError


class SpyClient:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[dict[str, object]] = []
        self.fail = fail

    def rerank(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.fail:
            raise TimeoutError("secret provider detail")
        documents = kwargs["documents"]
        assert isinstance(documents, list)
        return SimpleNamespace(
            results=[
                SimpleNamespace(index=index, relevance_score=1 / (index + 1))
                for index in range(len(documents))
            ]
        )


def test_fast_and_pro_receive_identical_candidate_payloads() -> None:
    spy = SpyClient()
    documents = ("first", "second")
    CohereRerankAdapter(spy, "rerank-v4.0-fast").rerank("query", documents, 2)
    CohereRerankAdapter(spy, "rerank-v4.0-pro").rerank("query", documents, 2)
    assert spy.calls[0]["documents"] == spy.calls[1]["documents"]
    assert spy.calls[0]["query"] == spy.calls[1]["query"]
    assert spy.calls[0]["top_n"] == spy.calls[1]["top_n"]


def test_rerank_errors_are_normalized() -> None:
    with pytest.raises(ProviderAdapterError) as error:
        CohereRerankAdapter(SpyClient(fail=True), "rerank-v4.0-fast").rerank(
            "query", ("document",), 1
        )
    assert str(error.value) == "rerank provider request failed for rerank-v4.0-fast"
