from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever


class RecordingEmbedder:
    model = "live-contract-model"

    def __init__(self) -> None:
        self.document_calls: list[tuple[str, ...]] = []
        self.query_calls: list[str] = []

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        self.document_calls.append(texts)
        return tuple((1.0, float(index + 1)) for index, _ in enumerate(texts))

    def embed_query(self, text: str) -> tuple[float, ...]:
        self.query_calls.append(text)
        return (1.0, 1.0)


class RecordingReranker:
    model = "live-contract-rerank"

    def rerank(
        self, query: str, documents: tuple[str, ...], top_n: int
    ) -> tuple[tuple[int, float], ...]:
        return tuple((index, 1.0 / (index + 1)) for index in range(min(top_n, len(documents))))


def test_live_model_embeds_only_authorized_snapshot_candidates_and_reuses_them() -> None:
    corpus = load_hero_corpus()
    case = canonical_hero_case()
    identity = make_identity_snapshot(
        tenant_id=case.tenant_id,
        actor_id="user_contractor_synthetic",
        role="contractor",
        region=case.region,
        case_time=case.case_time,
    )
    embedder = RecordingEmbedder()
    retriever = HybridRetriever(
        corpus,
        AuthorizationPolicy(),
        embedder,
        RecordingReranker(),
    )
    restricted_version_ids = {
        version.artifact_version_id
        for version in corpus.versions
        if version.artifact_id == "artifact_restricted_legal"
    }
    restricted_content = {
        chunk.content
        for chunk in corpus.chunks
        if chunk.artifact_version_id in restricted_version_ids
    }

    first = retriever.retrieve(case.raw_text, identity)
    second = retriever.retrieve("payments rollback follow-up", identity)

    assert first.embedding_source == "computed_authorized_candidates"
    assert first.embedding_model == "live-contract-model"
    assert len(embedder.document_calls) == 1
    assert len(embedder.document_calls[0]) == first.eligible_chunk_count
    assert restricted_content.isdisjoint(embedder.document_calls[0])
    assert len(embedder.query_calls) == 2
    assert second.embedding_source == "computed_authorized_candidates"
