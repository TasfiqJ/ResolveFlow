from __future__ import annotations

from types import SimpleNamespace

import pytest
from resolveflow.retrieval.cohere import CohereEmbedAdapter, ProviderAdapterError


class EmbedSpy:
    def __init__(self, fail: bool = False, vectors: object | None = None) -> None:
        self.fail = fail
        self.vectors = vectors
        self.calls: list[dict[str, object]] = []

    def embed(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.fail:
            raise TimeoutError("secret provider detail")
        texts = kwargs["texts"]
        assert isinstance(texts, list)
        vectors = self.vectors
        if vectors is None:
            vectors = [[0.25, 0.75] for _ in texts]
        return SimpleNamespace(embeddings=SimpleNamespace(float=vectors))


def test_embed_v4_maps_query_and_document_input_types() -> None:
    spy = EmbedSpy()
    adapter = CohereEmbedAdapter(spy, dimension=2)
    assert adapter.embed_documents(("document",)) == ((0.25, 0.75),)
    assert adapter.embed_query("query") == (0.25, 0.75)
    assert spy.calls[0]["input_type"] == "search_document"
    assert spy.calls[1]["input_type"] == "search_query"
    assert all(call["model"] == "embed-v4.0" for call in spy.calls)
    assert all(call["embedding_types"] == ["float"] for call in spy.calls)
    assert all(
        call["request_options"] == {"timeout_in_seconds": 30, "max_retries": 0}
        for call in spy.calls
    )


def test_embed_errors_are_normalized_without_provider_detail() -> None:
    with pytest.raises(ProviderAdapterError) as error:
        CohereEmbedAdapter(EmbedSpy(fail=True), dimension=2).embed_query("query")
    assert str(error.value) == "embed provider request failed for embed-v4.0"


@pytest.mark.parametrize(
    "vectors",
    [
        [],
        [[0.25, 0.75], [0.5, 0.5]],
        [[0.25]],
        [[0.25, float("nan")]],
        [[0.25, float("inf")]],
        [["not-a-number", 0.75]],
        [[True, 0.75]],
        [[0.0, 0.0]],
        [{0: 0.25, 1: 0.75}],
        None,
    ],
)
def test_malformed_embed_shapes_are_safe_typed_failures(vectors: object) -> None:
    spy = EmbedSpy(vectors=vectors)
    if vectors is None:
        spy.embed = lambda **_: SimpleNamespace(embeddings=SimpleNamespace())  # type: ignore[method-assign]

    with pytest.raises(ProviderAdapterError) as error:
        CohereEmbedAdapter(spy, dimension=2).embed_query("query")

    assert str(error.value) == "embed provider request failed for embed-v4.0"
