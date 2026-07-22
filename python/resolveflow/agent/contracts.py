from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel


class PassKind(str, Enum):
    EVIDENCE = "evidence"
    STRUCTURE = "structure"


class FinishReason(str, Enum):
    COMPLETE = "complete"
    TOOL_CALL = "tool_call"
    MAX_TOKENS = "max_tokens"
    TIMEOUT = "timeout"
    ERROR = "error"


class ToolCallRequest(FrozenModel):
    tool_call_id: str
    name: str
    arguments_json: str


class ProviderUsage(FrozenModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class UntrustedEvidenceDocument(FrozenModel):
    document_id: str
    artifact_id: str
    artifact_version_id: str
    title: str
    version: str
    locator: str
    content: str
    content_checksum: str
    untrusted: Literal[True] = True
    hostile: bool = False


class ToolDefinition(FrozenModel):
    name: str
    description: str
    parameters: dict[str, Any]
    authority: Literal["read_only", "inert_proposal"]


class ChatRequest(FrozenModel):
    pass_kind: PassKind
    model: str
    messages: tuple[dict[str, Any], ...]
    documents: tuple[UntrustedEvidenceDocument, ...] = ()
    tools: tuple[ToolDefinition, ...] = ()
    strict_tools: bool = False
    response_schema: dict[str, Any] | None = None
    max_tokens: int = Field(gt=0)
    temperature: float = Field(ge=0.0, le=1.0)
    seed: int

    @model_validator(mode="after")
    def enforce_pass_boundary(self) -> ChatRequest:
        if self.pass_kind is PassKind.STRUCTURE:
            if self.documents or self.tools or self.strict_tools:
                raise ValueError("structure pass cannot receive documents or tools")
            if self.response_schema is None:
                raise ValueError("structure pass requires a response schema")
        elif self.response_schema is not None:
            raise ValueError("evidence pass cannot request structured output")
        return self


class ChatResponse(FrozenModel):
    response_id: str
    model: str
    finish_reason: FinishReason
    text: str
    tool_calls: tuple[ToolCallRequest, ...] = ()
    citation_ids: tuple[str, ...] = ()
    usage: ProviderUsage


class ProviderTrace(FrozenModel):
    provider_call_id: str
    pass_kind: PassKind
    model: str
    status: Literal["ok", "timeout", "malformed", "error", "budget_exhausted"]
    request_hash: str
    response_hash: str | None
    response_id: str | None
    finish_reason: FinishReason | None
    tool_call_names: tuple[str, ...]
    citation_ids: tuple[str, ...]
    usage: ProviderUsage
    duration_ms: int = Field(ge=0)
    safe_error_code: str | None = None


class ToolTrace(FrozenModel):
    tool_call_id: str
    name: str
    status: Literal["ok", "rejected", "timeout", "error"]
    authorization: Literal["allowed", "denied", "not_evaluated"]
    arguments_hash: str
    duration_ms: int = Field(ge=0)
    provenance_ids: tuple[str, ...]
    safe_error_code: str | None = None
    external_write: Literal[False] = False


class AgentBudgets(FrozenModel):
    policy_id: Literal["governed-agent-1.0"] = "governed-agent-1.0"
    max_tool_rounds: int = Field(default=2, ge=1, le=8)
    max_provider_calls: int = Field(default=4, ge=2, le=12)
    max_total_tokens: int = Field(default=4096, ge=256)
    max_output_tokens_per_call: int = Field(default=1024, ge=64)
    wall_clock_seconds: float = Field(default=30.0, gt=0.0, le=120.0)
    tool_timeout_seconds: float = Field(default=2.0, gt=0.0, le=30.0)


class ProviderError(RuntimeError):
    """Normalized provider error that is safe to expose in a trace."""


class ProviderTimeoutError(ProviderError):
    pass
