from __future__ import annotations

import pytest
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def test_pro_requires_escalation_reason() -> None:
    case = canonical_hero_case()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="operator",
        role="incident_commander",
        region=case.region,
        case_time=case.case_time,
    )
    retriever = HybridRetriever(
        load_hero_corpus(), AuthorizationPolicy(), FixtureEmbeddingAdapter(), FixtureRerankAdapter()
    )
    with pytest.raises(ValueError, match="escalation reason"):
        retriever.retrieve(case.raw_text, identity, rerank_model="rerank-v4.0-pro")
