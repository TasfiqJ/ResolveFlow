from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from resolveflow.domain.base import FrozenModel


class PassKind(str, Enum):
    EVIDENCE = "evidence"
    FINDINGS = "findings"
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

    @field_validator("tool_call_id", "name")
    @classmethod
    def identifier_is_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("tool-call identifiers and names must be nonblank")
        return value


class ProviderCitationSource(FrozenModel):
    source_id: str
    source_type: str


class ProviderCitation(FrozenModel):
    content_index: int = Field(ge=0)
    citation_type: Literal["TEXT_CONTENT", "THINKING_CONTENT", "PLAN"]
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str
    sources: tuple[ProviderCitationSource, ...]

    @model_validator(mode="after")
    def end_follows_start(self) -> ProviderCitation:
        if self.end < self.start:
            raise ValueError("citation end must not precede start")
        return self


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


class ToolResultEvidenceDocument(FrozenModel):
    """Data-only evidence emitted by one trusted, authorized read-only tool execution.

    This is deliberately a separate type from ``UntrustedEvidenceDocument``: a tool
    result is not a corpus chunk and must not inherit corpus ACL/version semantics.
    Its content remains untrusted model input; only the execution metadata is trusted.
    """

    schema_version: Literal["1.0"] = "1.0"
    source_kind: Literal["tool_result"] = "tool_result"
    document_id: str
    tool_call_id: str
    tool_name: str
    title: str
    locator: str
    content: str
    content_checksum: str
    authority: Literal["read_only"] = "read_only"
    authorization: Literal["allowed"] = "allowed"
    execution_status: Literal["ok"] = "ok"
    source_status: Literal["ok"] = "ok"
    freshness: Literal["run_context"] = "run_context"
    source_operation: str
    source_as_of: datetime
    source_version: Literal["context-result/1.0"] = "context-result/1.0"
    source_checksum: str
    provenance_ids: tuple[str, ...] = Field(min_length=1)
    untrusted: Literal[True] = True
    hostile: Literal[True] = True

    @field_validator("source_as_of")
    @classmethod
    def source_timestamp_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("tool-result source timestamp must be timezone-aware")
        return value

    @field_validator("provenance_ids")
    @classmethod
    def provenance_ids_are_nonblank_and_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("tool-result provenance IDs must be nonblank")
        if len(set(value)) != len(value):
            raise ValueError("tool-result provenance IDs must be unique")
        return value


EvidenceDocument = UntrustedEvidenceDocument | ToolResultEvidenceDocument


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
    tool_choice: Literal["REQUIRED", "NONE"] | None = None
    citation_mode: Literal["ACCURATE", "FAST"] | None = None
    response_schema: dict[str, Any] | None = None
    max_tokens: int = Field(gt=0)
    temperature: float = Field(ge=0.0, le=1.0)
    seed: int

    @model_validator(mode="after")
    def enforce_pass_boundary(self) -> ChatRequest:
        if self.pass_kind in {PassKind.FINDINGS, PassKind.STRUCTURE}:
            if (
                self.documents
                or self.tools
                or self.strict_tools
                or self.tool_choice is not None
                or self.citation_mode is not None
            ):
                raise ValueError("structured pass cannot receive documents or tools")
            if self.response_schema is None:
                raise ValueError("structured pass requires a response schema")
        elif self.response_schema is not None:
            raise ValueError("evidence pass cannot request structured output")
        elif self.tool_choice is not None and not self.tools:
            raise ValueError("tool choice requires at least one tool")
        return self


class ChatResponse(FrozenModel):
    response_id: str
    model: str
    finish_reason: FinishReason
    text: str
    tool_calls: tuple[ToolCallRequest, ...] = ()
    citation_ids: tuple[str, ...] = ()
    citations: tuple[ProviderCitation, ...] = ()
    usage: ProviderUsage

    @model_validator(mode="after")
    def tool_call_ids_are_unique(self) -> ChatResponse:
        call_ids = [item.tool_call_id for item in self.tool_calls]
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("provider response contains duplicate tool-call IDs")
        return self


class ProviderTrace(FrozenModel):
    provider_call_id: str
    pass_kind: PassKind
    model: str
    status: Literal["ok", "timeout", "malformed", "error", "budget_exhausted"]
    request_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    response_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    response_id: str | None
    finish_reason: FinishReason | None
    tool_call_names: tuple[str, ...]
    citation_ids: tuple[str, ...]
    citations: tuple[ProviderCitation, ...] = ()
    usage: ProviderUsage
    duration_ms: float = Field(ge=0.0)
    safe_error_code: str | None = None


class ToolTrace(FrozenModel):
    tool_call_id: str
    name: str
    status: Literal["ok", "rejected", "timeout", "error"]
    authorization: Literal["allowed", "denied", "not_evaluated"]
    authority: Literal["read_only", "inert_proposal"] | None = None
    source_status: (
        Literal["ok", "not_found", "denied", "timeout", "malformed", "unavailable"] | None
    ) = None
    freshness: Literal["run_context"] | None = None
    source_operation: str | None = None
    source_as_of: datetime | None = None
    source_version: Literal["context-result/1.0"] | None = None
    source_checksum: str | None = None
    arguments_hash: str
    duration_ms: float = Field(ge=0.0)
    provenance_ids: tuple[str, ...]
    safe_error_code: str | None = None
    external_write: Literal[False] = False

    @field_validator("source_as_of")
    @classmethod
    def source_timestamp_is_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("tool trace source timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def successful_read_has_valid_provenance(self) -> ToolTrace:
        if self.status == "ok" and self.authority == "read_only" and self.source_status == "ok":
            if not self.provenance_ids or any(not item.strip() for item in self.provenance_ids):
                raise ValueError("successful read trace requires nonblank provenance IDs")
            if len(set(self.provenance_ids)) != len(self.provenance_ids):
                raise ValueError("successful read trace requires unique provenance IDs")
        return self


class AgentBudgets(FrozenModel):
    policy_id: Literal["governed-agent-1.0"] = "governed-agent-1.0"
    max_tool_rounds: int = Field(default=2, ge=1, le=8)
    max_tool_calls_per_response: int = Field(default=4, ge=1, le=16)
    max_tool_calls_per_run: int = Field(default=8, ge=1, le=32)
    max_provider_calls: int = Field(default=4, ge=2, le=12)
    reserved_provider_calls_for_render: int = Field(default=1, ge=1, le=2)
    max_total_tokens: int = Field(
        default=4096,
        ge=256,
        description=(
            "Observed provider-usage stop threshold checked before and after each response; "
            "not a pre-call hard billing ceiling because input usage is provider-reported."
        ),
    )
    max_output_tokens_per_call: int = Field(default=1024, ge=64)
    wall_clock_seconds: float = Field(
        default=30.0,
        gt=0.0,
        le=120.0,
        description=(
            "Cooperative run deadline propagated to adapters and checked after return; provider "
            "transport timeouts do not prove a hard end-to-end server deadline."
        ),
    )
    tool_timeout_seconds: float = Field(default=2.0, gt=0.0, le=30.0)

    @model_validator(mode="after")
    def preserve_evidence_capacity(self) -> AgentBudgets:
        if self.reserved_provider_calls_for_render >= self.max_provider_calls:
            raise ValueError("render reservation must leave at least one evidence call")
        if self.max_tool_calls_per_response > self.max_tool_calls_per_run:
            raise ValueError("per-response tool-call limit cannot exceed the run limit")
        return self


class ProviderError(RuntimeError):
    """Normalized provider error that is safe to expose in a trace."""


class ProviderTimeoutError(ProviderError):
    pass
