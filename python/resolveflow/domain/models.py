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
    region: Literal["ca-central"] = "ca-central"
    service: Literal["payments-api"] = "payments-api"
    raw_text: str
    error_code: Literal["PYM-431"] = "PYM-431"
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


class FinalResponse(FrozenModel):
    status: Literal["verified_fixture"] = "verified_fixture"
    route: Literal["Payments Platform"] = "Payments Platform"
    summary: str
    recommended_steps: tuple[str, ...]
    unknowns: tuple[str, ...]
    citations: tuple[Citation, ...]
    provider: Literal["recorded_fixture"] = "recorded_fixture"
    verifier_status: Literal["fixture_supported"] = "fixture_supported"


class TraceEvent(FrozenModel):
    sequence: int
    event_id: str
    occurred_at: datetime
    actor: str
    component: str
    event_name: str
    outcome: Literal["ok", "needs_information"]
    correlation_id: str
    safe_detail: dict[str, Any]


class AuditEvent(TraceEvent):
    previous_event_hash: str | None = None
    event_hash: str


class ActionBoundary(FrozenModel):
    action_type: Literal["create_jira_issue"] = "create_jira_issue"
    state: Literal["pending_approval"] = "pending_approval"
    connector: Literal["synthetic_not_dispatched"] = "synthetic_not_dispatched"
    summary: str
    team: Literal["Payments Platform"] = "Payments Platform"


class RunSnapshot(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    provenance: Literal["recorded_fixture"] = "recorded_fixture"
    generated_at: datetime
    run_id: str
    build_id: Literal["foundation-v1"] = "foundation-v1"
    commit: str
    model_policy: Literal["fixture-only-1.0"] = "fixture-only-1.0"
    corpus_version: Literal["hero-corpus-1.0"] = "hero-corpus-1.0"
    identity_snapshot: IdentitySnapshot
    retrieval: RetrievalTrace
    case: CanonicalCase
    context: tuple[ContextResult, ...]
    response: FinalResponse
    action: ActionBoundary
    trace: tuple[TraceEvent, ...]
    content_hash: str


class VersionResponse(FrozenModel):
    version: str
    build_id: str
    commit: str
    schema_version: str = "1.0"


class HealthResponse(FrozenModel):
    status: Literal["ok", "ready"]
