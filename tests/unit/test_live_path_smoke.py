"""Exercise the live `--provider cohere` code path against a stub Cohere client.

The live A/B spends a metered trial key. Discovering an adapter bug by burning
calls is the expensive way to find it. This test drives the same path the live
run takes -- CohereChatAdapter, CohereRerankAdapter, the cached embedder in
strict mode, and the budget wrapper -- with a stub that returns the response
shapes the real SDK returns, so a shape or wiring regression fails here first.

It makes no network call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from resolveflow.eval.ab_runner import ABHarness, run_ab
from resolveflow.eval.budget import BudgetedCohereClient
from resolveflow.eval.corpus import ATTACK_MANIFEST, BASE_MANIFEST
from resolveflow.eval.embedding_cache import CachedEmbeddingAdapter
from resolveflow.eval.scenarios import all_scenarios, scenario_queries
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter

FINDINGS_JSON = json.dumps(
    {
        "schema_version": "1.0",
        "claims": [],
        "citations": [],
        "unknowns": [
            {
                "unknown_id": "unknown_cluster_id",
                "field": "cluster_id",
                "text": "The cluster identifier was not supplied.",
                "reason_code": "missing_field",
            }
        ],
        "requested_proposal": "none",
    }
)


class _Content:
    def __init__(self, text: str) -> None:
        self.text = text


class _Message:
    def __init__(self, text: str) -> None:
        self.content = [_Content(text)]
        self.tool_calls: list[Any] = []
        self.citations: list[Any] = []


class _Usage:
    """Reports token counts derived from the actual payload size.

    The first version of this stub returned a flat 120 input tokens. That is why
    it failed to catch the budget bug that voided the first live run: the real
    evidence prompt is 3.3k-5.1k input tokens against a 4096 ceiling, and a stub
    that under-reports usage cannot exercise a usage ceiling at all. A stub may
    fake the content of a response; faking its cost defeats the purpose.
    """

    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self._input = input_tokens
        self._output = output_tokens

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        del mode
        return {"tokens": {"input_tokens": self._input, "output_tokens": self._output}}


def _estimate_tokens(payload: Any) -> int:
    return max(1, len(json.dumps(payload, default=str)) // 4)


class _ChatResponse:
    def __init__(self, text: str, input_tokens: int = 120) -> None:
        self.id = "chat_stub_1"
        self.message = _Message(text)
        self.finish_reason = "COMPLETE"
        self.usage = _Usage(input_tokens, max(1, len(text) // 4))


class _RerankResult:
    def __init__(self, index: int, score: float) -> None:
        self.index = index
        self.relevance_score = score


class _RerankResponse:
    def __init__(self, count: int) -> None:
        self.id = "rerank_stub_1"
        self.results = [_RerankResult(i, 1.0 - i * 0.01) for i in range(count)]
        self.usage = None


class _StubCohere:
    """Returns the shapes cohere.ClientV2 returns, and counts what it was asked."""

    def __init__(self) -> None:
        self.chat_calls = 0
        self.rerank_calls = 0
        self.embed_calls = 0
        self.seen_kwargs: list[dict[str, Any]] = []

    def chat(self, **kwargs: Any) -> _ChatResponse:
        self.chat_calls += 1
        self.seen_kwargs.append(kwargs)
        cost = _estimate_tokens(kwargs)
        if "response_format" in kwargs:
            # Structure pass: the model must return a StructureSelection. Returning
            # a deliberately empty-but-valid selection keeps the renderer honest.
            graph_hash = json.loads(kwargs["messages"][-1]["content"])["graph_hash"]
            return _ChatResponse(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "disposition": "needs_review",
                        "route_claim_id": None,
                        "summary_claim_ids": [],
                        "recommended_step_claim_ids": [],
                        "unknown_ids": [],
                        "conflict_ids": [],
                        "graph_hash": graph_hash,
                        "needs_review": True,
                    }
                ),
                input_tokens=cost,
            )
        return _ChatResponse(FINDINGS_JSON, input_tokens=cost)

    def rerank(self, **kwargs: Any) -> _RerankResponse:
        self.rerank_calls += 1
        return _RerankResponse(len(kwargs["documents"]))

    def embed(self, **kwargs: Any) -> Any:  # pragma: no cover - must never be reached
        self.embed_calls += 1
        raise AssertionError("the A/B must not spend an embed call")


def _prewarmed_cache(tmp_path: Path) -> CachedEmbeddingAdapter:
    """Cache every text the run will need, using local vectors, at zero API cost."""

    class _LocalEmbed:
        def embed(self, **kwargs: Any) -> Any:
            fixture = FixtureEmbeddingAdapter()
            vectors = [list(fixture.embed_query(text)) for text in kwargs["texts"]]

            class _Vectors:
                float = vectors

            class _Response:
                embeddings = _Vectors()
                usage = None

            return _Response()

    adapter = CachedEmbeddingAdapter(
        tmp_path / "cache.json",
        client=_LocalEmbed(),
        dimension=FixtureEmbeddingAdapter.dimension,
        allow_provider=True,
    )
    texts: list[str] = []
    for manifest in (BASE_MANIFEST, ATTACK_MANIFEST):
        corpus = load_hero_corpus(manifest, embedder=FixtureEmbeddingAdapter())
        texts.extend(chunk.content for chunk in corpus.chunks)
    adapter.prewarm(documents=tuple(texts), queries=scenario_queries())
    adapter.save()
    return CachedEmbeddingAdapter(
        tmp_path / "cache.json",
        client=None,
        model="embed-v4.0",
        allow_provider=False,
    )


def test_live_provider_path_runs_and_accounts_for_every_call(tmp_path: Path) -> None:
    cache = tmp_path / "cache.json"
    CachedEmbeddingAdapter(
        cache, client=None, model="embed-v4.0", allow_provider=False
    )  # sanity: constructor tolerates a missing file
    embedder = _prewarmed_cache(tmp_path)
    # The cache was written under embed-v4.0's name so the strict reader accepts it.
    stub = _StubCohere()
    client = BudgetedCohereClient(stub, max_calls=400, sleep=lambda _: None)
    harness = ABHarness(provider="cohere", budgeted_client=client, embedder=embedder)

    scenarios = tuple(all_scenarios()[:2])
    result = run_ab(harness=harness, scenarios=scenarios)

    assert result["provider"] == "cohere"
    assert result["run_count"] == 4
    assert stub.embed_calls == 0, "the A/B must never spend an embed call"
    assert stub.chat_calls > 0 and stub.rerank_calls > 0

    ledger = client.ledger()
    # Every HTTP attempt is accounted for, and the endpoint split is real.
    assert ledger.total_calls == stub.chat_calls + stub.rerank_calls
    assert ledger.calls_by_endpoint == {
        "chat": stub.chat_calls,
        "rerank": stub.rerank_calls,
    }
    assert ledger.input_tokens > 0
    assert "embed" not in ledger.calls_by_endpoint

    # Scenario and build attribution must be present on every record, otherwise
    # per-scenario cost reporting in the dry pass is meaningless.
    assert all(item.scenario_id for item in ledger.records)
    assert all(item.build_id for item in ledger.records)


def test_live_path_sends_documents_as_untrusted_and_keeps_strict_tools(
    tmp_path: Path,
) -> None:
    embedder = _prewarmed_cache(tmp_path)
    stub = _StubCohere()
    client = BudgetedCohereClient(stub, max_calls=400, sleep=lambda _: None)
    harness = ABHarness(provider="cohere", budgeted_client=client, embedder=embedder)
    run_ab(harness=harness, scenarios=(all_scenarios()[0],))

    evidence_calls = [item for item in stub.seen_kwargs if "documents" in item]
    assert evidence_calls, "the evidence pass must send retrieved documents"
    for call in evidence_calls:
        assert call["strict_tools"] is True
        for document in call["documents"]:
            # The trust marker is what tells the model these are data, not orders.
            assert document["data"]["trust"] == "untrusted_evidence"


def test_live_path_measures_real_provider_time(tmp_path: Path) -> None:
    embedder = _prewarmed_cache(tmp_path)
    client = BudgetedCohereClient(_StubCohere(), max_calls=400, sleep=lambda _: None)
    harness = ABHarness(provider="cohere", budgeted_client=client, embedder=embedder)
    result = run_ab(harness=harness, scenarios=(all_scenarios()[0],))
    # Under a live provider the agent records real durations, so provider time is
    # populated rather than the structural zero the fixture provider forces.
    assert any(row["provider_call_ms"] is not None for row in result["runs"])
    assert result["by_build"]["guarded-v1"]["provider_call_ms"] is not None


@pytest.mark.parametrize("provider", ["cohere"])
def test_dry_pass_cannot_be_skipped_in_live_mode(provider: str) -> None:
    from resolveflow.eval import ab_cli

    with pytest.raises(SystemExit) as excinfo:
        ab_cli.main(["--provider", provider, "--skip-dry-pass"])
    assert "dry pass cannot be skipped" in str(excinfo.value)


def test_configured_budget_actually_fits_a_real_evidence_prompt(tmp_path: Path) -> None:
    """The regression that voided the first live run.

    Under the old 4096-token ceiling every run aborted with
    token_budget_exhausted before it could cite anything, and the published
    quality metrics were all consequences of that, not of the model. Assert that
    the evaluation budget lets a run actually reach completion.
    """
    from resolveflow.eval.ab_runner import EVAL_BUDGETS

    embedder = _prewarmed_cache(tmp_path)
    client = BudgetedCohereClient(_StubCohere(), max_calls=400, sleep=lambda _: None)
    harness = ABHarness(provider="cohere", budgeted_client=client, embedder=embedder)
    result = run_ab(harness=harness, scenarios=(all_scenarios()[0],))

    for row in result["runs"]:
        assert row["terminal_reason"] != "token_budget_exhausted", (
            f"{row['scenario_id']}/{row['build_id']} exhausted its token budget; "
            f"EVAL_BUDGETS.max_total_tokens={EVAL_BUDGETS.max_total_tokens} is too "
            f"small for this corpus and every quality metric would be void"
        )
        assert row["completed"], row["terminal_reason"]


def test_old_default_budget_is_refused_before_any_call_is_spent() -> None:
    from resolveflow.agent.contracts import AgentBudgets
    from resolveflow.eval.ab_runner import BudgetTooSmall, assert_budget_fits_corpus
    from resolveflow.eval.corpus import build_eval_corpus

    corpus = build_eval_corpus(
        embedder=FixtureEmbeddingAdapter(), attack_artifact_id="attack_a1_override_direct"
    )
    with pytest.raises(BudgetTooSmall, match="token_budget_exhausted"):
        assert_budget_fits_corpus(corpus, AgentBudgets())
