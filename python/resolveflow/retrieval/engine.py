from __future__ import annotations

import math

from resolveflow.domain.evidence import (
    Corpus,
    IdentitySnapshot,
    RetrievalCandidate,
    RetrievalTrace,
)
from resolveflow.domain.hashing import checksum
from resolveflow.policy.authorization import AuthorizationPolicy
from resolveflow.retrieval.fixture import tokens
from resolveflow.retrieval.ports import EmbeddingPort, RerankPort


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


class HybridRetriever:
    def __init__(
        self,
        corpus: Corpus,
        policy: AuthorizationPolicy,
        embedder: EmbeddingPort,
        reranker: RerankPort,
        *,
        candidate_k: int = 10,
        rrf_constant: int = 60,
        diversity_cap: int = 2,
    ) -> None:
        self.corpus = corpus
        self.policy = policy
        self.embedder = embedder
        self.reranker = reranker
        self.candidate_k = candidate_k
        self.rrf_constant = rrf_constant
        self.diversity_cap = diversity_cap
        self._cache: dict[str, RetrievalTrace] = {}

    def retrieve(
        self,
        query: str,
        identity: IdentitySnapshot,
        *,
        rerank_model: str | None = None,
        escalation_reason: str | None = None,
    ) -> RetrievalTrace:
        if rerank_model is not None and "pro" in rerank_model and not escalation_reason:
            raise ValueError("every Pro rerank call requires an escalation reason")
        cache_key = self.policy.cache_key(identity, self.corpus.snapshot.snapshot_id, query)
        if cache_key in self._cache:
            return self._cache[cache_key]

        eligible_ids = self.policy.eligible_chunk_ids(
            identity, self.corpus.versions, self.corpus.chunks, self.corpus.acls
        )
        acl_snapshot = self.policy.snapshot(
            identity, self.corpus.snapshot.snapshot_id, eligible_ids
        )
        snapshot_versions = set(self.corpus.snapshot.artifact_version_ids)
        eligible_chunks = tuple(
            chunk
            for chunk in self.corpus.chunks
            if chunk.chunk_id in eligible_ids and chunk.artifact_version_id in snapshot_versions
        )
        query_terms = set(tokens(query))
        lexical_scored = [
            (chunk, float(sum(1 for token in tokens(chunk.content) if token in query_terms)))
            for chunk in eligible_chunks
        ]
        lexical = sorted(lexical_scored, key=lambda item: (-item[1], item[0].chunk_id))[
            : self.candidate_k
        ]

        query_vector = self.embedder.embed_query(query)
        embedding_by_chunk = {item.chunk_id: item.vector for item in self.corpus.embeddings}
        vector_scored = [
            (chunk, _cosine(query_vector, embedding_by_chunk[chunk.chunk_id]))
            for chunk in eligible_chunks
            if chunk.chunk_id in embedding_by_chunk
        ]
        vector = sorted(vector_scored, key=lambda item: (-item[1], item[0].chunk_id))[
            : self.candidate_k
        ]
        lexical_ranks = {item.chunk_id: index for index, (item, _) in enumerate(lexical, 1)}
        vector_ranks = {item.chunk_id: index for index, (item, _) in enumerate(vector, 1)}
        lexical_scores = {item.chunk_id: score for item, score in lexical}
        vector_scores = {item.chunk_id: score for item, score in vector}
        fused_ids = set(lexical_ranks) | set(vector_ranks)
        fused_scores = {
            chunk_id: (
                (
                    1 / (self.rrf_constant + lexical_ranks[chunk_id])
                    if chunk_id in lexical_ranks
                    else 0
                )
                + (
                    1 / (self.rrf_constant + vector_ranks[chunk_id])
                    if chunk_id in vector_ranks
                    else 0
                )
            )
            for chunk_id in fused_ids
        }
        chunk_by_id = {item.chunk_id: item for item in eligible_chunks}
        version_by_id = {item.artifact_version_id: item for item in self.corpus.versions}
        artifact_by_id = {item.artifact_id: item for item in self.corpus.artifacts}
        ordered_ids = sorted(fused_ids, key=lambda item: (-fused_scores[item], item))
        dedupe_checksums: set[str] = set()
        artifact_counts: dict[str, int] = {}
        selected_ids: list[str] = []
        for chunk_id in ordered_ids:
            chunk = chunk_by_id[chunk_id]
            version = version_by_id[chunk.artifact_version_id]
            if chunk.checksum in dedupe_checksums:
                continue
            if artifact_counts.get(version.artifact_id, 0) >= self.diversity_cap:
                continue
            selected_ids.append(chunk_id)
            dedupe_checksums.add(chunk.checksum)
            artifact_counts[version.artifact_id] = artifact_counts.get(version.artifact_id, 0) + 1

        documents = tuple(chunk_by_id[item].content for item in selected_ids)
        reranked = self.reranker.rerank(query, documents, len(documents))
        rerank_by_id = {
            selected_ids[input_index]: (rank, score)
            for rank, (input_index, score) in enumerate(reranked, 1)
        }
        candidates: list[RetrievalCandidate] = []
        for fused_rank, chunk_id in enumerate(selected_ids, 1):
            chunk = chunk_by_id[chunk_id]
            version = version_by_id[chunk.artifact_version_id]
            artifact = artifact_by_id[version.artifact_id]
            rerank_rank, rerank_score = rerank_by_id[chunk_id]
            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk_id,
                    artifact_id=artifact.artifact_id,
                    artifact_version_id=version.artifact_version_id,
                    title=artifact.title,
                    position=chunk.position,
                    content=chunk.content,
                    content_checksum=chunk.checksum,
                    lexical_rank=lexical_ranks.get(chunk_id),
                    lexical_score=lexical_scores.get(chunk_id),
                    vector_rank=vector_ranks.get(chunk_id),
                    vector_score=vector_scores.get(chunk_id),
                    fused_rank=fused_rank,
                    fused_score=fused_scores[chunk_id],
                    rerank_rank=rerank_rank,
                    rerank_score=rerank_score,
                    provenance_checksum=checksum(
                        {
                            "artifact": artifact.checksum,
                            "version": version.checksum,
                            "chunk": chunk.checksum,
                        }
                    ),
                )
            )
        candidates.sort(key=lambda item: (item.rerank_rank or math.inf, item.chunk_id))
        payload_body = {
            "ids": selected_ids,
            "documents": documents,
            "top_n": len(documents),
        }
        body = {
            "query_checksum": checksum(query),
            "corpus_snapshot_id": self.corpus.snapshot.snapshot_id,
            "identity_snapshot_id": identity.snapshot_id,
            "acl_snapshot_id": acl_snapshot.snapshot_id,
            "cache_key": cache_key,
            "eligible_chunk_count": len(eligible_chunks),
            "lexical_candidate_ids": tuple(item.chunk_id for item, _ in lexical),
            "vector_candidate_ids": tuple(item.chunk_id for item, _ in vector),
            "rerank_model": rerank_model or self.reranker.model,
            "rerank_escalation_reason": escalation_reason,
            "rerank_payload_checksum": checksum(payload_body),
            "candidates": tuple(candidates),
        }
        trace = RetrievalTrace(**body, checksum=checksum(body))
        self._cache[cache_key] = trace
        return trace
