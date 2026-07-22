from __future__ import annotations

import math
from datetime import datetime
from enum import IntEnum
from typing import Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum


class Classification(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    RESTRICTED = 2


class SourcePosition(FrozenModel):
    kind: Literal["section", "page", "row", "image"]
    locator: str


class Artifact(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    artifact_id: str
    tenant_id: str
    source_system: str
    source_key: str
    title: str
    owner: str
    modality: Literal["text", "pdf", "json", "csv", "image"]
    created_at: datetime
    checksum: str


class ArtifactVersion(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    artifact_version_id: str
    artifact_id: str
    version: str
    source_path: str
    source_checksum: str
    parser_name: str
    parser_version: str
    chunker_name: str
    chunker_version: str
    parsing_quality: Literal["complete", "partial", "failed"]
    language: str
    classification: Classification
    effective_from: datetime
    effective_to: datetime | None = None
    created_at: datetime
    checksum: str

    @model_validator(mode="after")
    def effective_interval_is_valid(self) -> ArtifactVersion:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be later than effective_from")
        return self


class Chunk(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    chunk_id: str
    artifact_version_id: str
    ordinal: int = Field(ge=0)
    position: SourcePosition
    content: str = Field(min_length=1)
    token_count: int = Field(gt=0)
    checksum: str


class ChunkACL(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    acl_id: str
    chunk_id: str
    tenant_id: str
    role: Literal["incident_commander", "contractor"]
    region: str
    policy_version: str
    checksum: str


class EmbeddingRecord(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    embedding_id: str
    chunk_id: str
    model: str
    dimension: int = Field(gt=0)
    input_type: Literal["search_document", "search_query"]
    preprocessing_version: str
    content_checksum: str
    vector: tuple[float, ...]
    checksum: str

    @model_validator(mode="after")
    def vector_matches_dimension(self) -> EmbeddingRecord:
        if len(self.vector) != self.dimension or any(not math.isfinite(x) for x in self.vector):
            raise ValueError("embedding vector must contain exactly dimension finite values")
        return self


class CorpusSnapshot(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    snapshot_id: str
    tenant_id: str
    as_of: datetime
    artifact_version_ids: tuple[str, ...]
    embedding_ids: tuple[str, ...]
    parser_versions: tuple[str, ...]
    chunker_versions: tuple[str, ...]
    embedding_policy: str
    created_at: datetime
    checksum: str


class IdentitySnapshot(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    snapshot_id: str
    tenant_id: str
    actor_id: str
    active_role: Literal["incident_commander", "contractor"]
    region: str
    maximum_classification: Classification
    policy_version: str
    case_time: datetime
    created_at: datetime
    checksum: str


class ACLSnapshot(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    snapshot_id: str
    identity_snapshot_id: str
    corpus_snapshot_id: str
    eligible_chunk_ids: tuple[str, ...]
    policy_version: str
    created_at: datetime
    checksum: str


class Corpus(FrozenModel):
    artifacts: tuple[Artifact, ...]
    versions: tuple[ArtifactVersion, ...]
    chunks: tuple[Chunk, ...]
    acls: tuple[ChunkACL, ...]
    embeddings: tuple[EmbeddingRecord, ...]
    snapshot: CorpusSnapshot


class RetrievalCandidate(FrozenModel):
    chunk_id: str
    artifact_id: str
    artifact_version_id: str
    title: str
    position: SourcePosition
    content: str
    content_checksum: str
    lexical_rank: int | None = None
    lexical_score: float | None = None
    vector_rank: int | None = None
    vector_score: float | None = None
    fused_rank: int
    fused_score: float
    rerank_rank: int | None = None
    rerank_score: float | None = None
    provenance_checksum: str


class RetrievalTrace(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    query_checksum: str
    corpus_snapshot_id: str
    identity_snapshot_id: str
    acl_snapshot_id: str
    cache_key: str
    policy_reason_code: Literal["eligible_by_snapshot"] = "eligible_by_snapshot"
    eligible_chunk_count: int
    lexical_candidate_ids: tuple[str, ...]
    vector_candidate_ids: tuple[str, ...]
    rerank_model: str
    rerank_escalation_reason: str | None
    rerank_payload_checksum: str
    candidates: tuple[RetrievalCandidate, ...]
    checksum: str


class RetrievalMetricObservation(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    metric_id: str
    metric_name: Literal["recall_at_5", "recall_at_10", "ndcg_at_10"]
    split: Literal["development", "calibration"]
    build_id: str
    fixture_version: str
    numerator: float
    denominator: int = Field(gt=0)
    value: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    checksum: str


def stable_id(prefix: str, value: object) -> str:
    return f"{prefix}_{checksum(value).split(':', 1)[1][:24]}"
