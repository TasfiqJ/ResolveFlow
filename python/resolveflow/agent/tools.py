from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Literal

from pydantic import Field, ValidationError

from resolveflow.agent.contracts import ToolCallRequest, ToolDefinition, ToolTrace
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import CanonicalCase, ContextResult


class CustomerLookupArgs(FrozenModel):
    customer_id: str = Field(min_length=1, max_length=80)


class RolloutLookupArgs(FrozenModel):
    rollout_id: str = Field(min_length=1, max_length=100)


class PriorIncidentArgs(FrozenModel):
    error_code: str = Field(pattern=r"^[A-Z]{3}-[0-9]{3}$")


class JiraProposalArgs(FrozenModel):
    summary: str = Field(min_length=8, max_length=160)
    team: Literal["Payments Platform"]
    priority: Literal["high"]


class ToolResult(FrozenModel):
    tool_call_id: str
    name: str
    status: Literal["ok", "rejected", "timeout", "error"]
    data: dict[str, Any]
    provenance_ids: tuple[str, ...]
    safe_error_code: str | None = None

    def as_message(self) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": [
                {
                    "type": "document",
                    "document": {
                        "id": f"tool-result:{self.tool_call_id}",
                        "data": json.dumps(self.model_dump(mode="json"), sort_keys=True),
                    },
                }
            ],
        }


Handler = Callable[[FrozenModel], tuple[dict[str, Any], tuple[str, ...]]]


class ToolRegistry:
    """Fixed, typed tool registry. No registered handler performs an external write."""

    def __init__(self, case: CanonicalCase, context: tuple[ContextResult, ...]) -> None:
        self.case = case
        self.context = {item.operation: item for item in context}
        self.adapter_invocations: list[str] = []
        self._models: dict[str, type[FrozenModel]] = {
            "lookup_customer_context": CustomerLookupArgs,
            "query_rollout_record": RolloutLookupArgs,
            "query_prior_incident": PriorIncidentArgs,
            "propose_jira_issue": JiraProposalArgs,
        }
        self._handlers: dict[str, Handler] = {
            "lookup_customer_context": self._customer,
            "query_rollout_record": self._rollout,
            "query_prior_incident": self._incident,
            "propose_jira_issue": self._proposal,
        }

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        descriptions = {
            "lookup_customer_context": (
                "Read the current synthetic customer profile by customer ID."
            ),
            "query_rollout_record": "Read one tenant-scoped rollout record by rollout ID.",
            "query_prior_incident": "Read one prior incident record by exact error code.",
            "propose_jira_issue": (
                "Prepare an inert create-issue proposal for later human review; this never sends "
                "or approves an issue."
            ),
        }
        authority: dict[str, Literal["read_only", "inert_proposal"]] = {
            "lookup_customer_context": "read_only",
            "query_rollout_record": "read_only",
            "query_prior_incident": "read_only",
            "propose_jira_issue": "inert_proposal",
        }
        return tuple(
            ToolDefinition(
                name=name,
                description=descriptions[name],
                parameters=model.model_json_schema(),
                authority=authority[name],
            )
            for name, model in self._models.items()
        )

    def execute(
        self, call: ToolCallRequest, *, timeout_seconds: float
    ) -> tuple[ToolResult, ToolTrace]:
        started = time.monotonic()
        arguments_hash = checksum(call.arguments_json)
        model = self._models.get(call.name)
        if model is None:
            return self._rejected(
                call, arguments_hash, started, "tool_not_allowlisted", "not_evaluated"
            )
        try:
            raw = json.loads(call.arguments_json)
            arguments = model.model_validate(raw)
        except (json.JSONDecodeError, ValidationError, TypeError):
            return self._rejected(
                call, arguments_hash, started, "tool_arguments_invalid", "not_evaluated"
            )
        if not self._authorized(call.name, arguments):
            return self._rejected(
                call, arguments_hash, started, "tool_authorization_denied", "denied"
            )

        handler = self._handlers[call.name]
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="resolveflow-tool")
        future = executor.submit(handler, arguments)
        try:
            data, provenance_ids = future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            future.cancel()
            result = ToolResult(
                tool_call_id=call.tool_call_id,
                name=call.name,
                status="timeout",
                data={},
                provenance_ids=(),
                safe_error_code="tool_timeout",
            )
            trace = self._trace(
                call, "timeout", "allowed", arguments_hash, started, (), "tool_timeout"
            )
            return result, trace
        except Exception:
            result = ToolResult(
                tool_call_id=call.tool_call_id,
                name=call.name,
                status="error",
                data={},
                provenance_ids=(),
                safe_error_code="tool_execution_failed",
            )
            trace = self._trace(
                call,
                "error",
                "allowed",
                arguments_hash,
                started,
                (),
                "tool_execution_failed",
            )
            return result, trace
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        self.adapter_invocations.append(call.name)
        result = ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status="ok",
            data=data,
            provenance_ids=provenance_ids,
        )
        return result, self._trace(
            call, "ok", "allowed", arguments_hash, started, provenance_ids, None
        )

    def _authorized(self, name: str, arguments: FrozenModel) -> bool:
        if name == "lookup_customer_context":
            return (
                isinstance(arguments, CustomerLookupArgs)
                and arguments.customer_id == self.case.customer_id
            )
        if name == "query_rollout_record":
            return (
                isinstance(arguments, RolloutLookupArgs)
                and arguments.rollout_id == "rollout-payments-2026-07-15"
            )
        if name == "query_prior_incident":
            return (
                isinstance(arguments, PriorIncidentArgs)
                and arguments.error_code == self.case.error_code
            )
        if name == "propose_jira_issue":
            return isinstance(arguments, JiraProposalArgs) and arguments.team == "Payments Platform"
        return False

    def _customer(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_customer_profile")

    def _rollout(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_rollouts")

    def _incident(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_open_incidents")

    @staticmethod
    def _proposal(arguments: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        assert isinstance(arguments, JiraProposalArgs)
        return (
            {
                "state": "pending_approval",
                "connector": "not_invoked",
                "payload": arguments.model_dump(mode="json"),
            },
            ("policy:inert-proposal-only",),
        )

    def _context_data(self, operation: str) -> tuple[dict[str, Any], tuple[str, ...]]:
        result = self.context[operation]
        return (
            {"status": result.status.value, "data": result.data},
            result.provenance_ids,
        )

    def _rejected(
        self,
        call: ToolCallRequest,
        arguments_hash: str,
        started: float,
        code: str,
        authorization: Literal["denied", "not_evaluated"],
    ) -> tuple[ToolResult, ToolTrace]:
        result = ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status="rejected",
            data={},
            provenance_ids=(),
            safe_error_code=code,
        )
        return result, self._trace(
            call, "rejected", authorization, arguments_hash, started, (), code
        )

    @staticmethod
    def _trace(
        call: ToolCallRequest,
        status: Literal["ok", "rejected", "timeout", "error"],
        authorization: Literal["allowed", "denied", "not_evaluated"],
        arguments_hash: str,
        started: float,
        provenance_ids: tuple[str, ...],
        safe_error_code: str | None,
    ) -> ToolTrace:
        return ToolTrace(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=status,
            authorization=authorization,
            arguments_hash=arguments_hash,
            duration_ms=max(0, int((time.monotonic() - started) * 1000)),
            provenance_ids=provenance_ids,
            safe_error_code=safe_error_code,
        )
