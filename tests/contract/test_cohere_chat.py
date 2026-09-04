from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderError,
    ProviderTimeoutError,
    ToolCallRequest,
    ToolDefinition,
    UntrustedEvidenceDocument,
)
from resolveflow.agent.renderer import StructureSelection


class RecordingClient:
    def __init__(self, response: object | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.requests: list[dict[str, object]] = []

    def chat(self, **kwargs: object) -> object:
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response


def _raw_response() -> SimpleNamespace:
    return SimpleNamespace(
        id="cohere-fixture-response",
        finish_reason="TOOL_CALL",
        message=SimpleNamespace(
            content=[],
            tool_calls=[
                SimpleNamespace(
                    id="call-1",
                    function=SimpleNamespace(
                        name="query_rollout_record", arguments='{"rollout_id":"r1"}'
                    ),
                )
            ],
            citations=[],
        ),
        usage={"tokens": {"input_tokens": 10, "output_tokens": 5}},
    )


def test_evidence_pass_maps_v2_tools_documents_and_strict_tools() -> None:
    client = RecordingClient(_raw_response())
    adapter = CohereChatAdapter(client=client)
    response = adapter.chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            documents=(
                UntrustedEvidenceDocument(
                    document_id="chunk-1",
                    artifact_id="artifact-1",
                    artifact_version_id="artifact-1-v1",
                    title="Synthetic evidence",
                    version="1",
                    locator="section 1",
                    content="untrusted content",
                    content_checksum="sha256:test",
                ),
            ),
            tools=(
                ToolDefinition(
                    name="query_rollout_record",
                    description="Read one rollout.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "rollout_id": {
                                "type": "string",
                                "minLength": 1,
                                "pattern": r"^[a-z0-9-]+$",
                            }
                        },
                        "required": ["rollout_id"],
                    },
                    authority="read_only",
                ),
            ),
            strict_tools=True,
            tool_choice="NONE",
            citation_mode="ACCURATE",
            max_tokens=128,
            temperature=0,
            seed=17,
        )
    )
    request = client.requests[0]
    assert request["strict_tools"] is True
    assert request["tool_choice"] == "NONE"
    assert request["citation_options"] == {"mode": "ACCURATE"}
    assert request["documents"]
    assert request["tools"]
    assert "response_format" not in request
    parameters = request["tools"][0]["function"]["parameters"]
    assert parameters["properties"]["rollout_id"] == {"type": "string"}
    assert response.tool_calls[0].name == "query_rollout_record"
    assert response.usage.total_tokens == 15


def test_bounded_chat_uses_native_timeout_and_disables_hidden_retries() -> None:
    client = RecordingClient(_raw_response())
    adapter = CohereChatAdapter(client=client)

    adapter.chat_with_timeout(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        ),
        timeout_seconds=3.9,
    )

    assert client.requests[0]["request_options"] == {
        "timeout_in_seconds": 3,
        "max_retries": 0,
    }


def test_subsecond_provider_budget_fails_before_network_dispatch() -> None:
    client = RecordingClient(_raw_response())
    adapter = CohereChatAdapter(client=client)

    with pytest.raises(ProviderTimeoutError, match="provider_timeout"):
        adapter.chat_with_timeout(
            ChatRequest(
                pass_kind=PassKind.EVIDENCE,
                model="command-a-plus-05-2026",
                messages=({"role": "user", "content": "fixture"},),
                max_tokens=64,
                temperature=0,
                seed=17,
            ),
            timeout_seconds=0.9,
        )

    assert client.requests == []


def test_native_citation_spans_and_nested_source_ids_are_preserved() -> None:
    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="The rollout completed.")],
        tool_calls=[],
        citations=[
            SimpleNamespace(
                start=4,
                end=21,
                text="rollout completed",
                content_index=0,
                type="TEXT_CONTENT",
                sources=[
                    SimpleNamespace(id="chunk-1", type="document"),
                    SimpleNamespace(id="tool-result:call-1", type="tool"),
                ],
            )
        ],
    )

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            tools=(
                ToolDefinition(
                    name="query_rollout_record",
                    description="Read one rollout.",
                    parameters={"type": "object", "properties": {}},
                    authority="read_only",
                ),
            ),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.citation_ids == ("chunk-1", "tool-result:call-1")
    assert response.citations[0].start == 4
    assert response.citations[0].end == 21
    assert response.citations[0].content_index == 0
    assert response.citations[0].citation_type == "TEXT_CONTENT"
    assert response.citations[0].text == "rollout completed"
    assert tuple(source.source_type for source in response.citations[0].sources) == (
        "document",
        "tool",
    )


def test_single_text_block_sdk_citation_may_omit_optional_index_and_type() -> None:
    from cohere.types import Citation, DocumentSource

    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello world")],
        tool_calls=[],
        citations=[Citation(start=0, end=5, text="hello", sources=[DocumentSource(id="doc-1")])],
    )

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.citation_ids == ("doc-1",)
    assert response.citations[0].content_index == 0
    assert response.citations[0].citation_type == "TEXT_CONTENT"


def test_citation_omissions_are_rejected_when_a_hidden_block_is_present() -> None:
    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", text="private reasoning"),
            SimpleNamespace(type="text", text="hello world"),
        ],
        tool_calls=[],
        citations=[
            SimpleNamespace(
                start=0,
                end=5,
                text="hello",
                sources=[SimpleNamespace(id="doc-1", type="document")],
            )
        ],
    )

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.citation_ids == ()
    assert response.citations == ()


def test_misaligned_native_citation_span_is_not_recorded_as_valid() -> None:
    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="The rollout completed.")],
        tool_calls=[],
        citations=[
            SimpleNamespace(
                start=0,
                end=3,
                text="rollout",
                content_index=0,
                type="TEXT_CONTENT",
                sources=[SimpleNamespace(id="chunk-1", type="document")],
            )
        ],
    )

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            tools=(
                ToolDefinition(
                    name="query_rollout_record",
                    description="Read one rollout.",
                    parameters={"type": "object", "properties": {}},
                    authority="read_only",
                ),
            ),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.citation_ids == ()
    assert response.citations == ()


def test_native_citation_span_is_bound_to_its_indexed_text_block() -> None:
    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="Prefix rollout "),
            SimpleNamespace(type="text", text="completed safely"),
            SimpleNamespace(type="thinking", text="private reasoning"),
        ],
        tool_calls=[],
        citations=[
            SimpleNamespace(
                start=0,
                end=9,
                text="completed",
                content_index=1,
                type="TEXT_CONTENT",
                sources=[SimpleNamespace(id="chunk-valid", type="document")],
            ),
            SimpleNamespace(
                start=0,
                end=6,
                text="Prefix",
                content_index=9,
                type="TEXT_CONTENT",
                sources=[SimpleNamespace(id="chunk-out-of-range", type="document")],
            ),
            SimpleNamespace(
                start=0,
                end=7,
                text="private",
                content_index=2,
                type="THINKING_CONTENT",
                sources=[SimpleNamespace(id="chunk-non-text", type="document")],
            ),
            SimpleNamespace(
                start=0,
                end=6,
                text="Prefix",
                content_index=0,
                type="THINKING_CONTENT",
                sources=[SimpleNamespace(id="chunk-type-mismatch", type="document")],
            ),
        ],
    )

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.text == "Prefix rollout completed safely"
    assert response.citation_ids == ("chunk-valid",)
    assert tuple(item.text for item in response.citations) == ("completed",)
    assert response.citations[0].content_index == 1


def test_malformed_optional_response_shape_is_normalized_to_safe_provider_error() -> None:
    raw = _raw_response()
    raw.message.tool_calls = [SimpleNamespace(id="missing-function")]

    with pytest.raises(ProviderError, match="provider_error"):
        CohereChatAdapter(client=RecordingClient(raw)).chat(
            ChatRequest(
                pass_kind=PassKind.EVIDENCE,
                model="command-a-plus-05-2026",
                messages=({"role": "user", "content": "fixture"},),
                max_tokens=64,
                temperature=0,
                seed=17,
            )
        )


@pytest.mark.parametrize("field", ["tool_call_id", "name"])
def test_tool_call_identifiers_must_be_nonblank(field: str) -> None:
    values = {
        "tool_call_id": "call-1",
        "name": "query_rollout_record",
        "arguments_json": "{}",
    }
    values[field] = "   "

    with pytest.raises(ValidationError, match="must be nonblank"):
        ToolCallRequest(**values)


def test_provider_response_rejects_duplicate_tool_call_ids() -> None:
    call = ToolCallRequest(
        tool_call_id="call-1",
        name="query_rollout_record",
        arguments_json="{}",
    )

    with pytest.raises(ValidationError, match="duplicate tool-call IDs"):
        ChatResponse(
            response_id="duplicate-calls",
            model="command-a-plus-05-2026",
            finish_reason=FinishReason.TOOL_CALL,
            text="",
            tool_calls=(call, call),
            usage={"input_tokens": 1, "output_tokens": 1},
        )


def test_structure_pass_sends_schema_but_no_tools_or_documents() -> None:
    raw = _raw_response()
    raw.finish_reason = "COMPLETE"
    raw.message = SimpleNamespace(
        content=[SimpleNamespace(text='{"disposition":"needs_review"}')],
        tool_calls=[],
        citations=[],
    )
    client = RecordingClient(raw)
    CohereChatAdapter(client=client).chat(
        ChatRequest(
            pass_kind=PassKind.STRUCTURE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "verified graph only"},),
            response_schema=StructureSelection.model_json_schema(),
            max_tokens=128,
            temperature=0,
            seed=17,
        )
    )
    request = client.requests[0]
    assert "tools" not in request
    assert "documents" not in request
    assert "tool_choice" not in request
    assert "citation_options" not in request
    assert request["response_format"] == {
        "type": "json_object",
        "json_schema": CohereChatAdapter._strict_schema(StructureSelection.model_json_schema()),
    }


def test_usage_accepts_live_sdk_float_counts_and_prefers_total_tokens() -> None:
    raw = _raw_response()
    raw.usage = {
        "billed_units": {"input_tokens": 5.0, "output_tokens": 2.0},
        "tokens": {"input_tokens": 30.0, "output_tokens": 8.0, "reasoning_tokens": 6},
    }

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.usage.input_tokens == 30
    assert response.usage.output_tokens == 8


def test_usage_never_mixes_a_partial_tokens_block_with_billed_units() -> None:
    raw = _raw_response()
    raw.usage = {
        "tokens": {"input_tokens": 100},
        "billed_units": {"input_tokens": 10, "output_tokens": 20},
    }

    response = CohereChatAdapter(client=RecordingClient(raw)).chat(
        ChatRequest(
            pass_kind=PassKind.EVIDENCE,
            model="command-a-plus-05-2026",
            messages=({"role": "user", "content": "fixture"},),
            max_tokens=64,
            temperature=0,
            seed=17,
        )
    )

    assert response.usage.input_tokens == 10
    assert response.usage.output_tokens == 20


@pytest.mark.parametrize(
    "tokens",
    [
        {"input_tokens": -1.0, "output_tokens": 2.0},
        {"input_tokens": 1.5, "output_tokens": 2.0},
        {"input_tokens": float("inf"), "output_tokens": 2.0},
    ],
)
def test_usage_rejects_non_exact_token_counts(tokens: dict[str, float]) -> None:
    raw = _raw_response()
    raw.usage = {"tokens": tokens}

    with pytest.raises(ProviderError, match="provider_error"):
        CohereChatAdapter(client=RecordingClient(raw)).chat(
            ChatRequest(
                pass_kind=PassKind.EVIDENCE,
                model="command-a-plus-05-2026",
                messages=({"role": "user", "content": "fixture"},),
                max_tokens=64,
                temperature=0,
                seed=17,
            )
        )


def test_timeout_is_normalized_without_live_provider() -> None:
    adapter = CohereChatAdapter(client=RecordingClient(error=TimeoutError()))
    with pytest.raises(ProviderTimeoutError, match="provider_timeout"):
        adapter.chat(
            ChatRequest(
                pass_kind=PassKind.STRUCTURE,
                model="command-a-plus-05-2026",
                messages=({"role": "user", "content": "graph"},),
                response_schema=StructureSelection.model_json_schema(),
                max_tokens=64,
                temperature=0,
                seed=17,
            )
        )
