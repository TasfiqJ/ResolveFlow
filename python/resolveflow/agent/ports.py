from __future__ import annotations

from typing import Protocol

from resolveflow.agent.contracts import ChatRequest, ChatResponse


class ChatProviderPort(Protocol):
    provider_name: str

    def chat(self, request: ChatRequest) -> ChatResponse: ...
