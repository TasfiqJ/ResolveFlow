from __future__ import annotations

from resolveflow.agent.contracts import AgentBudgets
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.ports import ChatProviderPort
from resolveflow.agent.service import GovernedAgent, GovernedRunResult
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.evidence import Corpus, IdentitySnapshot, RetrievalTrace
from resolveflow.domain.models import CanonicalCase, ContextResult
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def governed_inputs(
    *, role: str = "incident_commander"
) -> tuple[
    CanonicalCase,
    tuple[ContextResult, ...],
    Corpus,
    IdentitySnapshot,
    RetrievalTrace,
]:
    case = canonical_hero_case()
    context = FixtureContextRepository().enrich(case)
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id=f"user_{role}_synthetic",
        role=role,
        region=case.region,
        case_time=case.case_time,
    )
    retrieval = HybridRetriever(
        corpus,
        AuthorizationPolicy(),
        FixtureEmbeddingAdapter(),
        FixtureRerankAdapter(),
    ).retrieve(case.raw_text, identity)
    return case, context, corpus, identity, retrieval


def run_governed(
    provider: ChatProviderPort | None = None,
    *,
    budgets: AgentBudgets | None = None,
    retrieval: RetrievalTrace | None = None,
) -> GovernedRunResult:
    case, context, corpus, identity, default_retrieval = governed_inputs()
    return GovernedAgent(provider or FixtureChatAdapter(), budgets=budgets).resolve(
        run_id="run_test_governed",
        case=case,
        context=context,
        identity=identity,
        retrieval=retrieval or default_retrieval,
        corpus=corpus,
    )
