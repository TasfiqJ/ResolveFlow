from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel


class ActionState(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    DISPATCHING = "dispatching"
    RECONCILING = "reconciling"
    ACKNOWLEDGED = "acknowledged"
    COMPLETE = "complete"
    RETRY_WAIT = "retry_wait"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class PermissionResult(str, Enum):
    ALLOWED = "allowed"
    DENIED_MISSING_PERMISSION = "denied_missing_permission"
    DENIED_SERVICE_IDENTITY = "denied_service_identity"
    DENIED_NOT_HUMAN = "denied_not_human"
    DENIED_POLICY = "denied_policy"


class ActionPayload(FrozenModel):
    action_type: Literal["create_jira_issue"] = "create_jira_issue"
    summary: str = Field(min_length=1, max_length=160)
    team: Literal["Payments Platform"] = "Payments Platform"
    priority: Literal["High", "Medium", "Low"]
    verified_description: str = Field(min_length=1, max_length=4000)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    unknowns: tuple[str, ...] = ()
    risk: Literal["low", "medium", "high"]


class ActionProposal(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    proposal_id: str
    logical_action_id: str
    run_id: str
    tenant_id: str
    graph_hash: str
    supporting_claim_ids: tuple[str, ...] = Field(min_length=1)
    payload: ActionPayload
    payload_digest: str
    idempotency_key: str
    state: ActionState
    created_at: datetime
    expires_at: datetime
    revision: int = Field(ge=1)
    invalidated_by_proposal_id: str | None = None

    @model_validator(mode="after")
    def expiry_follows_creation(self) -> ActionProposal:
        if self.expires_at <= self.created_at:
            raise ValueError("proposal expiry must be later than creation")
        return self


class ApprovalCommand(FrozenModel):
    proposal_id: str
    payload_digest: str
    actor_id: str
    permissions: frozenset[str] = frozenset()
    authenticated: bool = True
    human: bool = True
    policy_allows: bool = True


class ApprovalRecord(FrozenModel):
    approval_id: str
    proposal_id: str
    payload_digest: str
    approver_id: str
    permission_result: PermissionResult
    approved_at: datetime
    expires_at: datetime


class RejectionCommand(FrozenModel):
    proposal_id: str
    actor_id: str
    reason: str = Field(min_length=1, max_length=500)
    permissions: frozenset[str] = frozenset()
    authenticated: bool = True
    human: bool = True


class ActionDecision(FrozenModel):
    accepted: bool
    code: str
    proposal: ActionProposal
    approval: ApprovalRecord | None = None


class DispatchPayload(FrozenModel):
    project_key: Literal["SYN"] = "SYN"
    issue_type: Literal["Task"] = "Task"
    summary: str
    team: Literal["Payments Platform"]
    priority: Literal["High", "Medium", "Low"]
    description: str
    idempotency_marker: str


class ConnectorDisposition(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    PRE_SEND_FAILURE = "pre_send_failure"
    UNCERTAIN = "uncertain"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    PERMISSION_DENIED = "permission_denied"


class ConnectorResult(FrozenModel):
    disposition: ConnectorDisposition
    request_fingerprint: str
    remote_issue_key: str | None = None
    provider_request_id: str | None = None
    safe_error_code: str | None = None
    retry_after_seconds: int | None = None


class ReconciliationResult(FrozenModel):
    found: bool
    idempotency_key: str
    remote_issue_key: str | None = None
    safe_code: str


class ActionAttempt(FrozenModel):
    attempt_id: str
    proposal_id: str
    logical_action_id: str
    idempotency_key: str
    payload_digest: str
    attempt_number: int = Field(ge=1)
    started_at: datetime
    finished_at: datetime
    request_fingerprint: str
    disposition: ConnectorDisposition
    safe_error_code: str | None = None
    retry_decision: Literal["none", "retry", "reconcile", "dead_letter"]
    reconciliation: ReconciliationResult | None = None
    remote_issue_key: str | None = None


class RetryPolicy(FrozenModel):
    policy_id: Literal["action-retry-1.0"] = "action-retry-1.0"
    max_attempts: int = Field(default=5, ge=1, le=10)
    base_seconds: int = Field(default=5, ge=1)
    maximum_seconds: int = Field(default=300, ge=1)
    jitter_percent: int = Field(default=20, ge=0, le=50)


class DispatchResult(FrozenModel):
    proposal: ActionProposal
    attempt: ActionAttempt | None
    next_attempt_at: datetime | None = None
