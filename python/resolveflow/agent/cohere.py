from __future__ import annotations

import json
from typing import Any

from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderError,
    ProviderTimeoutError,
    ProviderUsage,
    ToolCallRequest,
)


class CohereChatAdapter:
    """Official Cohere V2 Chat adapter. Construction is explicit and live-off by default."""

    provider_name = "cohere"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        allow_live: bool = False,
        client: Any | None = None,
    ) -> None:
        if client is None:
            if not allow_live or not api_key:
                raise ValueError("live Cohere adapter requires allow_live=true and an API key")
            import cohere

            client = cohere.ClientV2(api_key=api_key)
        self.client = client

    def chat(self, request: ChatRequest) -> ChatResponse:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": list(request.messages),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "seed": request.seed,
        }
        if request.pass_kind is PassKind.EVIDENCE:
            kwargs["documents"] = [
                {
                    "id": document.document_id,
                    "data": {
                        "title": document.title,
                        "locator": document.locator,
                        "content": document.content,
                        "trust": "untrusted_evidence",
                    },
                }
                for document in request.documents
            ]
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in request.tools
            ]
            kwargs["strict_tools"] = request.strict_tools
        else:
            kwargs["response_format"] = {
                "type": "json_object",
                "schema": request.response_schema,
            }
        try:
            raw = self.client.chat(**kwargs)
        except (TimeoutError, ConnectionError) as exc:
            raise ProviderTimeoutError("provider_timeout") from exc
        except Exception as exc:
            raise ProviderError("provider_error") from exc
        return self._normalize(raw, request.model)

    @classmethod
    def _normalize(cls, raw: Any, model: str) -> ChatResponse:
        message = raw.message
        content = getattr(message, "content", None) or []
        text = "".join(str(getattr(item, "text", "")) for item in content)
        tool_calls = tuple(
            ToolCallRequest(
                tool_call_id=str(item.id),
                name=str(item.function.name),
                arguments_json=str(item.function.arguments),
            )
            for item in (getattr(message, "tool_calls", None) or [])
        )
        citations = tuple(
            str(getattr(item, "id", getattr(item, "document_id", "citation")))
            for item in (getattr(message, "citations", None) or [])
        )
        usage = cls._usage(getattr(raw, "usage", None))
        finish_value = getattr(raw, "finish_reason", "error")
        if hasattr(finish_value, "value"):
            finish_value = finish_value.value
        finish = str(finish_value).rsplit(".", 1)[-1].lower()
        finish_map = {
            "complete": FinishReason.COMPLETE,
            "tool_call": FinishReason.TOOL_CALL,
            "max_tokens": FinishReason.MAX_TOKENS,
            "timeout": FinishReason.TIMEOUT,
            "error": FinishReason.ERROR,
        }
        return ChatResponse(
            response_id=str(raw.id),
            model=model,
            finish_reason=finish_map.get(finish, FinishReason.ERROR),
            text=text,
            tool_calls=tool_calls,
            citation_ids=citations,
            usage=usage,
        )

    @staticmethod
    def _usage(raw: Any) -> ProviderUsage:
        if raw is None:
            return ProviderUsage(input_tokens=0, output_tokens=0)
        if hasattr(raw, "model_dump"):
            data = raw.model_dump(mode="json")
        elif isinstance(raw, dict):
            data = raw
        else:
            data = json.loads(json.dumps(raw, default=lambda value: value.__dict__))

        def find(names: tuple[str, ...]) -> int:
            stack: list[Any] = [data]
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    for key, value in current.items():
                        if key in names and isinstance(value, int):
                            return value
                        stack.append(value)
                elif isinstance(current, list):
                    stack.extend(current)
            return 0

        return ProviderUsage(
            input_tokens=find(("input_tokens", "input_token_count")),
            output_tokens=find(("output_tokens", "output_token_count")),
        )
