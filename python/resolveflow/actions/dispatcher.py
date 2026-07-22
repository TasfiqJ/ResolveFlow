from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from resolveflow.actions.connectors import JiraConnector
from resolveflow.actions.models import (
    ActionAttempt,
    ActionProposal,
    ActionState,
    ApprovalRecord,
    ConnectorDisposition,
    DispatchPayload,
    DispatchResult,
    RetryPolicy,
)
from resolveflow.actions.service import action_payload_digest
from resolveflow.domain.evidence import stable_id
from resolveflow.domain.hashing import checksum


def reconstruct_dispatch_payload(proposal: ActionProposal) -> DispatchPayload:
    payload = proposal.payload
    evidence = ", ".join(payload.evidence_refs)
    unknowns = "; ".join(payload.unknowns) if payload.unknowns else "none declared"
    description = (
        f"{payload.verified_description}\n\nEvidence: {evidence}\n"
        f"Unknowns: {unknowns}\nRisk: {payload.risk}\n"
        f"ResolveFlow-Idempotency: {proposal.idempotency_key}"
    )
    return DispatchPayload(
        summary=payload.summary,
        team=payload.team,
        priority=payload.priority,
        description=description,
        idempotency_marker=proposal.idempotency_key,
    )


def bounded_backoff(policy: RetryPolicy, attempt_number: int, idempotency_key: str) -> int:
    power = max(0, attempt_number - 1)
    exponential: int = min(policy.maximum_seconds, policy.base_seconds * (2**power))
    if policy.jitter_percent == 0:
        return int(exponential)
    digest = int(checksum({"key": idempotency_key, "attempt": attempt_number})[-8:], 16)
    span = max(1, exponential * policy.jitter_percent // 100)
    jitter = digest % (span * 2 + 1) - span
    return int(max(1, min(policy.maximum_seconds, exponential + jitter)))


@dataclass
class ActionDispatcher:
    connector: JiraConnector
    retry_policy: RetryPolicy = RetryPolicy()
    dispatch_enabled: bool = True

    def dispatch(
        self,
        *,
        proposal: ActionProposal,
        approval: ApprovalRecord | None,
        worker_id: str,
        attempt_number: int,
        now: datetime,
        current_permission: bool = True,
    ) -> DispatchResult:
        if not self.dispatch_enabled:
            return DispatchResult(
                proposal=proposal.model_copy(update={"state": ActionState.CANCELLED}),
                attempt=None,
            )
        self._validate(proposal, approval, worker_id, now, current_permission)
        dispatching = proposal.model_copy(update={"state": ActionState.DISPATCHING})
        wire_payload = reconstruct_dispatch_payload(dispatching)
        connector_result = self.connector.create_issue(wire_payload)
        reconciliation = None
        retry_decision: str = "none"
        next_attempt_at = None
        final_state = ActionState.COMPLETE
        remote_key = connector_result.remote_issue_key

        if connector_result.disposition is ConnectorDisposition.UNCERTAIN:
            dispatching = dispatching.model_copy(update={"state": ActionState.RECONCILING})
            reconciliation = self.connector.reconcile(dispatching.idempotency_key)
            if reconciliation.found:
                final_state = ActionState.COMPLETE
                remote_key = reconciliation.remote_issue_key
            elif attempt_number >= self.retry_policy.max_attempts:
                final_state = ActionState.DEAD_LETTER
                retry_decision = "dead_letter"
            else:
                final_state = ActionState.RETRY_WAIT
                retry_decision = "retry"
        elif connector_result.disposition in {
            ConnectorDisposition.PRE_SEND_FAILURE,
            ConnectorDisposition.RATE_LIMITED,
            ConnectorDisposition.SERVER_ERROR,
        }:
            if attempt_number >= self.retry_policy.max_attempts:
                final_state = ActionState.DEAD_LETTER
                retry_decision = "dead_letter"
            else:
                final_state = ActionState.RETRY_WAIT
                retry_decision = "retry"
        elif connector_result.disposition is ConnectorDisposition.PERMISSION_DENIED:
            final_state = ActionState.DEAD_LETTER
            retry_decision = "dead_letter"

        if retry_decision == "retry":
            delay = connector_result.retry_after_seconds or bounded_backoff(
                self.retry_policy, attempt_number, dispatching.idempotency_key
            )
            delay = min(self.retry_policy.maximum_seconds, max(1, delay))
            next_attempt_at = now + timedelta(seconds=delay)
        finished = now
        attempt = ActionAttempt(
            attempt_id=stable_id(
                "attempt",
                {
                    "proposal": proposal.proposal_id,
                    "number": attempt_number,
                    "fingerprint": connector_result.request_fingerprint,
                },
            ),
            proposal_id=proposal.proposal_id,
            logical_action_id=proposal.logical_action_id,
            idempotency_key=proposal.idempotency_key,
            payload_digest=proposal.payload_digest,
            attempt_number=attempt_number,
            started_at=now,
            finished_at=finished,
            request_fingerprint=connector_result.request_fingerprint,
            disposition=connector_result.disposition,
            safe_error_code=connector_result.safe_error_code,
            retry_decision=retry_decision,
            reconciliation=reconciliation,
            remote_issue_key=remote_key,
        )
        return DispatchResult(
            proposal=dispatching.model_copy(update={"state": final_state}),
            attempt=attempt,
            next_attempt_at=next_attempt_at,
        )

    @staticmethod
    def _validate(
        proposal: ActionProposal,
        approval: ApprovalRecord | None,
        worker_id: str,
        now: datetime,
        current_permission: bool,
    ) -> None:
        if not worker_id.startswith("worker_"):
            raise PermissionError("dispatch_requires_worker_identity")
        if proposal.state not in {ActionState.APPROVED, ActionState.RETRY_WAIT}:
            raise ValueError("dispatch_requires_approved_action")
        if approval is None or approval.proposal_id != proposal.proposal_id:
            raise ValueError("dispatch_requires_exact_approval")
        if approval.payload_digest != proposal.payload_digest:
            raise ValueError("approved_payload_mismatch")
        if action_payload_digest(proposal.payload) != proposal.payload_digest:
            raise ValueError("proposal_payload_tampered")
        if now >= proposal.expires_at or now >= approval.expires_at:
            raise ValueError("approved_proposal_expired")
        if not current_permission:
            raise PermissionError("dispatch_permission_revoked")
