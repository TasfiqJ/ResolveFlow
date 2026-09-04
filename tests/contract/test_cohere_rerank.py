from __future__ import annotations

from types import SimpleNamespace

import pytest
from resolveflow.retrieval.cohere import CohereRerankAdapter, ProviderAdapterError


class SpyClient:
    def __init__(self, results: tuple[tuple[object, float], ...]) -> None:
        self.results = results
        self.calls: list[dict[str, object]] = []

    def rerank(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            results=[
                SimpleNamespace(index=index, relevance_score=score) for index, score in self.results
            ]
        )


def test_rerank_sends_the_bounded_default_to_cohere() -> None:
    client = SpyClient(((1, 0.9), (0, 0.2)))

    result = CohereRerankAdapter(client, "rerank-v4.0-fast").rerank("query", ("first", "second"), 2)

    assert result == ((1, 0.9), (0, 0.2))
    assert client.calls == [
        {
            "model": "rerank-v4.0-fast",
            "query": "query",
            "documents": ["first", "second"],
            "top_n": 2,
            "max_tokens_per_doc": 4096,
            "request_options": {"timeout_in_seconds": 30, "max_retries": 0},
        }
    ]


def test_rerank_accepts_a_custom_positive_document_token_limit() -> None:
    client = SpyClient(((0, 1.0),))

    CohereRerankAdapter(client, "rerank-v4.0-pro", max_tokens_per_doc=2048).rerank(
        "query", ("document",), 1
    )

    assert client.calls[0]["max_tokens_per_doc"] == 2048


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_rerank_rejects_invalid_document_token_limits(value: object) -> None:
    client = SpyClient(((0, 1.0),))

    with pytest.raises(ValueError, match="positive integer"):
        CohereRerankAdapter(
            client,
            "rerank-v4.0-fast",
            max_tokens_per_doc=value,  # type: ignore[arg-type]
        )

    assert client.calls == []


@pytest.mark.parametrize(
    "results",
    [
        ((0, 0.9), (0, 0.8)),
        ((-1, 0.9),),
        ((2, 0.9),),
        ((False, 0.9),),
        (("0", 0.9),),
    ],
)
def test_rerank_rejects_untrusted_result_indexes(
    results: tuple[tuple[object, float], ...],
) -> None:
    client = SpyClient(results)

    with pytest.raises(ProviderAdapterError) as error:
        CohereRerankAdapter(client, "rerank-v4.0-fast").rerank("query", ("first", "second"), 2)

    assert str(error.value) == "rerank provider request failed for rerank-v4.0-fast"


@pytest.mark.parametrize(
    "results",
    [
        ((0, 0.9),),
        ((0, float("nan")), (1, 0.2)),
        ((0, float("inf")), (1, 0.2)),
        ((0, -0.1), (1, 0.2)),
        ((0, 1.1), (1, 0.2)),
        ((0, True), (1, 0.2)),
        ((0, "0.9"), (1, 0.2)),
        ((0, 0.2), (1, 0.9)),
    ],
)
def test_rerank_rejects_incomplete_or_nonfinite_results(
    results: tuple[tuple[object, float], ...],
) -> None:
    client = SpyClient(results)

    with pytest.raises(ProviderAdapterError):
        CohereRerankAdapter(client, "rerank-v4.0-fast").rerank("query", ("first", "second"), 2)


@pytest.mark.parametrize("top_n", [0, -1, True, 3])
def test_rerank_rejects_invalid_top_n_before_provider_call(top_n: object) -> None:
    client = SpyClient(((0, 1.0),))

    with pytest.raises(ValueError, match="no greater than document count"):
        CohereRerankAdapter(client, "rerank-v4.0-fast").rerank(
            "query",
            ("first", "second"),
            top_n,  # type: ignore[arg-type]
        )

    assert client.calls == []


def test_fast_and_pro_keep_the_same_non_model_payload() -> None:
    client = SpyClient(((0, 1.0),))

    CohereRerankAdapter(client, "rerank-v4.0-fast").rerank("query", ("document",), 1)
    CohereRerankAdapter(client, "rerank-v4.0-pro").rerank("query", ("document",), 1)

    fast_payload = {key: value for key, value in client.calls[0].items() if key != "model"}
    pro_payload = {key: value for key, value in client.calls[1].items() if key != "model"}
    assert fast_payload == pro_payload
