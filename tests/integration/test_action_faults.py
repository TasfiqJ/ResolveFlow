from __future__ import annotations

import pytest
from resolveflow.actions.connectors import ConnectorFault, SyntheticJiraConnector
from resolveflow.actions.dispatcher import ActionDispatcher
from resolveflow.actions.models import ActionState, ApprovalCommand, RetryPolicy
from resolveflow.actions.service import ActionService

from tests.action_helpers import NOW, fixture_proposal


def _approved():
    proposal = fixture_proposal()
    decision = ActionService().approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal.proposal_id,
            payload_digest=proposal.payload_digest,
            actor_id="human_approver",
            permissions=frozenset({"approve_jira"}),
        ),
        NOW,
    )
    assert decision.approval is not None
    return decision.proposal, decision.approval


@pytest.mark.parametrize(
    ("fault", "expected"),
    [
        (ConnectorFault.TIMEOUT_BEFORE_SEND, ActionState.RETRY_WAIT),
        (ConnectorFault.RATE_LIMITED, ActionState.RETRY_WAIT),
        (ConnectorFault.SERVER_ERROR, ActionState.RETRY_WAIT),
        (ConnectorFault.PERMISSION_DENIED, ActionState.DEAD_LETTER),
    ],
)
def test_fault_classification_and_bounded_retry(fault, expected) -> None:
    proposal, approval = _approved()
    connector = SyntheticJiraConnector()
    connector.queue_faults(fault)
    result = ActionDispatcher(connector).dispatch(
        proposal=proposal,
        approval=approval,
        worker_id="worker_actions_1",
        attempt_number=1,
        now=NOW,
    )
    assert result.proposal.state is expected
    assert result.attempt is not None
    assert connector.issue_count == 0


@pytest.mark.parametrize(
    "fault", [ConnectorFault.TIMEOUT_AFTER_ACCEPT, ConnectorFault.ACKNOWLEDGEMENT_LOST]
)
def test_uncertain_send_reconciles_before_retry_and_never_duplicates(fault) -> None:
    proposal, approval = _approved()
    connector = SyntheticJiraConnector()
    connector.queue_faults(fault)
    dispatcher = ActionDispatcher(connector)
    result = dispatcher.dispatch(
        proposal=proposal,
        approval=approval,
        worker_id="worker_actions_1",
        attempt_number=1,
        now=NOW,
    )
    assert result.proposal.state is ActionState.COMPLETE
    assert result.attempt is not None
    assert result.attempt.reconciliation is not None
    assert result.attempt.reconciliation.found
    assert connector.issue_count == 1

    duplicate = dispatcher.dispatch(
        proposal=proposal,
        approval=approval,
        worker_id="worker_actions_2",
        attempt_number=2,
        now=NOW,
    )
    assert duplicate.proposal.state is ActionState.COMPLETE
    assert connector.issue_count == 1
    assert duplicate.attempt is not None
    assert duplicate.attempt.idempotency_key == result.attempt.idempotency_key


def test_max_attempt_reaches_dead_letter() -> None:
    proposal, approval = _approved()
    connector = SyntheticJiraConnector()
    connector.queue_faults(ConnectorFault.SERVER_ERROR)
    dispatcher = ActionDispatcher(connector, RetryPolicy(max_attempts=1))
    result = dispatcher.dispatch(
        proposal=proposal,
        approval=approval,
        worker_id="worker_actions_1",
        attempt_number=1,
        now=NOW,
    )
    assert result.proposal.state is ActionState.DEAD_LETTER
    assert result.attempt is not None
    assert result.attempt.retry_decision == "dead_letter"


def test_unapproved_expired_tampered_or_non_worker_dispatch_is_blocked() -> None:
    proposal = fixture_proposal()
    dispatcher = ActionDispatcher(SyntheticJiraConnector())
    with pytest.raises(ValueError, match="approved"):
        dispatcher.dispatch(
            proposal=proposal,
            approval=None,
            worker_id="worker_actions_1",
            attempt_number=1,
            now=NOW,
        )
    approved, approval = _approved()
    with pytest.raises(PermissionError, match="worker"):
        dispatcher.dispatch(
            proposal=approved,
            approval=approval,
            worker_id="user_human",
            attempt_number=1,
            now=NOW,
        )
    with pytest.raises(ValueError, match="expired"):
        dispatcher.dispatch(
            proposal=approved,
            approval=approval,
            worker_id="worker_actions_1",
            attempt_number=1,
            now=approved.expires_at,
        )
