from __future__ import annotations

from resolveflow.agent.contracts import ToolCallRequest
from resolveflow.agent.tools import ToolRegistry

from tests.agent_helpers import governed_inputs


def test_forbidden_tool_arguments_reach_no_adapter() -> None:
    case, context, _, _, _ = governed_inputs()
    registry = ToolRegistry(case, context)
    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="cross_case",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"another-tenant-rollout"}',
        ),
        timeout_seconds=0.1,
    )
    assert result.status == "rejected"
    assert trace.authorization == "denied"
    assert registry.adapter_invocations == []
