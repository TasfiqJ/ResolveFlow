from __future__ import annotations

import json
import time

import pytest
from resolveflow.agent.contracts import (
    AgentBudgets,
    ChatRequest,
    ChatResponse,
    FinishReason,
    ProviderTimeoutError,
    ProviderUsage,
    ToolCallRequest,
)
from resolveflow.agent.fixture import FixtureChatAdapter

from tests.agent_helpers import run_governed


class EndlessToolProvider:
    provider_name = "recorded_fixture"

    def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            response_id="endless",
            model=request.model,
            finish_reason=FinishReason.TOOL_CALL,
            text="",
            tool_calls=(
                ToolCallRequest(
                    tool_call_id="loop",
                    name="query_rollout_record",
                    arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
                ),
            ),
            usage=ProviderUsage(input_tokens=40, output_tokens=10),
        )


class TimeoutProvider:
    provider_name = "recorded_fixture"

    def chat(self, request: ChatRequest) -> ChatResponse:
        raise ProviderTimeoutError("provider_timeout")


class HighUsageProvider:
    provider_name = "recorded_fixture"

    def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            response_id="high-usage",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text="{}",
            usage=ProviderUsage(input_tokens=240, output_tokens=64),
        )


class HangingProvider:
    provider_name = "recorded_fixture"

    def chat(self, request: ChatRequest) -> ChatResponse:
        time.sleep(0.2)
        return HighUsageProvider().chat(request)


class LiveShapeProvider(HighUsageProvider):
    provider_name = "cohere"

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        return super().chat(request)


class FencedFindingsProvider(FixtureChatAdapter):
    def chat(self, request: ChatRequest) -> ChatResponse:
        response = super().chat(request)
        if request.pass_kind.value == "evidence" and not response.tool_calls:
            return response.model_copy(update={"text": f"```json\n{response.text}\n```"})
        return response


class RepairingFindingsProvider(FixtureChatAdapter):
    def __init__(self) -> None:
        self.evidence_request: ChatRequest | None = None

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.pass_kind.value == "findings":
            assert self.evidence_request is not None
            return ChatResponse(
                response_id="repaired-findings",
                model=request.model,
                finish_reason=FinishReason.COMPLETE,
                text=json.dumps(self._findings(self.evidence_request), sort_keys=True),
                usage=ProviderUsage(input_tokens=120, output_tokens=80),
            )
        response = super().chat(request)
        if request.pass_kind.value == "evidence":
            self.evidence_request = request
            if not response.tool_calls:
                return response.model_copy(
                    update={
                        "text": json.dumps(
                            {
                                "schema_version": "1.0",
                                "disposition": "needs_review",
                                "needs_review": True,
                            }
                        )
                    }
                )
        return response


class StructureBudgetOverflowProvider(FixtureChatAdapter):
    def chat(self, request: ChatRequest) -> ChatResponse:
        response = super().chat(request)
        if request.pass_kind.value == "structure":
            return response.model_copy(
                update={"usage": ProviderUsage(input_tokens=100, output_tokens=64)}
            )
        return response


def test_provider_and_round_budgets_terminate_endless_tool_loop() -> None:
    result = run_governed(
        EndlessToolProvider(),
        budgets=AgentBudgets(max_tool_rounds=1, max_provider_calls=3),
    )
    assert result.terminal_reason == "tool_round_budget_exhausted"
    assert result.provider_calls <= 3
    assert result.response.needs_review is True
    assert result.response.route is None


def test_render_call_reservation_must_leave_evidence_capacity() -> None:
    with pytest.raises(ValueError, match="leave at least one evidence call"):
        AgentBudgets(max_provider_calls=2, reserved_provider_calls_for_render=2)


def test_provider_timeout_is_visible_and_falls_back() -> None:
    result = run_governed(TimeoutProvider())
    assert result.terminal_reason == "provider_timeout"
    assert result.provider_traces[0].status == "timeout"
    assert result.response.status == "needs_review"


def test_token_budget_is_fixed_and_enforced() -> None:
    result = run_governed(
        HighUsageProvider(),
        budgets=AgentBudgets(max_total_tokens=256, max_output_tokens_per_call=64),
    )
    assert result.terminal_reason == "token_budget_exhausted"
    assert result.provider_calls == 1
    assert result.response.needs_review is True


def test_live_evidence_request_includes_the_required_findings_schema() -> None:
    provider = LiveShapeProvider()
    run_governed(provider)

    payload = json.loads(str(provider.requests[0].messages[1]["content"]))
    assert payload["required_output_schema"]["title"] == "FirstPassFindings"
    assert set(payload["required_output_schema"]["properties"]) >= {
        "claims",
        "citations",
        "unknowns",
        "requested_proposal",
    }


def test_whole_markdown_json_fence_is_accepted_before_schema_validation() -> None:
    result = run_governed(FencedFindingsProvider())

    assert result.terminal_reason == "complete"
    assert result.response.route == "Payments Platform"
    assert result.response.needs_review is False


def test_malformed_findings_use_one_bounded_schema_repair_pass() -> None:
    result = run_governed(
        RepairingFindingsProvider(),
        budgets=AgentBudgets(max_provider_calls=5, max_total_tokens=4096),
    )

    assert tuple(trace.pass_kind.value for trace in result.provider_traces) == (
        "evidence",
        "evidence",
        "findings",
        "structure",
    )
    assert result.provider_traces[1].status == "malformed"
    assert result.provider_traces[2].status == "ok"
    assert result.terminal_reason == "complete"
    assert result.response.route == "Payments Platform"


def test_structure_pass_overflow_is_reported_as_token_budget_exhaustion() -> None:
    result = run_governed(
        StructureBudgetOverflowProvider(),
        budgets=AgentBudgets(max_total_tokens=512, max_output_tokens_per_call=64),
    )

    assert result.total_tokens == 608
    assert result.terminal_reason == "token_budget_exhausted"
    assert result.response.needs_review is True


def test_wall_clock_budget_interrupts_hanging_provider_wait() -> None:
    result = run_governed(HangingProvider(), budgets=AgentBudgets(wall_clock_seconds=0.05))
    assert result.terminal_reason == "provider_timeout"
    assert result.provider_traces[0].status == "timeout"
