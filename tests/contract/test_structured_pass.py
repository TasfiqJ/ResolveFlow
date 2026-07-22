from __future__ import annotations

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


def test_second_pass_has_no_tools_no_documents() -> None:
    provider = MalformedStructureProvider()
    run_governed(provider)
    request = next(item for item in provider.requests if item.pass_kind is PassKind.STRUCTURE)
    assert request.tools == ()
    assert request.documents == ()
    assert request.response_schema is not None


def test_invalid_output_uses_minimal_verified_fallback() -> None:
    provider = MalformedStructureProvider()
    result = run_governed(provider)
    assert result.terminal_reason == "structured_response_invalid"
    assert result.response.needs_review is True
    assert result.response.route is None
    assert result.response.verified_facts == ("The issuer-routing-v3 rollout completed.",)
    assert all(item.status != "ok" for item in result.provider_traces[-1:])
