from __future__ import annotations

import json
import math
from typing import Any

from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderCitation,
    ProviderCitationSource,
    ProviderError,
    ProviderTimeoutError,
    ProviderUsage,
    ToolCallRequest,
)


class CohereChatAdapter:
    """Official Cohere V2 Chat adapter. Construction is explicit and live-off by default."""

    provider_name = "cohere"
    _unsupported_strict_schema_keys = frozenset(
        {
            "allOf",
            "exclusiveMaximum",
            "exclusiveMinimum",
            "maximum",
            "maxItems",
            "maxLength",
            "minimum",
            "minItems",
            "minLength",
            "not",
            "oneOf",
            "pattern",
            "uniqueItems",
        }
    )

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

    def chat_with_timeout(self, request: ChatRequest, *, timeout_seconds: float) -> ChatResponse:
        # SDK 7's RequestOptions contract uses whole seconds. Floor rather than
        # ceil so the network timeout can never exceed the remaining run budget.
        provider_timeout_seconds = int(timeout_seconds)
        if provider_timeout_seconds <= 0:
            raise ProviderTimeoutError("provider_timeout")
        return self.chat(request, timeout_seconds=provider_timeout_seconds)

    def chat(self, request: ChatRequest, *, timeout_seconds: float | None = None) -> ChatResponse:
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
                        "parameters": self._strict_schema(tool.parameters),
                    },
                }
                for tool in request.tools
            ]
            kwargs["strict_tools"] = request.strict_tools
            if request.tool_choice is not None:
                kwargs["tool_choice"] = request.tool_choice
            if request.citation_mode is not None:
                kwargs["citation_options"] = {"mode": request.citation_mode}
        else:
            kwargs["response_format"] = {
                "type": "json_object",
                "json_schema": self._strict_schema(request.response_schema),
            }
        if timeout_seconds is not None:
            # The SDK forwards this per-request option to httpx. Disabling hidden
            # SDK retries keeps each orchestrator call equal to one budgeted call.
            kwargs["request_options"] = {
                "timeout_in_seconds": int(timeout_seconds),
                "max_retries": 0,
            }
        try:
            raw = self.client.chat(**kwargs)
            return self._normalize(raw, request.model)
        except (TimeoutError, ConnectionError) as exc:
            raise ProviderTimeoutError("provider_timeout") from exc
        except Exception as exc:  # noqa: BLE001
            # A budget-cap signal is control flow, not a provider error. Let it
            # propagate so the harness can stop cleanly at a repetition boundary
            # instead of mislabelling an exhausted budget as a model failure.
            if type(exc).__name__ == "BudgetExceeded":
                raise
            if "timeout" in type(exc).__name__.lower():
                raise ProviderTimeoutError("provider_timeout") from exc
            raise ProviderError("provider_error") from exc

    # Objects whose keys are caller-chosen NAMES rather than JSON Schema keywords.
    # Dropping a key here would delete a real field (e.g. a property literally named
    # "pattern") while leaving it listed in "required", producing an invalid schema.
    _schema_name_maps = frozenset({"properties", "patternProperties", "$defs", "definitions"})

    @classmethod
    def _strict_schema(cls, value: Any, *, is_name_map: bool = False) -> Any:
        """Project Pydantic schemas onto Cohere's supported strict-output subset."""
        if isinstance(value, dict):
            if is_name_map:
                return {key: cls._strict_schema(item) for key, item in value.items()}
            return {
                key: cls._strict_schema(item, is_name_map=key in cls._schema_name_maps)
                for key, item in value.items()
                if key not in cls._unsupported_strict_schema_keys
            }
        if isinstance(value, list):
            return [cls._strict_schema(item) for item in value]
        return value

    @classmethod
    def _normalize(cls, raw: Any, model: str) -> ChatResponse:
        message = raw.message
        content = getattr(message, "content", None) or []
        text_blocks = tuple(cls._text_content(item) for item in content)
        text = "".join(item for item in text_blocks if item is not None)
        tool_calls = tuple(
            ToolCallRequest(
                tool_call_id=str(item.id),
                name=str(item.function.name),
                arguments_json=str(item.function.arguments),
            )
            for item in (getattr(message, "tool_calls", None) or [])
        )
        citation_ids, citations = cls._citations(
            getattr(message, "citations", None) or [], text_blocks
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
            citation_ids=citation_ids,
            citations=citations,
            usage=usage,
        )

    @staticmethod
    def _value(value: Any, name: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    @classmethod
    def _text_content(cls, content_item: Any) -> str | None:
        block_type = cls._value(content_item, "type", None)
        if hasattr(block_type, "value"):
            block_type = block_type.value
        if block_type is not None and str(block_type).rsplit(".", 1)[-1].lower() != "text":
            return None
        text = cls._value(content_item, "text", None)
        return text if isinstance(text, str) else None

    @classmethod
    def _citations(
        cls, raw_citations: Any, text_blocks: tuple[str | None, ...]
    ) -> tuple[tuple[str, ...], tuple[ProviderCitation, ...]]:
        source_ids: list[str] = []
        normalized: list[ProviderCitation] = []
        for raw_citation in raw_citations:
            raw_sources = cls._value(raw_citation, "sources", None) or []
            sources: list[ProviderCitationSource] = []
            for raw_source in raw_sources:
                source_id = cls._value(raw_source, "id", None)
                if source_id is None:
                    continue
                source_id = str(source_id)
                sources.append(
                    ProviderCitationSource(
                        source_id=source_id,
                        source_type=str(cls._value(raw_source, "type", "unknown")),
                    )
                )

            # Retain compatibility with older SDK response objects without ever
            # inventing the literal fallback ID that obscured live provenance.
            if not sources:
                legacy_id = cls._value(raw_citation, "id", None)
                if legacy_id is None:
                    legacy_id = cls._value(raw_citation, "document_id", None)
                if legacy_id is not None:
                    legacy_id = str(legacy_id)

            start = cls._value(raw_citation, "start", None)
            end = cls._value(raw_citation, "end", None)
            citation_text = cls._value(raw_citation, "text", None)
            content_index = cls._value(raw_citation, "content_index", None)
            unambiguous_text_response = len(text_blocks) == 1 and isinstance(text_blocks[0], str)
            if content_index is None and unambiguous_text_response:
                # SDK 7 declares content_index optional and normal single-block
                # responses can omit it. Hidden or additional blocks make any
                # inferred index ambiguous, even when only one block is visible.
                content_index = 0
            citation_type = cls._value(raw_citation, "type", None)
            if hasattr(citation_type, "value"):
                citation_type = citation_type.value
            if citation_type is None and unambiguous_text_response:
                # The SDK and Cohere's RAG examples also permit an omitted type.
                # Default only for the same unambiguous one-block response.
                citation_type = "TEXT_CONTENT"
            citation_type = (
                str(citation_type).rsplit(".", 1)[-1].upper() if citation_type is not None else None
            )
            referenced_text = (
                text_blocks[content_index]
                if isinstance(content_index, int)
                and not isinstance(content_index, bool)
                and 0 <= content_index < len(text_blocks)
                else None
            )
            if (
                sources
                # ResolveFlow retains only visible text citations. Thinking/plan
                # offsets use different provider content semantics and must never
                # be validated against a visible text block by coincidence.
                and citation_type == "TEXT_CONTENT"
                and isinstance(content_index, int)
                and not isinstance(content_index, bool)
                and isinstance(referenced_text, str)
                and isinstance(start, int)
                and not isinstance(start, bool)
                and isinstance(end, int)
                and not isinstance(end, bool)
                and isinstance(citation_text, str)
                and 0 <= start <= end
                and end <= len(referenced_text)
                and referenced_text[start:end] == citation_text
            ):
                source_ids.extend(source.source_id for source in sources)
                normalized.append(
                    ProviderCitation(
                        content_index=content_index,
                        citation_type=citation_type,
                        start=start,
                        end=end,
                        text=citation_text,
                        sources=tuple(sources),
                    )
                )
        return tuple(dict.fromkeys(source_ids)), tuple(normalized)

    @staticmethod
    def _usage(raw: Any) -> ProviderUsage:
        if raw is None:
            raise ValueError("provider response omitted required token usage")
        if hasattr(raw, "model_dump"):
            data = raw.model_dump(mode="json")
        elif isinstance(raw, dict):
            data = raw
        else:
            data = json.loads(json.dumps(raw, default=lambda value: value.__dict__))

        def token_count(value: Any) -> int | None:
            if isinstance(value, bool) or not isinstance(value, int | float):
                return None
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
                return None
            return int(numeric)

        def complete_pair(block: Any) -> ProviderUsage | None:
            if not isinstance(block, dict):
                return None
            input_tokens = token_count(block.get("input_tokens"))
            output_tokens = token_count(block.get("output_tokens"))
            if input_tokens is None or output_tokens is None:
                return None
            return ProviderUsage(input_tokens=input_tokens, output_tokens=output_tokens)

        if isinstance(data, dict):
            for field in ("tokens", "billed_units"):
                parsed = complete_pair(data.get(field))
                if parsed is not None:
                    return parsed
        raise ValueError("provider response omitted complete token usage")
