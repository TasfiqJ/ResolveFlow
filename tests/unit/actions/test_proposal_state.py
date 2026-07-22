from __future__ import annotations

from datetime import timedelta

from resolveflow.actions.models import (
    ActionState,
    ApprovalCommand,
    RejectionCommand,
)
from resolveflow.actions.service import ActionService, action_payload_digest

from tests.action_helpers import NOW, fixture_proposal


def test_exact_digest_and_permission_are_required() -> None:
    service = ActionService()
    proposal = fixture_proposal()
    denied = service.approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id="contractor_synthetic",
            permissions=frozenset(),
        ),
        NOW,
    )
    assert not denied.accepted
    assert denied.code == "denied_missing_permission"
    assert denied.proposal.state is ActionState.PENDING_APPROVAL

    mismatch = service.approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest="sha256:" + "0" * 64,
            actor_id="human_approver",
            permissions=frozenset({"approve_jira"}),
        ),
        NOW,
    )
    assert not mismatch.accepted
    assert mismatch.code == "payload_digest_mismatch"


def test_approval_rejection_expiry_and_revision_invalidation() -> None:
    service = ActionService()
    proposal = fixture_proposal()
    approved = service.approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id="human_approver",
            permissions=frozenset({"approve_jira"}),
        ),
        NOW,
    )
    assert approved.accepted
    assert approved.proposal.state is ActionState.APPROVED
    assert approved.approval is not None

    rejected = service.reject(
        proposal,
        RejectionCommand(
            proposal_id=proposal.proposal_id,
            actor_id="human_approver",
            reason="Cluster context must be supplied first",
            permissions=frozenset({"approve_jira"}),
        ),
        NOW,
    )
    assert rejected.accepted
    assert rejected.proposal.state is ActionState.REJECTED

    expired = service.approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id="human_approver",
            permissions=frozenset({"approve_jira"}),
        ),
        proposal.expires_at,
    )
    assert not expired.accepted
    assert expired.proposal.state is ActionState.EXPIRED

    changed_payload = proposal.payload.model_copy(update={"priority": "Medium"})
    invalidated, replacement = service.revise(proposal, changed_payload, NOW + timedelta(minutes=1))
    assert invalidated.state is ActionState.INVALIDATED
    assert replacement.state is ActionState.PENDING_APPROVAL
    assert replacement.revision == 2
    assert replacement.payload_digest == action_payload_digest(changed_payload)
    assert replacement.payload_digest != proposal.payload_digest
    assert replacement.idempotency_key == proposal.idempotency_key


def test_worker_service_identity_cannot_approve() -> None:
    proposal = fixture_proposal()
    decision = ActionService().approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id="worker_action_1",
            permissions=frozenset({"approve_jira"}),
        ),
        NOW,
    )
    assert not decision.accepted
    assert decision.code == "denied_service_identity"
