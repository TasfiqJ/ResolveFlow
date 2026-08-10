from __future__ import annotations

from types import SimpleNamespace

import pytest
from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.contracts import (
    ChatRequest,
    PassKind,
    ProviderTimeoutError,
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
            max_tokens=128,
            temperature=0,
            seed=17,
        )
    )
    request = client.requests[0]
    assert request["strict_tools"] is True
    assert request["documents"]
    assert request["tools"]
    assert "response_format" not in request
    parameters = request["tools"][0]["function"]["parameters"]
    assert parameters["properties"]["rollout_id"] == {"type": "string"}
    assert response.tool_calls[0].name == "query_rollout_record"
    assert response.usage.total_tokens == 15


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
    assert request["response_format"]


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
