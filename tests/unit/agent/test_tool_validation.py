from __future__ import annotations

import json
import time

from resolveflow.agent.contracts import ToolCallRequest
from resolveflow.agent.tools import ToolRegistry

from tests.agent_helpers import governed_inputs


def test_tool_calls_require_allowlisted_name_and_strict_local_schema() -> None:
    case, context, _, _, _ = governed_inputs()
    registry = ToolRegistry(case, context)
    calls = (
        ToolCallRequest(
            tool_call_id="unknown",
            name="fetch_url",
            arguments_json='{"url":"https://example.test"}',
        ),
        ToolCallRequest(
            tool_call_id="extra",
            name="query_rollout_record",
            arguments_json=json.dumps(
                {"rollout_id": "rollout-payments-2026-07-15", "sql": "SELECT *"}
            ),
        ),
        ToolCallRequest(
            tool_call_id="malformed",
            name="query_rollout_record",
            arguments_json="{not-json",
        ),
    )
    for call in calls:
        result, trace = registry.execute(call, timeout_seconds=0.1)
        assert result.status == "rejected"
        assert trace.status == "rejected"
        assert trace.external_write is False
    assert registry.adapter_invocations == []


def test_valid_read_tool_is_logged_with_provenance() -> None:
    case, context, _, _, _ = governed_inputs()
    registry = ToolRegistry(case, context)
    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="valid",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.1,
    )
    assert result.status == "ok"
    assert result.provenance_ids == ("rollout-row-20260715",)
    assert trace.authorization == "allowed"


def test_tool_timeout_is_explicit_and_never_writes() -> None:
    case, context, _, _, _ = governed_inputs()
    registry = ToolRegistry(case, context)

    def slow_handler(_: object) -> tuple[dict[str, object], tuple[str, ...]]:
        time.sleep(0.05)
        return {}, ()

    registry._handlers["query_rollout_record"] = slow_handler  # type: ignore[assignment]
    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="slow",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.001,
    )
    assert result.status == "timeout"
    assert trace.safe_error_code == "tool_timeout"
    assert trace.external_write is False
