from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from queue import Queue
from threading import Thread
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from resolveflow.agent.contracts import (
    ToolCallRequest,
    ToolDefinition,
    ToolResultEvidenceDocument,
    ToolTrace,
)
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.domain.models import CanonicalCase, ContextResult

from .security import ATTACK_PATTERNS

TOOL_EVIDENCE_DATA_FIELD = "resolveflow_canonical_evidence"
TOOL_CONTEXT_OPERATIONS = {
    "lookup_customer_context": "get_customer_profile",
    "query_rollout_record": "get_rollouts",
    "query_prior_incident": "get_open_incidents",
}


def _is_timezone_aware(value: object) -> bool:
    return (
        isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    )


def _context_result_body(result: ContextResult) -> dict[str, Any]:
    return {
        "operation": result.operation,
        "status": result.status,
        "as_of": result.as_of,
        "provenance_ids": result.provenance_ids,
        "data": result.data,
    }


def _context_result_is_valid(result: ContextResult, expected_operation: str) -> bool:
    try:
        provenance_valid = result.status.value != "ok" or (
            bool(result.provenance_ids)
            and all(isinstance(item, str) and item.strip() for item in result.provenance_ids)
            and len(set(result.provenance_ids)) == len(result.provenance_ids)
        )
        return bool(
            result.operation == expected_operation
            and _is_timezone_aware(result.as_of)
            and isinstance(result.data, dict)
            and provenance_valid
            and result.checksum == checksum(_context_result_body(result))
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _context_result_matches_arguments(
    tool_name: str, arguments: FrozenModel, result: ContextResult
) -> bool:
    """Bind canonical source identities to the exact authorized tool request.

    A valid source checksum only proves that the source envelope is internally
    consistent. It does not prove that the enclosed record answers this tool
    call, so each read tool independently checks its request key here.
    """

    required_field: str
    expected_value: str
    optional_aliases: tuple[str, ...] = ()
    if tool_name == "lookup_customer_context" and isinstance(arguments, CustomerLookupArgs):
        required_field = "customer_id"
        expected_value = arguments.customer_id
    elif tool_name == "query_rollout_record" and isinstance(arguments, RolloutLookupArgs):
        required_field = "rollout_id"
        expected_value = arguments.rollout_id
    elif tool_name == "query_prior_incident" and isinstance(arguments, PriorIncidentArgs):
        required_field = "matching_error"
        expected_value = arguments.error_code
        optional_aliases = ("error_code",)
    else:
        return False

    # Non-success sources may legitimately omit the lookup key. If they carry
    # one, however, it must still identify the requested record. Successful
    # reads must always carry their canonical identity field.
    if result.status.value == "ok" and result.data.get(required_field) != expected_value:
        return False
    if required_field in result.data and result.data[required_field] != expected_value:
        return False
    return all(
        alias not in result.data or result.data[alias] == expected_value
        for alias in optional_aliases
    )


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
    authority: Literal["read_only", "inert_proposal"] | None = None
    authorization: Literal["allowed", "denied", "not_evaluated"] = "not_evaluated"
    source_status: (
        Literal["ok", "not_found", "denied", "timeout", "malformed", "unavailable"] | None
    ) = None
    freshness: Literal["run_context"] | None = None
    source_operation: str | None = None
    source_as_of: datetime | None = None
    source_version: Literal["context-result/1.0"] | None = None
    source_checksum: str | None = None
    safe_error_code: str | None = None

    @field_validator("source_as_of")
    @classmethod
    def source_timestamp_is_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and not _is_timezone_aware(value):
            raise ValueError("tool-result source timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def successful_read_has_bound_source_metadata(self) -> ToolResult:
        if self.status != "ok" or self.authority != "read_only":
            return self
        if (
            self.authorization != "allowed"
            or self.source_status is None
            or self.freshness != "run_context"
            or not self.source_operation
            or self.source_as_of is None
            or self.source_version != "context-result/1.0"
            or self.source_checksum is None
        ):
            raise ValueError("successful read result requires bound source metadata")
        if self.source_status == "ok":
            if not self.provenance_ids or any(not item.strip() for item in self.provenance_ids):
                raise ValueError("successful read result requires nonblank provenance IDs")
            if len(set(self.provenance_ids)) != len(self.provenance_ids):
                raise ValueError("successful read result requires unique provenance IDs")
        return self

    def as_message(self) -> dict[str, Any]:
        message, _ = self.as_message_and_evidence()
        return message

    def as_message_and_evidence(
        self, trace: ToolTrace | None = None
    ) -> tuple[dict[str, Any], ToolResultEvidenceDocument | None]:
        """Materialize one canonical provider message and its verifier twin.

        Only trusted successful executions of read-only tools with a current,
        provenance-bearing context result produce verifier evidence. Rejected,
        failed, timed-out, not-found, and inert-proposal outputs remain visible
        to the model as data but cannot support a claim.
        """

        content = canonical_json(self)
        document_id = f"tool-result:{self.tool_call_id}"
        message = {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": [
                {
                    "type": "document",
                    "document": {
                        "id": document_id,
                        "data": {TOOL_EVIDENCE_DATA_FIELD: content},
                    },
                }
            ],
        }
        source_data = self.data.get("data")
        source_binding_valid = bool(
            self.source_operation
            and self.source_status
            and _is_timezone_aware(self.source_as_of)
            and isinstance(source_data, dict)
            and set(self.data) == {"status", "data"}
            and self.data.get("status") == self.source_status
            and self.source_checksum
            == checksum(
                {
                    "operation": self.source_operation,
                    "status": self.source_status,
                    "as_of": self.source_as_of,
                    "provenance_ids": self.provenance_ids,
                    "data": source_data,
                }
            )
        )
        provenance_valid = bool(
            self.provenance_ids
            and all(item.strip() for item in self.provenance_ids)
            and len(set(self.provenance_ids)) == len(self.provenance_ids)
        )
        hostile_output = any(pattern.search(content) for _, pattern in ATTACK_PATTERNS)
        evidence: ToolResultEvidenceDocument | None = None
        if (
            trace is not None
            and trace.tool_call_id == self.tool_call_id
            and trace.name == self.name
            and trace.status == self.status == "ok"
            and trace.authorization == self.authorization == "allowed"
            and trace.authority == self.authority == "read_only"
            and trace.provenance_ids == self.provenance_ids
            and trace.source_status == self.source_status == "ok"
            and trace.freshness == self.freshness == "run_context"
            and trace.source_operation == self.source_operation
            and trace.source_as_of == self.source_as_of
            and trace.source_version == self.source_version == "context-result/1.0"
            and trace.source_checksum == self.source_checksum
            and self.source_as_of is not None
            and self.source_operation == TOOL_CONTEXT_OPERATIONS.get(self.name)
            and self.source_version == "context-result/1.0"
            and self.source_checksum is not None
            and source_binding_valid
            and provenance_valid
            and not hostile_output
        ):
            evidence = ToolResultEvidenceDocument(
                document_id=document_id,
                tool_call_id=self.tool_call_id,
                tool_name=self.name,
                title=f"Read-only tool result: {self.name}",
                locator=f"tool call {self.tool_call_id}",
                content=content,
                content_checksum=checksum(content),
                source_operation=self.source_operation,
                source_as_of=self.source_as_of,
                source_checksum=self.source_checksum,
                provenance_ids=self.provenance_ids,
            )
        return message, evidence


Handler = Callable[[FrozenModel], Awaitable[tuple[dict[str, Any], tuple[str, ...]]]]


async def _run_handler(
    handler: Handler, arguments: FrozenModel, timeout_seconds: float
) -> tuple[dict[str, Any], tuple[str, ...]]:
    return await asyncio.wait_for(handler(arguments), timeout=timeout_seconds)


def _run_handler_sync(
    handler: Handler, arguments: FrozenModel, timeout_seconds: float
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Run one cooperative handler from sync or already-async callers.

    ``GovernedAgent`` is deliberately synchronous. If it is called on a thread
    that already owns an event loop, Python forbids nesting ``asyncio.run``. A
    short-lived joined bridge thread owns the handler loop in that case. It is
    never detached: cancellation completes and the thread is joined before a
    tool result can be returned, so no handler survives a reported timeout.
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run_handler(handler, arguments, timeout_seconds))

    outcome: Queue[tuple[tuple[dict[str, Any], tuple[str, ...]] | None, BaseException | None]] = (
        Queue(maxsize=1)
    )

    def run() -> None:
        try:
            outcome.put((asyncio.run(_run_handler(handler, arguments, timeout_seconds)), None))
        except BaseException as exc:  # propagated on the calling thread below
            outcome.put((None, exc))

    bridge = Thread(target=run, name="resolveflow-tool-loop", daemon=False)
    bridge.start()
    bridge.join()
    result, error = outcome.get_nowait()
    if error is not None:
        raise error
    assert result is not None
    return result


class ToolRegistry:
    """Fixed, typed tool registry. No registered handler performs an external write."""

    def __init__(self, case: CanonicalCase, context: tuple[ContextResult, ...]) -> None:
        self.case = case
        self._context_counts = {
            operation: sum(item.operation == operation for item in context)
            for operation in {item.operation for item in context}
        }
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
        self._authorities: dict[str, Literal["read_only", "inert_proposal"]] = {
            "lookup_customer_context": "read_only",
            "query_rollout_record": "read_only",
            "query_prior_incident": "read_only",
            "propose_jira_issue": "inert_proposal",
        }
        self._context_operations = TOOL_CONTEXT_OPERATIONS

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
        return tuple(
            ToolDefinition(
                name=name,
                description=descriptions[name],
                parameters=model.model_json_schema(),
                authority=self._authorities[name],
            )
            for name, model in self._models.items()
        )

    def execute(
        self, call: ToolCallRequest, *, timeout_seconds: float
    ) -> tuple[ToolResult, ToolTrace]:
        started = time.perf_counter_ns()
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

        expected_operation = self._context_operations.get(call.name)
        source = self.context.get(expected_operation or "")
        if expected_operation is not None and (
            source is None
            or self._context_counts.get(expected_operation) != 1
            or not _context_result_is_valid(source, expected_operation)
        ):
            return self._source_error(call, arguments_hash, started, "tool_source_integrity_failed")
        if source is not None and not _context_result_matches_arguments(
            call.name, arguments, source
        ):
            return self._source_error(
                call, arguments_hash, started, "tool_source_identity_mismatch"
            )

        handler = self._handlers[call.name]
        try:
            data, provenance_ids = _run_handler_sync(handler, arguments, timeout_seconds)
        except TimeoutError:
            result = ToolResult(
                tool_call_id=call.tool_call_id,
                name=call.name,
                status="timeout",
                data={},
                provenance_ids=(),
                authority=self._authorities[call.name],
                authorization="allowed",
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
                authority=self._authorities[call.name],
                authorization="allowed",
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
        self.adapter_invocations.append(call.name)
        authority = self._authorities[call.name]
        if source is not None and (
            data != {"status": source.status.value, "data": source.data}
            or provenance_ids != source.provenance_ids
        ):
            return self._source_error(call, arguments_hash, started, "tool_source_binding_failed")
        result = ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status="ok",
            data=data,
            provenance_ids=provenance_ids,
            authority=authority,
            authorization="allowed",
            source_status=source.status.value if source is not None else None,
            freshness="run_context" if source is not None else None,
            source_operation=source.operation if source is not None else None,
            source_as_of=source.as_of if source is not None else None,
            source_version="context-result/1.0" if source is not None else None,
            source_checksum=source.checksum if source is not None else None,
        )
        return result, self._trace(
            call,
            "ok",
            "allowed",
            arguments_hash,
            started,
            provenance_ids,
            None,
            source=source,
        )

    def reject_without_execution(
        self, call: ToolCallRequest, *, code: str
    ) -> tuple[ToolResult, ToolTrace]:
        """Return an auditable budget rejection without authorizing or running a handler."""

        started = time.perf_counter_ns()
        return self._rejected(
            call,
            checksum(call.arguments_json),
            started,
            code,
            "not_evaluated",
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

    async def _customer(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_customer_profile")

    async def _rollout(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_rollouts")

    async def _incident(self, _: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
        return self._context_data("get_open_incidents")

    @staticmethod
    async def _proposal(arguments: FrozenModel) -> tuple[dict[str, Any], tuple[str, ...]]:
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
            authority=self._authorities.get(call.name),
            authorization=authorization,
            safe_error_code=code,
        )
        return result, self._trace(
            call, "rejected", authorization, arguments_hash, started, (), code
        )

    def _source_error(
        self,
        call: ToolCallRequest,
        arguments_hash: str,
        started: float,
        code: str,
    ) -> tuple[ToolResult, ToolTrace]:
        result = ToolResult(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status="error",
            data={},
            provenance_ids=(),
            authority=self._authorities.get(call.name),
            authorization="allowed",
            safe_error_code=code,
        )
        return result, self._trace(
            call,
            "error",
            "allowed",
            arguments_hash,
            started,
            (),
            code,
        )

    def _trace(
        self,
        call: ToolCallRequest,
        status: Literal["ok", "rejected", "timeout", "error"],
        authorization: Literal["allowed", "denied", "not_evaluated"],
        arguments_hash: str,
        started: float,
        provenance_ids: tuple[str, ...],
        safe_error_code: str | None,
        *,
        source: ContextResult | None = None,
    ) -> ToolTrace:
        return ToolTrace(
            tool_call_id=call.tool_call_id,
            name=call.name,
            status=status,
            authorization=authorization,
            authority=self._authorities.get(call.name),
            source_status=source.status.value if source is not None else None,
            freshness="run_context" if source is not None else None,
            source_operation=source.operation if source is not None else None,
            source_as_of=source.as_of if source is not None else None,
            source_version="context-result/1.0" if source is not None else None,
            source_checksum=source.checksum if source is not None else None,
            arguments_hash=arguments_hash,
            duration_ms=max(0.0, round((time.perf_counter_ns() - started) / 1_000_000.0, 6)),
            provenance_ids=provenance_ids,
            safe_error_code=safe_error_code,
        )
