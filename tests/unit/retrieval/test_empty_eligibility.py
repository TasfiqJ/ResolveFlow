from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


class StrictRerankAdapter(FixtureRerankAdapter):
    """Models a provider adapter, which rejects an empty document list / top_n=0."""

    def rerank(self, query, documents, top_n):  # type: ignore[no-untyped-def]
        if not documents or top_n <= 0:
            raise ValueError("provider rerank requires at least one document")
        return super().rerank(query, documents, top_n)


def test_identity_with_no_eligible_chunks_abstains_instead_of_failing() -> None:
    """An empty candidate set must produce an empty trace, not a run-ending error.

    The reranker was called unconditionally with `documents=()` and `top_n=0`; the
    real Cohere adapter rejects that and the failure surfaced as a
    ProviderAdapterError that ended the whole run rather than a clean abstention.
    """
    case = canonical_hero_case()
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="user_contractor_synthetic",
        role="contractor",
        region="antarctica-south",  # no ACL grants this region
        case_time=case.case_time,
    )

    trace = HybridRetriever(
        corpus,
        AuthorizationPolicy(),
        FixtureEmbeddingAdapter(),
        StrictRerankAdapter(),
    ).retrieve(case.raw_text, identity)

    assert trace.candidates == ()
