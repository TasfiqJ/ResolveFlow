from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def _trace():  # type: ignore[no-untyped-def]
    case = canonical_hero_case()
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="operator",
        role="incident_commander",
        region=case.region,
        case_time=case.case_time,
    )
    return HybridRetriever(
        corpus, AuthorizationPolicy(), FixtureEmbeddingAdapter(), FixtureRerankAdapter()
    ).retrieve(case.raw_text, identity)


def test_candidates_retain_component_scores_ranks_and_provenance() -> None:
    trace = _trace()
    assert trace.candidates
    assert all(item.lexical_rank is not None for item in trace.candidates)
    assert all(item.vector_rank is not None for item in trace.candidates)
    assert all(item.fused_rank > 0 and item.rerank_rank for item in trace.candidates)
    assert all(item.provenance_checksum.startswith("sha256:") for item in trace.candidates)
    assert trace.rerank_payload_checksum.startswith("sha256:")


def test_exact_identifier_evidence_remains_retrievable() -> None:
    trace = _trace()
    assert any("PYM-431" in item.content for item in trace.candidates[:3])
