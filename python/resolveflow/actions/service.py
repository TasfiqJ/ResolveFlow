from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from resolveflow.actions.models import (
    ActionDecision,
    ActionPayload,
    ActionProposal,
    ActionState,
    ApprovalCommand,
    ApprovalRecord,
    PermissionResult,
    RejectionCommand,
)
from resolveflow.domain.evidence import stable_id
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import FinalResponse

if TYPE_CHECKING:
    from resolveflow.verifier.models import EvidenceGraph


def _permission(command: ApprovalCommand) -> PermissionResult:
    if not command.authenticated or "approve_jira" not in command.permissions:
        return PermissionResult.DENIED_MISSING_PERMISSION
    if command.actor_id.startswith("service_") or command.actor_id.startswith("worker_"):
        return PermissionResult.DENIED_SERVICE_IDENTITY
    if not command.human:
        return PermissionResult.DENIED_NOT_HUMAN
    if not command.policy_allows:
        return PermissionResult.DENIED_POLICY
    return PermissionResult.ALLOWED


def action_payload_digest(payload: ActionPayload) -> str:
    """Digest exactly the immutable, human-visible proposal payload."""

    return checksum(payload)


def action_idempotency_key(logical_action_id: str) -> str:
    return checksum({"logical_action_id": logical_action_id, "action_type": "create_jira_issue"})


@dataclass
class ActionService:
    """Pure state machine; persistence adapters commit its result with an audit event."""

    proposal_ttl: timedelta = timedelta(hours=2)

    def create_proposal(
        self,
        *,
        run_id: str,
        tenant_id: str,
        graph: EvidenceGraph,
        response: FinalResponse,
        now: datetime,
    ) -> ActionProposal:
        if graph.run_id != run_id or response.graph_hash != graph.graph_hash:
            raise ValueError("proposal evidence graph does not match the run response")
        if not graph.permitted_proposals:
            raise ValueError("verified evidence does not permit a Jira proposal")
        permitted = graph.permitted_proposals[0]
        claims = {claim.claim_id: claim for claim in graph.claims}
        supporting = tuple(claims.get(claim_id) for claim_id in permitted.supporting_claim_ids)
        if not supporting or any(
            claim is None or claim.status.value != "supported" or not claim.action_supporting
            for claim in supporting
        ):
            raise ValueError("proposal support must contain only verified action claims")
        evidence_refs = tuple(
            sorted(
                citation.citation_id
                for citation in graph.citations
                if citation.claim_id in permitted.supporting_claim_ids
                and citation.authorized
                and citation.fresh
                and citation.supports_claim
            )
        )
        if not evidence_refs:
            raise ValueError("proposal requires verified evidence references")
        payload = ActionPayload(
            summary="Investigate PYM-431 after issuer-routing-v3 rollout",
            priority="High",
            verified_description=(
                f"{response.summary}\n\nVerified next steps:\n- "
                + "\n- ".join(response.recommended_steps)
            ),
            evidence_refs=evidence_refs,
            unknowns=response.unknowns,
            risk="medium",
        )
        logical_action_id = stable_id(
            "action", {"run_id": run_id, "action_type": payload.action_type}
        )
        digest = action_payload_digest(payload)
        proposal_id = stable_id(
            "proposal", {"logical_action_id": logical_action_id, "revision": 1, "digest": digest}
        )
        return ActionProposal(
            proposal_id=proposal_id,
            logical_action_id=logical_action_id,
            run_id=run_id,
            tenant_id=tenant_id,
            graph_hash=graph.graph_hash,
            supporting_claim_ids=permitted.supporting_claim_ids,
            payload=payload,
            payload_digest=digest,
            idempotency_key=action_idempotency_key(logical_action_id),
            state=ActionState.PENDING_APPROVAL,
            created_at=now,
            expires_at=now + self.proposal_ttl,
            revision=1,
        )

    def approve(
        self, proposal: ActionProposal, command: ApprovalCommand, now: datetime
    ) -> ActionDecision:
        permission = _permission(command)
        if permission is not PermissionResult.ALLOWED:
            return ActionDecision(accepted=False, code=permission.value, proposal=proposal)
        if proposal.state is not ActionState.PENDING_APPROVAL:
            return ActionDecision(accepted=False, code="invalid_state", proposal=proposal)
        if now >= proposal.expires_at:
            return ActionDecision(
                accepted=False,
                code="proposal_expired",
                proposal=proposal.model_copy(update={"state": ActionState.EXPIRED}),
            )
        if command.proposal_id != proposal.proposal_id:
            return ActionDecision(accepted=False, code="proposal_mismatch", proposal=proposal)
        if command.payload_digest != proposal.payload_digest:
            return ActionDecision(accepted=False, code="payload_digest_mismatch", proposal=proposal)
        approved = proposal.model_copy(update={"state": ActionState.APPROVED})
        approval = ApprovalRecord(
            approval_id=stable_id(
                "approval",
                {
                    "proposal_id": proposal.proposal_id,
                    "digest": proposal.payload_digest,
                    "actor": command.actor_id,
                    "at": now,
                },
            ),
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            approver_id=command.actor_id,
            permission_result=permission,
            approved_at=now,
            expires_at=proposal.expires_at,
        )
        return ActionDecision(accepted=True, code="approved", proposal=approved, approval=approval)

    def reject(
        self, proposal: ActionProposal, command: RejectionCommand, now: datetime
    ) -> ActionDecision:
        approval_shape = ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id=command.actor_id,
            permissions=command.permissions,
            authenticated=command.authenticated,
            human=command.human,
        )
        permission = _permission(approval_shape)
        if permission is not PermissionResult.ALLOWED:
            return ActionDecision(accepted=False, code=permission.value, proposal=proposal)
        if proposal.state is not ActionState.PENDING_APPROVAL:
            return ActionDecision(accepted=False, code="invalid_state", proposal=proposal)
        if now >= proposal.expires_at:
            return ActionDecision(
                accepted=False,
                code="proposal_expired",
                proposal=proposal.model_copy(update={"state": ActionState.EXPIRED}),
            )
        return ActionDecision(
            accepted=True,
            code="rejected",
            proposal=proposal.model_copy(update={"state": ActionState.REJECTED}),
        )

    def revise(
        self, proposal: ActionProposal, payload: ActionPayload, now: datetime
    ) -> tuple[ActionProposal, ActionProposal]:
        if proposal.state in {ActionState.COMPLETE, ActionState.CANCELLED}:
            raise ValueError("terminal proposal cannot be revised")
        invalidated = proposal.model_copy(update={"state": ActionState.INVALIDATED})
        digest = action_payload_digest(payload)
        replacement_id = stable_id(
            "proposal",
            {
                "logical_action_id": proposal.logical_action_id,
                "revision": proposal.revision + 1,
                "digest": digest,
            },
        )
        invalidated = invalidated.model_copy(update={"invalidated_by_proposal_id": replacement_id})
        replacement = proposal.model_copy(
            update={
                "proposal_id": replacement_id,
                "payload": payload,
                "payload_digest": digest,
                "state": ActionState.PENDING_APPROVAL,
                "created_at": now,
                "expires_at": now + self.proposal_ttl,
                "revision": proposal.revision + 1,
                "invalidated_by_proposal_id": None,
            }
        )
        return invalidated, replacement


def fixture_now() -> datetime:
    return datetime(2026, 7, 21, 0, 0, tzinfo=timezone.utc)
