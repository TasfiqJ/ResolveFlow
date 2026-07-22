from __future__ import annotations

import time

from resolveflow.agent.contracts import (
    AgentBudgets,
    ChatRequest,
    ChatResponse,
    FinishReason,
    ProviderTimeoutError,
    ProviderUsage,
    ToolCallRequest,
)

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


def test_provider_and_round_budgets_terminate_endless_tool_loop() -> None:
    result = run_governed(
        EndlessToolProvider(),
        budgets=AgentBudgets(max_tool_rounds=1, max_provider_calls=3),
    )
    assert result.terminal_reason == "tool_round_budget_exhausted"
    assert result.provider_calls <= 3
    assert result.response.needs_review is True
    assert result.response.route is None


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


def test_wall_clock_budget_interrupts_hanging_provider_wait() -> None:
    result = run_governed(HangingProvider(), budgets=AgentBudgets(wall_clock_seconds=0.05))
    assert result.terminal_reason == "provider_timeout"
    assert result.provider_traces[0].status == "timeout"
