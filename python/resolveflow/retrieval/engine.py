from __future__ import annotations

import math
import time
from typing import Any

from resolveflow.domain.evidence import (
    Corpus,
    IdentitySnapshot,
    RetrievalCandidate,
    RetrievalTrace,
)
from resolveflow.domain.hashing import checksum
from resolveflow.eval.budget import BudgetExceeded
from resolveflow.policy.authorization import AuthorizationPolicy
from resolveflow.retrieval.cohere import ProviderAdapterError
from resolveflow.retrieval.fixture import tokens
from resolveflow.retrieval.ports import EmbeddingPort, RerankPort
from resolveflow.telemetry.stages import (
    STAGE_ACL,
    STAGE_FUSION,
    STAGE_LEXICAL,
    STAGE_QUERY_EMBEDDING,
    STAGE_RERANK,
    STAGE_VECTOR,
    NullStageRecorder,
    StageRecorder,
)


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding vectors must have equal dimensions")
    if any(not math.isfinite(value) for value in (*left, *right)):
        raise ValueError("embedding vectors must contain only finite coordinates")
    left_norm = math.hypot(*left)
    right_norm = math.hypot(*right)
    if (
        not math.isfinite(left_norm)
        or not math.isfinite(right_norm)
        or left_norm <= 0.0
        or right_norm <= 0.0
    ):
        raise ValueError("embedding vectors must have a finite non-zero norm")
    similarity = sum((a / left_norm) * (b / right_norm) for a, b in zip(left, right, strict=True))
    if not math.isfinite(similarity):
        raise ValueError("cosine similarity must be finite")
    return similarity


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
        self._document_embedding_cache: dict[
            tuple[str, str, tuple[str, ...]], dict[str, tuple[float, ...]]
        ] = {}
        self.last_provider_call_count = 0
        self.last_provider_call_ms = 0.0

    def retrieve(
        self,
        query: str,
        identity: IdentitySnapshot,
        *,
        rerank_model: str | None = None,
        escalation_reason: str | None = None,
        recorder: StageRecorder | None = None,
        deadline: float | None = None,
    ) -> RetrievalTrace:
        actual_rerank_model = self.reranker.model
        if rerank_model is not None and rerank_model != actual_rerank_model:
            raise ValueError(
                "requested rerank model does not match the configured rerank adapter model"
            )
        if actual_rerank_model.lower().endswith("-pro") and not (
            escalation_reason and escalation_reason.strip()
        ):
            raise ValueError("every Pro rerank call requires an escalation reason")
        timer = recorder if recorder is not None else NullStageRecorder()
        self.last_provider_call_count = 0
        self.last_provider_call_ms = 0.0

        def bounded_call(adapter: object, method_name: str, *args: object) -> Any:
            failure_stage = "rerank" if method_name == "rerank" else "vector"
            provider_endpoint = "rerank" if method_name == "rerank" else "embed"
            model = str(getattr(adapter, "model", "unknown"))
            remaining = None if deadline is None else deadline - time.perf_counter()
            if remaining is not None and remaining <= 0:
                raise ProviderAdapterError(
                    "deadline",
                    model,
                    failure_stage=failure_stage,
                    provider_call_count=self.last_provider_call_count,
                    provider_call_ms=self.last_provider_call_ms,
                )
            method = getattr(adapter, method_name)
            provider_backed = bool(getattr(adapter, "provider_backed", False))
            minimum_timeout = float(getattr(adapter, "minimum_timeout_seconds", 0.0))
            if remaining is not None and remaining < minimum_timeout:
                raise ProviderAdapterError(
                    "deadline",
                    model,
                    failure_stage=failure_stage,
                    provider_call_count=self.last_provider_call_count,
                    provider_call_ms=self.last_provider_call_ms,
                )
            started = time.perf_counter()

            try:
                if remaining is not None:
                    if not getattr(adapter, "supports_deadline", False):
                        raise ProviderAdapterError(
                            "unbounded_adapter",
                            model,
                            failure_stage=failure_stage,
                            provider_call_count=self.last_provider_call_count,
                            provider_call_ms=self.last_provider_call_ms,
                        )
                    result = method(*args, timeout_seconds=remaining)
                else:
                    result = method(*args)
            except BudgetExceeded:
                raise
            except ProviderAdapterError as exc:
                if exc.endpoint in {"deadline", "unbounded_adapter"}:
                    raise
                elapsed_ms = max(0.0, (time.perf_counter() - started) * 1000.0)
                exc.failure_stage = failure_stage
                exc.provider_call_count += self.last_provider_call_count + (
                    1 if provider_backed else 0
                )
                exc.provider_call_ms += self.last_provider_call_ms + (
                    elapsed_ms if provider_backed else 0.0
                )
                raise
            except Exception as exc:
                elapsed_ms = max(0.0, (time.perf_counter() - started) * 1000.0)
                raise ProviderAdapterError(
                    provider_endpoint,
                    model,
                    failure_stage=failure_stage,
                    provider_call_count=self.last_provider_call_count
                    + (1 if provider_backed else 0),
                    provider_call_ms=self.last_provider_call_ms
                    + (elapsed_ms if provider_backed else 0.0),
                ) from exc

            elapsed_ms = max(0.0, (time.perf_counter() - started) * 1000.0)
            if provider_backed:
                self.last_provider_call_count += 1
                self.last_provider_call_ms += elapsed_ms
            if deadline is not None and time.perf_counter() > deadline:
                raise ProviderAdapterError(
                    "deadline",
                    model,
                    failure_stage=failure_stage,
                    provider_call_count=self.last_provider_call_count,
                    provider_call_ms=self.last_provider_call_ms,
                )
            return result

        cache_key = self.policy.cache_key(identity, self.corpus.snapshot.snapshot_id, query)
        if cache_key in self._cache:
            # A cache hit is a real observation, but it is not a measurement of the
            # retrieval stages. Label it so no stage silently reports near-zero.
            timer.record("retrieval_cache_hit", 0.0, timer.elapsed_ms())
            return self._cache[cache_key]

        with timer.stage(STAGE_ACL):
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

        with timer.stage(STAGE_LEXICAL):
            query_terms = set(tokens(query))
            lexical_scored = [
                (chunk, float(sum(1 for token in tokens(chunk.content) if token in query_terms)))
                for chunk in eligible_chunks
            ]
            lexical = sorted(lexical_scored, key=lambda item: (-item[1], item[0].chunk_id))[
                : self.candidate_k
            ]

        with timer.stage(STAGE_QUERY_EMBEDDING):
            query_vector = bounded_call(self.embedder, "embed_query", query)

        with timer.stage(STAGE_VECTOR):
            stored_embeddings = {
                item.chunk_id: item.vector
                for item in self.corpus.embeddings
                if item.model == self.embedder.model
            }
            if all(chunk.chunk_id in stored_embeddings for chunk in eligible_chunks):
                embedding_by_chunk = stored_embeddings
                embedding_source = "stored_snapshot"
            else:
                authorized_ids = tuple(chunk.chunk_id for chunk in eligible_chunks)
                embedding_cache_key = (
                    self.corpus.snapshot.snapshot_id,
                    self.embedder.model,
                    authorized_ids,
                )
                embedding_by_chunk = self._document_embedding_cache.get(embedding_cache_key, {})
                if not embedding_by_chunk:
                    vectors = bounded_call(
                        self.embedder,
                        "embed_documents",
                        tuple(chunk.content for chunk in eligible_chunks),
                    )
                    embedding_by_chunk = {
                        chunk.chunk_id: vector
                        for chunk, vector in zip(eligible_chunks, vectors, strict=True)
                    }
                    self._document_embedding_cache[embedding_cache_key] = embedding_by_chunk
                embedding_source = "computed_authorized_candidates"
            vector_scored = [
                (chunk, _cosine(query_vector, embedding_by_chunk[chunk.chunk_id]))
                for chunk in eligible_chunks
                if chunk.chunk_id in embedding_by_chunk
            ]
            vector = sorted(vector_scored, key=lambda item: (-item[1], item[0].chunk_id))[
                : self.candidate_k
            ]

        with timer.stage(STAGE_FUSION):
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
                artifact_counts[version.artifact_id] = (
                    artifact_counts.get(version.artifact_id, 0) + 1
                )
            documents = tuple(chunk_by_id[item].content for item in selected_ids)

        with timer.stage(STAGE_RERANK):
            # A provider rerank with an empty document list and top_n=0 is rejected by the
            # API and surfaces as a run-ending ProviderAdapterError. An identity with no
            # eligible chunks must abstain cleanly, not fail the run.
            reranked = (
                bounded_call(self.reranker, "rerank", query, documents, len(documents))
                if documents
                else ()
            )
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
            "embedding_model": self.embedder.model,
            "embedding_source": embedding_source,
            "rerank_model": actual_rerank_model,
            "rerank_escalation_reason": escalation_reason,
            "rerank_payload_checksum": checksum(payload_body),
            "candidates": tuple(candidates),
        }
        trace = RetrievalTrace(**body, checksum=checksum(body))
        self._cache[cache_key] = trace
        return trace
