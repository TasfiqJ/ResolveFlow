from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def _retrieve(role: str):  # type: ignore[no-untyped-def]
    case = canonical_hero_case()
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id=f"user_{role}",
        role=role,
        region=case.region,
        case_time=case.case_time,
    )
    return HybridRetriever(
        corpus, AuthorizationPolicy(), FixtureEmbeddingAdapter(), FixtureRerankAdapter()
    ).retrieve(case.raw_text, identity)


def test_role_downgrade_removes_restricted_source_before_every_ranker() -> None:
    commander = _retrieve("incident_commander")
    contractor = _retrieve("contractor")
    restricted_chunks = {
        item.chunk_id
        for item in commander.candidates
        if item.artifact_id == "artifact_restricted_legal"
    }
    assert restricted_chunks
    assert restricted_chunks.isdisjoint(contractor.lexical_candidate_ids)
    assert restricted_chunks.isdisjoint(contractor.vector_candidate_ids)
    assert restricted_chunks.isdisjoint(item.chunk_id for item in contractor.candidates)
    assert contractor.eligible_chunk_count < commander.eligible_chunk_count
