from __future__ import annotations

import json

from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderUsage,
)
from resolveflow.agent.fixture import FixtureChatAdapter

from tests.agent_helpers import run_governed


class MalformedStructureProvider:
    provider_name = "recorded_fixture"

    def __init__(self) -> None:
        self.fixture = FixtureChatAdapter()
        self.requests: list[ChatRequest] = []

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        return self.chat(request)

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if request.pass_kind is PassKind.STRUCTURE:
            return ChatResponse(
                response_id="malformed-structure",
                model=request.model,
                finish_reason=FinishReason.COMPLETE,
                text='{"route_claim_id":"unsupported-injected-fact"}',
                usage=ProviderUsage(input_tokens=10, output_tokens=5),
            )
        return self.fixture.chat(request)


class IncompleteStructureProvider(MalformedStructureProvider):
    def chat(self, request: ChatRequest) -> ChatResponse:
        response = super().chat(request)
        if request.pass_kind is PassKind.STRUCTURE:
            fixture_response = self.fixture.chat(request)
            return fixture_response.model_copy(update={"finish_reason": FinishReason.MAX_TOKENS})
        return response


def test_second_pass_has_no_tools_no_documents() -> None:
    provider = MalformedStructureProvider()
    run_governed(provider)
    request = next(item for item in provider.requests if item.pass_kind is PassKind.STRUCTURE)
    assert request.tools == ()
    assert request.documents == ()
    assert request.response_schema is not None


def test_second_pass_schema_is_bound_to_the_verified_graph() -> None:
    provider = MalformedStructureProvider()
    run_governed(provider)
    request = next(item for item in provider.requests if item.pass_kind is PassKind.STRUCTURE)
    payload = json.loads(str(request.messages[1]["content"]))
    allowed = payload["allowed_selection_ids"]
    properties = request.response_schema["properties"]

    assert properties["schema_version"] == {"type": "string", "const": "1.0"}
    assert properties["graph_hash"] == {
        "type": "string",
        "const": payload["verified_graph"]["graph_hash"],
    }
    assert properties["route_claim_id"]["anyOf"] == [
        {"type": "string", "enum": allowed["route_claim_ids"]},
        {"type": "null"},
    ]
    for field_name in (
        "summary_claim_ids",
        "recommended_step_claim_ids",
        "unknown_ids",
        "conflict_ids",
    ):
        allowed_ids = allowed[field_name]
        expected = (
            {"type": "array", "items": {"type": "string", "enum": allowed_ids}}
            if allowed_ids
            else {"type": "array", "items": {"type": "string"}}
        )
        assert properties[field_name] == expected


def test_invalid_output_uses_minimal_verified_fallback() -> None:
    provider = MalformedStructureProvider()
    result = run_governed(provider)
    assert result.terminal_reason == "structured_response_invalid"
    assert result.response.needs_review is True
    assert result.response.route is None
    assert result.response.verified_facts == ("The issuer-routing-v3 rollout completed.",)
    assert all(item.status != "ok" for item in result.provider_traces[-1:])


def test_schema_valid_but_incomplete_structure_output_fails_closed() -> None:
    result = run_governed(IncompleteStructureProvider())

    assert result.terminal_reason == "structured_response_invalid"
    assert result.response.needs_review is True
    assert result.provider_traces[-1].status == "malformed"
