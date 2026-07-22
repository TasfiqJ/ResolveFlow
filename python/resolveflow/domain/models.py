from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import IdentitySnapshot, RetrievalTrace


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContextStatus(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    DENIED = "denied"
    TIMEOUT = "timeout"
    MALFORMED = "malformed"
    UNAVAILABLE = "unavailable"


class CaseCreate(FrozenModel):
    scenario_id: Literal["hero-payments-001"] = "hero-payments-001"


class CanonicalCase(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    case_id: str
    tenant_id: str
    customer_id: str
    reporter: str
    source_system: Literal["web", "slack_fixture"]
    channel: str
    received_at: datetime
    case_time: datetime
    language_hint: Literal["en"] = "en"
    severity: Literal["high"] = "high"
    region: str = "ca-central"
    service: str = "payments-api"
    raw_text: str
    error_code: str = "PYM-431"
    missing_fields: tuple[str, ...] = ("cluster_id",)
    synthetic: Literal[True] = True
    checksum: str


class ContextResult(FrozenModel):
    operation: str
    status: ContextStatus
    as_of: datetime
    provenance_ids: tuple[str, ...]
    data: dict[str, Any] = Field(default_factory=dict)
    checksum: str


class Citation(FrozenModel):
    citation_id: str
    source_id: str
    title: str
    version: str
    locator: str
    excerpt: str
    claim_id: str | None = None
    verifier_codes: tuple[str, ...] = ()


class FinalResponse(FrozenModel):
    status: Literal["verified", "needs_review", "abstained"]
    disposition: Literal["resolved", "needs_review", "abstained"]
    route: str | None
    summary: str
    recommended_steps: tuple[str, ...]
    verified_facts: tuple[str, ...] = ()
    unknowns: tuple[str, ...]
    conflicts: tuple[str, ...] = ()
    citations: tuple[Citation, ...]
    claim_ids: tuple[str, ...] = ()
    graph_hash: str
    provider: Literal["recorded_fixture", "cohere"]
    verifier_status: Literal["verified", "needs_review"]
    needs_review: bool


class TraceEvent(FrozenModel):
    sequence: int
    event_id: str
    occurred_at: datetime
    actor: str
    component: str
    event_name: str
    outcome: Literal["ok", "needs_information", "rejected", "timeout", "failed"]
    correlation_id: str
    duration_ms: int = 0
    versions: dict[str, str] = Field(default_factory=dict)
    trace_id: str | None = None
    span_id: str | None = None
    safe_detail: dict[str, Any]


class AuditEvent(TraceEvent):
    previous_event_hash: str | None = None
    event_hash: str


class ActionBoundary(FrozenModel):
    action_type: Literal["create_jira_issue"] = "create_jira_issue"
    proposal_id: str | None = None
    state: Literal[
        "pending_approval",
        "approved",
        "rejected",
        "expired",
        "invalidated",
        "not_proposed",
    ]
    connector: Literal["synthetic_not_dispatched"] = "synthetic_not_dispatched"
    summary: str
    team: Literal["Payments Platform"] = "Payments Platform"
    priority: Literal["High", "Medium", "Low"] = "High"
    verified_description: str = ""
    evidence_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    risk: Literal["low", "medium", "high"] = "medium"
    expires_at: datetime | None = None
    payload_digest: str | None = None
    idempotency_key: str | None = None
    permission_required: Literal["approve_jira"] = "approve_jira"


class RunSnapshot(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    provenance: Literal["recorded_fixture"] = "recorded_fixture"
    generated_at: datetime
    run_id: str
    build_id: str
    scenario_id: str | None = None
    commit: str
    model_policy: str
    corpus_version: Literal["hero-corpus-1.0"] = "hero-corpus-1.0"
    identity_snapshot: IdentitySnapshot
    retrieval: RetrievalTrace
    case: CanonicalCase
    context: tuple[ContextResult, ...]
    response: FinalResponse
    evidence_graph: dict[str, Any]
    provider_traces: tuple[dict[str, Any], ...]
    tool_traces: tuple[dict[str, Any], ...]
    security_events: tuple[dict[str, Any], ...]
    forbidden_effect_score: dict[str, Any]
    action: ActionBoundary
    trace: tuple[TraceEvent, ...]
    run_inputs: dict[str, Any] = Field(default_factory=dict)
    content_hash: str


class VersionResponse(FrozenModel):
    version: str
    build_id: str
    commit: str
    schema_version: str = "1.0"


class HealthResponse(FrozenModel):
    status: Literal["ok", "ready"]
