from __future__ import annotations

import pytest
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.evidence import IdentitySnapshot
from resolveflow.domain.models import CanonicalCase
from resolveflow.eval.budget import BudgetExceeded
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator, ResolveRunConfiguration
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter


class RecordingReranker:
    def __init__(self, model: str) -> None:
        self.model = model
        self.calls = 0
        self.supports_deadline = True

    def rerank(
        self,
        query: str,
        documents: tuple[str, ...],
        top_n: int,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[tuple[int, float], ...]:
        del timeout_seconds
        self.calls += 1
        return tuple((index, 1.0 / (index + 1)) for index in range(top_n))


def make_retriever(model: str) -> tuple[HybridRetriever, RecordingReranker]:
    reranker = RecordingReranker(model)
    return (
        HybridRetriever(
            load_hero_corpus(), AuthorizationPolicy(), FixtureEmbeddingAdapter(), reranker
        ),
        reranker,
    )


def make_identity() -> tuple[CanonicalCase, IdentitySnapshot]:
    case = canonical_hero_case()
    return case, make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="operator",
        role="incident_commander",
        region=case.region,
        case_time=case.case_time,
    )


def test_pro_requires_escalation_reason() -> None:
    case, identity = make_identity()
    retriever, reranker = make_retriever("rerank-v4.0-pro")

    with pytest.raises(ValueError, match="escalation reason"):
        retriever.retrieve(case.raw_text, identity)

    assert reranker.calls == 0


def test_pro_rejects_a_blank_escalation_reason() -> None:
    case, identity = make_identity()
    retriever, reranker = make_retriever("rerank-v4.0-pro")

    with pytest.raises(ValueError, match="escalation reason"):
        retriever.retrieve(case.raw_text, identity, escalation_reason="   ")

    assert reranker.calls == 0


def test_requested_model_must_match_adapter_before_provider_call() -> None:
    case, identity = make_identity()
    retriever, reranker = make_retriever("rerank-v4.0-fast")

    with pytest.raises(ValueError, match="does not match the configured rerank adapter"):
        retriever.retrieve(
            case.raw_text,
            identity,
            rerank_model="rerank-v4.0-pro",
            escalation_reason="candidate tie requires the higher-quality model",
        )

    assert reranker.calls == 0


def test_trace_records_actual_adapter_model() -> None:
    case, identity = make_identity()
    retriever, reranker = make_retriever("rerank-v4.0-pro")

    trace = retriever.retrieve(
        case.raw_text,
        identity,
        rerank_model="rerank-v4.0-pro",
        escalation_reason="candidate tie requires the higher-quality model",
    )

    assert reranker.calls == 1
    assert trace.rerank_model == reranker.model
    assert trace.rerank_escalation_reason == "candidate tie requires the higher-quality model"


def test_rerank_call_cap_cannot_be_relabelled_as_a_retrieval_failure() -> None:
    class CappedReranker(RecordingReranker):
        def rerank(
            self,
            query: str,
            documents: tuple[str, ...],
            top_n: int,
            *,
            timeout_seconds: float | None = None,
        ) -> tuple[tuple[int, float], ...]:
            del query, documents, top_n, timeout_seconds
            self.calls += 1
            raise BudgetExceeded("evaluation provider-call cap reached")

    case, identity = make_identity()
    reranker = CappedReranker("rerank-v4.0-fast")
    retriever = HybridRetriever(
        load_hero_corpus(), AuthorizationPolicy(), FixtureEmbeddingAdapter(), reranker
    )

    with pytest.raises(BudgetExceeded, match="provider-call cap"):
        retriever.retrieve(case.raw_text, identity)

    assert reranker.calls == 1


def test_orchestrator_routes_an_explicit_audited_pro_escalation() -> None:
    case, identity = make_identity()
    fast = RecordingReranker("rerank-v4.0-fast")
    pro = RecordingReranker("rerank-v4.0-pro")
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(),
        GovernedAgent(FixtureChatAdapter()),
        embedding_adapter=FixtureEmbeddingAdapter(),
        rerank_adapter=fast,
        pro_rerank_adapter=pro,
    )
    configuration = ResolveRunConfiguration(
        run_id="run-pro-escalation",
        build_id="guarded-v1",
        generated_at=case.case_time,
        identity=identity,
        corpus=load_hero_corpus(),
        model_policy="governed-agent-1.0",
        rerank_model="rerank-v4.0-pro",
        rerank_escalation_reason="candidate tie requires the higher-quality model",
    )

    snapshot = orchestrator.run(case, configuration)

    assert fast.calls == 0
    assert pro.calls == 1
    assert snapshot.retrieval.rerank_model == "rerank-v4.0-pro"
    assert snapshot.retrieval.rerank_escalation_reason == (
        "candidate tie requires the higher-quality model"
    )


def test_run_configuration_rejects_unaudited_pro_selection() -> None:
    case, identity = make_identity()

    with pytest.raises(ValueError, match="Pro rerank run requires an escalation reason"):
        ResolveRunConfiguration(
            run_id="run-pro-without-reason",
            build_id="guarded-v1",
            generated_at=case.case_time,
            identity=identity,
            corpus=load_hero_corpus(),
            model_policy="governed-agent-1.0",
            rerank_model="rerank-v4.0-pro",
        )
