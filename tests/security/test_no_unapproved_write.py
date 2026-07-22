from __future__ import annotations

import pytest
from resolveflow.actions.connectors import DisabledJiraCloudConnector, SyntheticJiraConnector
from resolveflow.actions.dispatcher import ActionDispatcher

from tests.action_helpers import NOW, fixture_proposal


def test_no_connector_is_called_before_approval() -> None:
    proposal = fixture_proposal()
    connector = SyntheticJiraConnector()
    with pytest.raises(ValueError, match="approved"):
        ActionDispatcher(connector).dispatch(
            proposal=proposal,
            approval=None,
            worker_id="worker_actions",
            attempt_number=1,
            now=NOW,
        )
    assert connector.issue_count == 0


def test_real_jira_adapter_is_disabled_by_construction() -> None:
    connector = DisabledJiraCloudConnector()
    with pytest.raises(RuntimeError, match="disabled"):
        connector.reconcile("sha256:synthetic")
