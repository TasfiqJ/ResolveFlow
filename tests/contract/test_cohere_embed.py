from __future__ import annotations

from types import SimpleNamespace

import pytest
from resolveflow.retrieval.cohere import CohereEmbedAdapter, ProviderAdapterError


class EmbedSpy:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    def embed(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.fail:
            raise TimeoutError("secret provider detail")
        texts = kwargs["texts"]
        assert isinstance(texts, list)
        return SimpleNamespace(embeddings=SimpleNamespace(float=[[0.25, 0.75] for _ in texts]))


def test_embed_v4_maps_query_and_document_input_types() -> None:
    spy = EmbedSpy()
    adapter = CohereEmbedAdapter(spy, dimension=2)
    assert adapter.embed_documents(("document",)) == ((0.25, 0.75),)
    assert adapter.embed_query("query") == (0.25, 0.75)
    assert spy.calls[0]["input_type"] == "search_document"
    assert spy.calls[1]["input_type"] == "search_query"
    assert all(call["model"] == "embed-v4.0" for call in spy.calls)
    assert all(call["embedding_types"] == ["float"] for call in spy.calls)


def test_embed_errors_are_normalized_without_provider_detail() -> None:
    with pytest.raises(ProviderAdapterError) as error:
        CohereEmbedAdapter(EmbedSpy(fail=True), dimension=2).embed_query("query")
    assert str(error.value) == "embed provider request failed for embed-v4.0"
