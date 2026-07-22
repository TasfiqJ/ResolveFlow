from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def test_role_and_tenant_are_bound_into_cache_key() -> None:
    case = canonical_hero_case()
    retriever = HybridRetriever(
        load_hero_corpus(), AuthorizationPolicy(), FixtureEmbeddingAdapter(), FixtureRerankAdapter()
    )
    commander = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="same",
        role="incident_commander",
        region=case.region,
        case_time=case.case_time,
    )
    contractor = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="same",
        role="contractor",
        region=case.region,
        case_time=case.case_time,
    )
    commander_trace = retriever.retrieve(case.raw_text, commander)
    contractor_trace = retriever.retrieve(case.raw_text, contractor)
    assert commander_trace.cache_key != contractor_trace.cache_key
    assert commander_trace.identity_snapshot_id != contractor_trace.identity_snapshot_id
    assert commander_trace is retriever.retrieve(case.raw_text, commander)
