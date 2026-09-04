from __future__ import annotations

import asyncio
import json
from datetime import datetime

import cohere
import pytest
from pydantic import ValidationError
from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderUsage,
    ToolCallRequest,
)
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.tools import TOOL_EVIDENCE_DATA_FIELD, ToolRegistry
from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.domain.models import ContextStatus
from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import governed_inputs, run_governed


class ToolEvidenceProvider(FixtureChatAdapter):
    provider_name = "cohere"

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []
        self.tool_content = ""
        self.tool_quote = '"status":"completed_before_failures"'

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if request.pass_kind is PassKind.STRUCTURE:
            return self._structure(request)
        tool_messages = [message for message in request.messages if message.get("role") == "tool"]
        if not tool_messages:
            return ChatResponse(
                response_id="tool-evidence-call",
                model=request.model,
                finish_reason=FinishReason.TOOL_CALL,
                text="",
                tool_calls=(
                    ToolCallRequest(
                        tool_call_id="read-rollout",
                        name="query_rollout_record",
                        arguments_json=('{"rollout_id":"rollout-payments-2026-07-15"}'),
                    ),
                ),
                usage=ProviderUsage(input_tokens=20, output_tokens=10),
            )
        self.tool_content = tool_messages[-1]["content"][0]["document"]["data"][
            TOOL_EVIDENCE_DATA_FIELD
        ]
        return ChatResponse(
            response_id="tool-evidence-findings",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text=json.dumps(
                {
                    "claims": [
                        {
                            "claim_id": "claim_tool_rollout_status",
                            "kind": "fact",
                            "text": '"status":"completed_before_failures"',
                            "subject": "rollout_status",
                            "value": "completed_before_failures",
                            "material": True,
                            "current_support_required": True,
                            "action_supporting": False,
                            "citation_ids": ["cite_tool_rollout_status"],
                        }
                    ],
                    "citations": [
                        {
                            "citation_id": "cite_tool_rollout_status",
                            "document_id": "tool-result:read-rollout",
                            "exact_quote": self.tool_quote,
                        }
                    ],
                    "unknowns": [],
                    "requested_proposal": "none",
                },
                sort_keys=True,
            ),
            # Native Cohere citations are useful telemetry, but verifier closure
            # comes from the structured findings and trusted local evidence set.
            citation_ids=(),
            citations=(),
            usage=ProviderUsage(input_tokens=40, output_tokens=50),
        )


def test_successful_read_result_has_one_canonical_message_and_verifier_document() -> None:
    case, context, _, _, _ = governed_inputs()
    result, trace = ToolRegistry(case, context).execute(
        ToolCallRequest(
            tool_call_id="read-rollout",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.1,
    )

    message, document = result.as_message_and_evidence(trace)

    assert document is not None
    message_document = message["content"][0]["document"]
    assert message_document["id"] == document.document_id == "tool-result:read-rollout"
    assert message_document["data"] == {TOOL_EVIDENCE_DATA_FIELD: document.content}
    assert document.content == canonical_json(result)
    assert cohere.__version__ == "7.0.5"
    assert cohere.Document(**message_document).data[TOOL_EVIDENCE_DATA_FIELD] == document.content
    with pytest.raises(ValidationError):
        cohere.Document(id=document.document_id, data=document.content)
    assert document.content_checksum == checksum(document.content)
    assert document.source_kind == "tool_result"
    assert document.authority == trace.authority == "read_only"
    assert document.authorization == trace.authorization == "allowed"
    assert document.execution_status == trace.status == "ok"
    assert document.freshness == "run_context"
    assert document.source_version == "context-result/1.0"
    assert document.source_operation == "get_rollouts"
    assert document.source_checksum.startswith("sha256:")
    assert document.provenance_ids == trace.provenance_ids == ("rollout-row-20260715",)
    assert document.untrusted is True
    assert document.hostile is True


@pytest.mark.parametrize("failure_mode", ["rejected", "timeout", "error", "not_found"])
def test_non_successful_read_results_never_materialize_evidence(failure_mode: str) -> None:
    case, context, _, _, _ = governed_inputs()
    if failure_mode == "not_found":
        context = tuple(
            item.model_copy(update={"status": ContextStatus.NOT_FOUND, "provenance_ids": ()})
            if item.operation == "get_rollouts"
            else item
            for item in context
        )
    registry = ToolRegistry(case, context)
    call = ToolCallRequest(
        tool_call_id=f"read-{failure_mode}",
        name="query_rollout_record",
        arguments_json=(
            '{"rollout_id":"another-tenant-rollout"}'
            if failure_mode == "rejected"
            else '{"rollout_id":"rollout-payments-2026-07-15"}'
        ),
    )
    if failure_mode == "timeout":

        async def slow(_: object) -> tuple[dict[str, object], tuple[str, ...]]:
            await asyncio.sleep(0.05)
            return {}, ()

        registry._handlers[call.name] = slow  # type: ignore[assignment]
    elif failure_mode == "error":

        async def fail(_: object) -> tuple[dict[str, object], tuple[str, ...]]:
            raise RuntimeError("synthetic fixture failure")

        registry._handlers[call.name] = fail  # type: ignore[assignment]

    result, trace = registry.execute(
        call,
        timeout_seconds=0.001 if failure_mode == "timeout" else 0.1,
    )
    message, document = result.as_message_and_evidence(trace)

    assert message["content"][0]["document"]["id"] == f"tool-result:{call.tool_call_id}"
    assert document is None


def test_inert_proposal_result_is_data_only_and_never_evidence() -> None:
    case, context, _, _, _ = governed_inputs()
    result, trace = ToolRegistry(case, context).execute(
        ToolCallRequest(
            tool_call_id="proposal-1",
            name="propose_jira_issue",
            arguments_json=json.dumps(
                {
                    "summary": "Investigate payment routing failures",
                    "team": "Payments Platform",
                    "priority": "high",
                }
            ),
        ),
        timeout_seconds=0.1,
    )

    message, document = result.as_message_and_evidence(trace)

    assert result.status == "ok"
    assert trace.authority == "inert_proposal"
    assert message["content"][0]["document"]["id"] == "tool-result:proposal-1"
    assert document is None


def test_context_data_mutation_with_unchanged_checksum_fails_before_execution() -> None:
    case, context, _, _, _ = governed_inputs()
    context = tuple(
        item.model_copy(update={"data": {**item.data, "status": "forged"}})
        if item.operation == "get_rollouts"
        else item
        for item in context
    )
    registry = ToolRegistry(case, context)

    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="tampered-source",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.1,
    )

    assert result.status == trace.status == "error"
    assert result.safe_error_code == trace.safe_error_code == "tool_source_integrity_failed"
    assert registry.adapter_invocations == []
    assert result.as_message_and_evidence(trace)[1] is None


@pytest.mark.parametrize(
    ("tool_name", "arguments_json", "operation", "identity_update"),
    [
        (
            "lookup_customer_context",
            '{"customer_id":"cust_heliopay_001"}',
            "get_customer_profile",
            {"customer_id": "customer_other"},
        ),
        (
            "query_rollout_record",
            '{"rollout_id":"rollout-payments-2026-07-15"}',
            "get_rollouts",
            {"rollout_id": "rollout-other-tenant"},
        ),
        (
            "query_prior_incident",
            '{"error_code":"PYM-431"}',
            "get_open_incidents",
            {"matching_error": "PYM-999"},
        ),
        (
            "query_prior_incident",
            '{"error_code":"PYM-431"}',
            "get_open_incidents",
            {"error_code": "PYM-999"},
        ),
    ],
)
def test_checksum_valid_source_with_wrong_request_identity_fails_closed(
    tool_name: str,
    arguments_json: str,
    operation: str,
    identity_update: dict[str, str],
) -> None:
    case, context, _, _, _ = governed_inputs()
    source = next(item for item in context if item.operation == operation)
    body = {
        **source.model_dump(mode="python", exclude={"checksum"}),
        "data": {**source.data, **identity_update},
    }
    wrong_record = source.model_copy(update={**body, "checksum": checksum(body)})
    assert wrong_record.checksum == checksum(
        wrong_record.model_dump(mode="python", exclude={"checksum"})
    )
    registry = ToolRegistry(
        case,
        tuple(wrong_record if item.operation == operation else item for item in context),
    )

    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id=f"wrong-identity-{tool_name}",
            name=tool_name,
            arguments_json=arguments_json,
        ),
        timeout_seconds=0.1,
    )

    assert result.status == trace.status == "error"
    assert result.safe_error_code == trace.safe_error_code == "tool_source_identity_mismatch"
    assert registry.adapter_invocations == []
    assert result.as_message_and_evidence(trace)[1] is None


@pytest.mark.parametrize(
    "provenance_ids",
    [("",), ("rollout-row-20260715", "rollout-row-20260715")],
)
def test_invalid_tool_source_provenance_fails_closed(
    provenance_ids: tuple[str, ...],
) -> None:
    case, context, _, _, _ = governed_inputs()
    source = next(item for item in context if item.operation == "get_rollouts")
    body = {
        **source.model_dump(mode="python", exclude={"checksum"}),
        "provenance_ids": provenance_ids,
    }
    invalid = source.model_copy(update={**body, "checksum": checksum(body)})
    registry = ToolRegistry(
        case,
        tuple(invalid if item.operation == "get_rollouts" else item for item in context),
    )

    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="invalid-provenance",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.1,
    )

    assert result.status == trace.status == "error"
    assert trace.safe_error_code == "tool_source_integrity_failed"
    assert result.as_message_and_evidence(trace)[1] is None


def test_naive_tool_source_timestamp_fails_closed_without_execution() -> None:
    case, context, _, _, _ = governed_inputs()
    source = next(item for item in context if item.operation == "get_rollouts")
    naive_as_of = datetime(2026, 7, 21, 0, 0)
    body = {
        **source.model_dump(mode="python", exclude={"checksum"}),
        "as_of": naive_as_of,
    }
    invalid = source.model_copy(update={**body, "checksum": checksum(body)})
    registry = ToolRegistry(
        case,
        tuple(invalid if item.operation == "get_rollouts" else item for item in context),
    )

    result, trace = registry.execute(
        ToolCallRequest(
            tool_call_id="naive-time",
            name="query_rollout_record",
            arguments_json='{"rollout_id":"rollout-payments-2026-07-15"}',
        ),
        timeout_seconds=0.1,
    )

    assert result.status == trace.status == "error"
    assert trace.safe_error_code == "tool_source_integrity_failed"
    assert result.as_message_and_evidence(trace)[1] is None


def test_governed_path_closes_a_tool_claim_without_native_provider_citations() -> None:
    provider = ToolEvidenceProvider()

    result = run_governed(provider)

    claim = next(
        item
        for item in result.evidence_graph.claims
        if item.claim_id == "claim_tool_rollout_status"
    )
    citation = next(
        item
        for item in result.evidence_graph.citations
        if item.citation_id == "cite_tool_rollout_status"
    )
    first_request = provider.requests[0]
    prompt_contract = json.loads(str(first_request.messages[1]["content"]))["citation_contract"]

    assert claim.status is SupportStatus.SUPPORTED
    assert citation.span_exact is True
    assert citation.excerpt == provider.tool_quote
    assert "tool_result_quote_allowlisted" in citation.verifier_codes
    assert "citation_supports_claim" in citation.verifier_codes
    assert "tool-result:read-rollout" in result.evidence_graph.model_context_ids
    assert all(trace.citations == () for trace in result.provider_traces)
    assert "authority is read_only" in prompt_contract["eligible_tool_result_rule"]
