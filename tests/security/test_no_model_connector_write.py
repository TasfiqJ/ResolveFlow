from __future__ import annotations

from resolveflow.agent.contracts import ToolCallRequest
from resolveflow.agent.tools import ToolRegistry

from tests.agent_helpers import governed_inputs, run_governed


def test_model_has_no_connector_write_tool() -> None:
    case, context, _, _, _ = governed_inputs()
    registry = ToolRegistry(case, context)
    assert {item.authority for item in registry.definitions} == {
        "read_only",
        "inert_proposal",
    }
    assert "create_jira_issue" not in {item.name for item in registry.definitions}
    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="write",
            name="create_jira_issue",
            arguments_json='{"summary":"bypass"}',
        ),
        timeout_seconds=0.1,
    )
    assert result.status == "rejected"
    assert trace.external_write is False


def test_all_observed_tool_traces_have_no_external_write() -> None:
    result = run_governed()
    assert result.tool_traces
    assert all(item.external_write is False for item in result.tool_traces)
