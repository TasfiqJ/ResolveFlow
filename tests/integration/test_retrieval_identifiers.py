from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def test_exact_error_code_remains_retrievable() -> None:
    case = canonical_hero_case()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="identifier-test",
        role="contractor",
        region=case.region,
        case_time=case.case_time,
    )
    trace = HybridRetriever(
        load_hero_corpus(),
        AuthorizationPolicy(),
        FixtureEmbeddingAdapter(),
        FixtureRerankAdapter(),
    ).retrieve("PYM-431 issuer routing", identity)
    assert any("PYM-431" in item.content for item in trace.candidates[:3])
