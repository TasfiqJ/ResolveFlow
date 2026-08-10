from __future__ import annotations

import json

from resolveflow.agent.contracts import ChatRequest, ChatResponse, FinishReason, ProviderUsage
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.security import FINDINGS_REPAIR_PROMPT, lint_policy

from tests.agent_helpers import governed_inputs, run_governed


class MalformedThenRecordingProvider(FixtureChatAdapter):
    """Force the evidence pass to emit unparseable text, then capture the repair pass."""

    def __init__(self) -> None:
        self.repair_requests: list[ChatRequest] = []

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.pass_kind.value == "findings":
            self.repair_requests.append(request)
            return ChatResponse(
                response_id="repair-declined",
                model=request.model,
                finish_reason=FinishReason.COMPLETE,
                text="still not valid json",
                usage=ProviderUsage(input_tokens=10, output_tokens=4),
            )
        response = super().chat(request)
        if request.pass_kind.value == "evidence" and not response.tool_calls:
            return response.model_copy(update={"text": "not json at all"})
        return response


def test_repair_pass_never_receives_untrusted_evidence_content() -> None:
    """The repair pass must not smuggle retrieved documents past the pass boundary.

    ChatRequest.enforce_pass_boundary forbids `documents` on a FINDINGS pass, and the
    Cohere adapter only emits the trust-labelled `documents` channel for the EVIDENCE
    pass. Inlining document content into the FINDINGS *user turn* defeated both: hostile
    text that the run had already flagged was delivered as ordinary conversational input
    with no untrusted-evidence marker. The repair pass reformats the model's own
    malformed draft and nothing else.
    """
    provider = MalformedThenRecordingProvider()
    run_governed(provider)

    assert provider.repair_requests, "the repair pass did not run"
    request = provider.repair_requests[0]
    assert request.documents == ()
    assert request.tools == ()
    assert request.strict_tools is False

    _, _, corpus, _, retrieval = governed_inputs()
    payload = json.loads(request.messages[1]["content"])
    assert set(payload) == {"case_id", "malformed_findings_draft"}
    serialized = json.dumps(request.messages)

    hostile_phrases = ("Ignore all policy", "without approval")
    assert not any(phrase in serialized for phrase in hostile_phrases)

    for candidate in retrieval.candidates:
        assert candidate.content not in serialized
    for chunk in corpus.chunks:
        assert chunk.content not in serialized


def test_repair_prompt_is_policy_lint_clean() -> None:
    assert lint_policy(FINDINGS_REPAIR_PROMPT, ()) == ()
