from __future__ import annotations

import asyncio
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
from resolveflow.agent.tools import ToolRegistry

from tests.agent_helpers import run_governed


class EndlessToolProvider:
    provider_name = "recorded_fixture"

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        if timeout_seconds <= 0:
            raise ProviderTimeoutError("provider_timeout")
        return self.chat(request)

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

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        if timeout_seconds <= 0:
            raise ProviderTimeoutError("provider_timeout")
        return self.chat(request)

    def chat(self, request: ChatRequest) -> ChatResponse:
        raise ProviderTimeoutError("provider_timeout")


class HighUsageProvider:
    provider_name = "recorded_fixture"

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        if timeout_seconds <= 0:
            raise ProviderTimeoutError("provider_timeout")
        return self.chat(request)

    def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            response_id="high-usage",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text="{}",
            usage=ProviderUsage(input_tokens=240, output_tokens=64),
        )


class DeadlineAwareTimeoutProvider:
    provider_name = "recorded_fixture"

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        time.sleep(timeout_seconds)
        raise ProviderTimeoutError("provider_timeout")

    def chat(self, request: ChatRequest) -> ChatResponse:
        raise AssertionError("governed calls must use the deadline-aware entry point")


class LateReturningProvider(HighUsageProvider):
    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        time.sleep(timeout_seconds + 0.01)
        return self.chat(request)


class UnboundedLiveProvider:
    provider_name = "cohere"

    def __init__(self) -> None:
        self.called = False

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.called = True
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
    def __init__(self, repair_finish_reason: FinishReason = FinishReason.COMPLETE) -> None:
        self.evidence_request: ChatRequest | None = None
        self.repair_finish_reason = repair_finish_reason

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.pass_kind.value == "findings":
            assert self.evidence_request is not None
            return ChatResponse(
                response_id="repaired-findings",
                model=request.model,
                finish_reason=self.repair_finish_reason,
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


class SequentialToolProvider(FixtureChatAdapter):
    provider_name = "cohere"

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []
        self.first_evidence_request: ChatRequest | None = None

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if request.pass_kind.value == "structure":
            return self._structure(request)
        if self.first_evidence_request is None:
            self.first_evidence_request = request
        evidence_count = sum(item.pass_kind.value == "evidence" for item in self.requests)
        if evidence_count <= 2:
            name, arguments = (
                (
                    "query_rollout_record",
                    '{"rollout_id":"rollout-payments-2026-07-15"}',
                )
                if evidence_count == 1
                else ("query_prior_incident", '{"error_code":"PYM-431"}')
            )
            return ChatResponse(
                response_id=f"sequential-tool-{evidence_count}",
                model=request.model,
                finish_reason=FinishReason.TOOL_CALL,
                text="",
                tool_calls=(
                    ToolCallRequest(
                        tool_call_id=f"tool-{evidence_count}",
                        name=name,
                        arguments_json=arguments,
                    ),
                ),
                usage=ProviderUsage(input_tokens=40, output_tokens=10),
            )
        assert self.first_evidence_request is not None
        return ChatResponse(
            response_id="sequential-final",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text=json.dumps(self._findings(self.first_evidence_request), sort_keys=True),
            usage=ProviderUsage(input_tokens=80, output_tokens=120),
        )


class IgnoresNoToolsProvider(SequentialToolProvider):
    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.tool_choice == "NONE":
            self.requests.append(request)
            return ChatResponse(
                response_id="ignored-none",
                model=request.model,
                finish_reason=FinishReason.TOOL_CALL,
                text="",
                tool_calls=(
                    ToolCallRequest(
                        tool_call_id="forbidden-final-tool",
                        name="query_rollout_record",
                        arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
                    ),
                ),
                usage=ProviderUsage(input_tokens=40, output_tokens=10),
            )
        return super().chat(request)


class BatchedToolProvider(FixtureChatAdapter):
    def __init__(self, batch_sizes: tuple[int, ...]) -> None:
        self.batch_sizes = batch_sizes
        self.evidence_calls = 0

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.pass_kind.value == "structure":
            return self._structure(request)
        self.evidence_calls += 1
        batch_index = self.evidence_calls - 1
        if batch_index >= len(self.batch_sizes):
            return super().chat(request)
        return ChatResponse(
            response_id=f"batch-{self.evidence_calls}",
            model=request.model,
            finish_reason=FinishReason.TOOL_CALL,
            text="",
            tool_calls=tuple(
                ToolCallRequest(
                    tool_call_id=f"batch-{self.evidence_calls}-tool-{index}",
                    name="query_rollout_record",
                    arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
                )
                for index in range(self.batch_sizes[batch_index])
            ),
            usage=ProviderUsage(input_tokens=20, output_tokens=10),
        )


def test_provider_and_round_budgets_terminate_endless_tool_loop() -> None:
    result = run_governed(
        EndlessToolProvider(),
        budgets=AgentBudgets(max_tool_rounds=1, max_provider_calls=3),
    )
    assert result.terminal_reason == "tool_round_budget_exhausted"
    assert result.provider_calls <= 3
    assert result.response.needs_review is True
    assert result.response.route is None


def test_tool_calls_over_per_response_limit_are_rejected_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invocations: list[str] = []
    original = ToolRegistry._rollout

    async def counted(self: ToolRegistry, arguments: object):
        invocations.append("rollout")
        return await original(self, arguments)  # type: ignore[arg-type]

    monkeypatch.setattr(ToolRegistry, "_rollout", counted)
    result = run_governed(
        BatchedToolProvider((3,)),
        budgets=AgentBudgets(
            max_tool_calls_per_response=2,
            max_tool_calls_per_run=4,
        ),
    )

    assert result.terminal_reason == "tool_call_response_budget_exhausted"
    assert invocations == []
    assert len(result.tool_traces) == 3
    assert all(item.status == "rejected" for item in result.tool_traces)
    assert all(
        item.safe_error_code == "tool_call_response_budget_exhausted" for item in result.tool_traces
    )


def test_tool_calls_over_run_limit_reject_the_whole_overflow_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invocations: list[str] = []
    original = ToolRegistry._rollout

    def counted(self: ToolRegistry, arguments: object):
        invocations.append("rollout")
        return original(self, arguments)  # type: ignore[arg-type]

    monkeypatch.setattr(ToolRegistry, "_rollout", counted)
    result = run_governed(
        BatchedToolProvider((2, 2)),
        budgets=AgentBudgets(
            max_tool_rounds=3,
            max_provider_calls=5,
            max_tool_calls_per_response=2,
            max_tool_calls_per_run=3,
        ),
    )

    assert result.terminal_reason == "tool_call_run_budget_exhausted"
    assert invocations == ["rollout", "rollout"]
    assert tuple(item.status for item in result.tool_traces) == (
        "ok",
        "ok",
        "rejected",
        "rejected",
    )


def test_tool_timeout_is_capped_by_remaining_run_wall_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    late_effects: list[str] = []

    async def slow(self: ToolRegistry, arguments: object):
        await asyncio.sleep(0.2)
        late_effects.append("completed")
        return ToolRegistry._context_data(self, "get_rollouts")

    monkeypatch.setattr(ToolRegistry, "_rollout", slow)
    started = time.perf_counter()
    result = run_governed(
        BatchedToolProvider((1,)),
        budgets=AgentBudgets(wall_clock_seconds=0.03, tool_timeout_seconds=1.0),
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 0.15
    assert result.terminal_reason == "wall_clock_budget_exhausted"
    assert result.tool_traces[0].status == "timeout"
    time.sleep(0.22)
    assert late_effects == []


def test_render_call_reservation_must_leave_evidence_capacity() -> None:
    with pytest.raises(ValueError, match="leave at least one evidence call"):
        AgentBudgets(max_provider_calls=2, reserved_provider_calls_for_render=2)


def test_final_evidence_slot_forces_direct_response_after_sequential_tools() -> None:
    provider = SequentialToolProvider()
    result = run_governed(
        provider,
        budgets=AgentBudgets(
            max_tool_rounds=2,
            max_provider_calls=4,
            reserved_provider_calls_for_render=1,
        ),
    )

    evidence_requests = [item for item in provider.requests if item.pass_kind.value == "evidence"]
    assert [item.tool_choice for item in evidence_requests] == [None, None, "NONE"]
    assert all(item.citation_mode == "ACCURATE" for item in evidence_requests)
    assert result.terminal_reason == "complete"
    assert result.response.route == "Payments Platform"


def test_provider_ignoring_final_none_tool_choice_is_rejected_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invocations: list[str] = []
    original = ToolRegistry._rollout

    def counted(self: ToolRegistry, arguments: object):
        invocations.append("rollout")
        return original(self, arguments)  # type: ignore[arg-type]

    monkeypatch.setattr(ToolRegistry, "_rollout", counted)
    result = run_governed(
        IgnoresNoToolsProvider(),
        budgets=AgentBudgets(
            max_tool_rounds=2,
            max_provider_calls=4,
            reserved_provider_calls_for_render=1,
        ),
    )

    assert result.terminal_reason == "unexpected_tool_call"
    assert invocations == ["rollout"]
    assert result.provider_traces[-1].status == "malformed"
    assert result.provider_traces[-1].safe_error_code == "unexpected_tool_call"
    assert result.tool_traces[-1].status == "rejected"
    assert result.tool_traces[-1].safe_error_code == "unexpected_tool_call"


def test_provider_timeout_is_visible_and_falls_back() -> None:
    result = run_governed(TimeoutProvider())
    assert result.terminal_reason == "provider_timeout"
    assert result.provider_traces[0].status == "timeout"
    assert result.response.status == "needs_review"


def test_observed_token_threshold_stops_after_an_over_budget_response() -> None:
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


def test_schema_valid_but_incomplete_findings_repair_fails_closed() -> None:
    result = run_governed(
        RepairingFindingsProvider(FinishReason.MAX_TOKENS),
        budgets=AgentBudgets(max_provider_calls=5, max_total_tokens=4096),
    )

    assert result.terminal_reason == "evidence_findings_invalid"
    assert result.provider_traces[-1].status == "malformed"
    assert result.response.needs_review is True


def test_structure_pass_observed_usage_overflow_stops_the_run() -> None:
    result = run_governed(
        StructureBudgetOverflowProvider(),
        budgets=AgentBudgets(max_total_tokens=512, max_output_tokens_per_call=64),
    )

    assert result.total_tokens == 608
    assert result.terminal_reason == "token_budget_exhausted"
    assert result.response.needs_review is True


def test_provider_deadline_is_propagated_without_a_background_worker() -> None:
    started = time.perf_counter()
    result = run_governed(
        DeadlineAwareTimeoutProvider(), budgets=AgentBudgets(wall_clock_seconds=0.05)
    )
    elapsed = time.perf_counter() - started

    assert result.terminal_reason == "provider_timeout"
    assert result.provider_traces[0].status == "timeout"
    assert elapsed < 0.15


def test_late_provider_response_retains_spent_usage_and_identity() -> None:
    result = run_governed(LateReturningProvider(), budgets=AgentBudgets(wall_clock_seconds=0.01))

    assert result.terminal_reason == "provider_timeout"
    assert result.total_tokens == 304
    assert result.provider_traces[0].status == "timeout"
    assert result.provider_traces[0].response_id == "high-usage"
    assert result.provider_traces[0].response_hash is not None
    assert result.provider_traces[0].usage.total_tokens == 304


def test_unbounded_live_provider_is_rejected_without_invocation() -> None:
    provider = UnboundedLiveProvider()
    result = run_governed(provider)  # type: ignore[arg-type]

    assert result.terminal_reason == "provider_timeout_unsupported"
    assert result.provider_traces[0].safe_error_code == "provider_timeout_unsupported"
    assert provider.called is False
