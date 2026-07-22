from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Literal

from pydantic import ValidationError

from resolveflow.agent.contracts import (
    AgentBudgets,
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderError,
    ProviderTimeoutError,
    ProviderTrace,
    ProviderUsage,
    ToolTrace,
    UntrustedEvidenceDocument,
)
from resolveflow.agent.findings import FirstPassFindings, UnknownDraft
from resolveflow.agent.ports import ChatProviderPort
from resolveflow.agent.renderer import DeterministicRenderer, StructureSelection
from resolveflow.agent.security import (
    ATTACK_PATTERNS,
    SYSTEM_PROMPT,
    SecurityEvent,
    detect_hostile_evidence,
    require_policy_lint_clean,
)
from resolveflow.agent.tools import ToolRegistry
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import Corpus, IdentitySnapshot, RetrievalTrace
from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.domain.models import CanonicalCase, ContextResult, FinalResponse
from resolveflow.verifier.engine import EvidenceVerifier
from resolveflow.verifier.models import EvidenceGraph


class GovernedRunResult(FrozenModel):
    response: FinalResponse
    evidence_graph: EvidenceGraph
    provider_traces: tuple[ProviderTrace, ...]
    tool_traces: tuple[ToolTrace, ...]
    security_events: tuple[SecurityEvent, ...]
    terminal_reason: str
    provider_calls: int
    total_tokens: int


class GovernedAgent:
    """Bounded evidence/tool pass, deterministic verification, and strict structure pass."""

    def __init__(
        self,
        provider: ChatProviderPort,
        *,
        budgets: AgentBudgets | None = None,
        model: str = "command-a-plus-05-2026",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.provider = provider
        self.budgets = budgets or AgentBudgets()
        self.model = model
        self.clock = clock
        self.verifier = EvidenceVerifier()
        self.renderer = DeterministicRenderer()

    def resolve(
        self,
        *,
        run_id: str,
        case: CanonicalCase,
        context: tuple[ContextResult, ...],
        identity: IdentitySnapshot,
        retrieval: RetrievalTrace,
        corpus: Corpus,
    ) -> GovernedRunResult:
        started = self.clock()
        documents = self._documents(retrieval, corpus)
        registry = ToolRegistry(case, context)
        require_policy_lint_clean(SYSTEM_PROMPT, registry.definitions)
        security_events = detect_hostile_evidence(documents)
        provider_traces: list[ProviderTrace] = []
        tool_traces: list[ToolTrace] = []
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": canonical_json(
                    {
                        "case_id": case.case_id,
                        "tenant_id": case.tenant_id,
                        "error_code": case.error_code,
                        "service": case.service,
                        "missing_fields": case.missing_fields,
                        "task": "Return evidence-linked findings as JSON.",
                    }
                ),
            },
        ]
        total_tokens = 0
        tool_rounds = 0
        findings: FirstPassFindings | None = None
        terminal_reason = "complete"

        while findings is None:
            if self._expired(started):
                terminal_reason = "wall_clock_budget_exhausted"
                break
            if len(provider_traces) >= self.budgets.max_provider_calls - 1:
                terminal_reason = "provider_call_budget_exhausted"
                break
            remaining = self.budgets.max_total_tokens - total_tokens
            if remaining < 64:
                terminal_reason = "token_budget_exhausted"
                break
            request = ChatRequest(
                pass_kind=PassKind.EVIDENCE,
                model=self.model,
                messages=tuple(messages),
                documents=documents,
                tools=registry.definitions,
                strict_tools=True,
                max_tokens=min(self.budgets.max_output_tokens_per_call, remaining),
                temperature=0.0,
                seed=17,
            )
            response, trace = self._provider_call(
                request,
                len(provider_traces) + 1,
                timeout_seconds=max(
                    0.001,
                    self.budgets.wall_clock_seconds - (self.clock() - started),
                ),
            )
            provider_traces.append(trace)
            total_tokens += trace.usage.total_tokens
            if response is None:
                terminal_reason = trace.safe_error_code or trace.status
                break
            if total_tokens > self.budgets.max_total_tokens:
                terminal_reason = "token_budget_exhausted"
                break
            if response.tool_calls:
                tool_rounds += 1
                if tool_rounds > self.budgets.max_tool_rounds:
                    terminal_reason = "tool_round_budget_exhausted"
                    break
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.text,
                        "tool_calls": [
                            {
                                "id": call.tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": call.name,
                                    "arguments": call.arguments_json,
                                },
                            }
                            for call in response.tool_calls
                        ],
                    }
                )
                for call in response.tool_calls:
                    result, tool_trace = registry.execute(
                        call, timeout_seconds=self.budgets.tool_timeout_seconds
                    )
                    if self.provider.provider_name == "recorded_fixture":
                        tool_trace = tool_trace.model_copy(update={"duration_ms": 0})
                    tool_traces.append(tool_trace)
                    messages.append(result.as_message())
                continue
            if response.finish_reason is not FinishReason.COMPLETE:
                terminal_reason = f"provider_finish_{response.finish_reason.value}"
                break
            try:
                findings = FirstPassFindings.model_validate_json(response.text)
            except (ValidationError, ValueError, json.JSONDecodeError):
                provider_traces[-1] = provider_traces[-1].model_copy(
                    update={
                        "status": "malformed",
                        "safe_error_code": "evidence_findings_invalid",
                    }
                )
                terminal_reason = "evidence_findings_invalid"
                break

        if findings is None:
            findings = FirstPassFindings(
                claims=(),
                citations=(),
                unknowns=(
                    UnknownDraft(
                        unknown_id="unknown_verified_resolution",
                        field="verified_resolution",
                        text="A verified resolution is unavailable and requires review.",
                        reason_code=terminal_reason,
                    ),
                ),
            )
        graph = self.verifier.verify(
            run_id=run_id,
            findings=findings,
            documents=documents,
            identity=identity,
            corpus=corpus,
        )
        final_response = self.renderer.fallback(graph, provider=self._provider_label())
        if (
            terminal_reason == "complete"
            and not self._expired(started)
            and len(provider_traces) < self.budgets.max_provider_calls
            and self.budgets.max_total_tokens - total_tokens >= 64
        ):
            structure_request = ChatRequest(
                pass_kind=PassKind.STRUCTURE,
                model=self.model,
                messages=(
                    {
                        "role": "system",
                        "content": (
                            "Select only IDs from the verified graph. Return JSON matching the "
                            "schema. Do not add facts or prose."
                        ),
                    },
                    {"role": "user", "content": canonical_json(graph)},
                ),
                response_schema=StructureSelection.model_json_schema(),
                max_tokens=min(
                    self.budgets.max_output_tokens_per_call,
                    self.budgets.max_total_tokens - total_tokens,
                ),
                temperature=0.0,
                seed=17,
            )
            structured, trace = self._provider_call(
                structure_request,
                len(provider_traces) + 1,
                timeout_seconds=max(
                    0.001,
                    self.budgets.wall_clock_seconds - (self.clock() - started),
                ),
            )
            provider_traces.append(trace)
            total_tokens += trace.usage.total_tokens
            if structured is not None and total_tokens <= self.budgets.max_total_tokens:
                try:
                    selection = StructureSelection.model_validate_json(structured.text)
                    final_response = self.renderer.render(
                        graph, selection, provider=self._provider_label()
                    )
                except (ValidationError, ValueError, json.JSONDecodeError):
                    provider_traces[-1] = provider_traces[-1].model_copy(
                        update={
                            "status": "malformed",
                            "safe_error_code": "structured_response_invalid",
                        }
                    )
                    terminal_reason = "structured_response_invalid"
            elif trace.safe_error_code:
                terminal_reason = trace.safe_error_code

        return GovernedRunResult(
            response=final_response,
            evidence_graph=graph,
            provider_traces=tuple(provider_traces),
            tool_traces=tuple(tool_traces),
            security_events=security_events,
            terminal_reason=terminal_reason,
            provider_calls=len(provider_traces),
            total_tokens=total_tokens,
        )

    def _provider_call(
        self, request: ChatRequest, sequence: int, *, timeout_seconds: float
    ) -> tuple[ChatResponse | None, ProviderTrace]:
        started = self.clock()
        request_hash = checksum(request)
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="resolveflow-provider")
        future = executor.submit(self.provider.chat, request)
        try:
            response = future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            future.cancel()
            return None, self._trace(
                sequence, request, started, request_hash, None, "timeout", "provider_timeout"
            )
        except ProviderTimeoutError:
            return None, self._trace(
                sequence, request, started, request_hash, None, "timeout", "provider_timeout"
            )
        except ProviderError:
            return None, self._trace(
                sequence, request, started, request_hash, None, "error", "provider_error"
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return response, self._trace(sequence, request, started, request_hash, response, "ok", None)

    def _trace(
        self,
        sequence: int,
        request: ChatRequest,
        started: float,
        request_hash: str,
        response: ChatResponse | None,
        status: Literal["ok", "timeout", "malformed", "error", "budget_exhausted"],
        error: str | None,
    ) -> ProviderTrace:
        return ProviderTrace(
            provider_call_id=f"provider_{sequence:02d}",
            pass_kind=request.pass_kind,
            model=request.model,
            status=status,
            request_hash=request_hash,
            response_hash=checksum(response.text) if response else None,
            response_id=response.response_id if response else None,
            finish_reason=response.finish_reason if response else None,
            tool_call_names=tuple(call.name for call in response.tool_calls) if response else (),
            citation_ids=response.citation_ids if response else (),
            usage=response.usage if response else ProviderUsage(input_tokens=0, output_tokens=0),
            duration_ms=(
                0
                if self.provider.provider_name == "recorded_fixture"
                else max(0, int((self.clock() - started) * 1000))
            ),
            safe_error_code=error,
        )

    def _expired(self, started: float) -> bool:
        return self.clock() - started >= self.budgets.wall_clock_seconds

    def _provider_label(self) -> Literal["recorded_fixture", "cohere"]:
        return "cohere" if self.provider.provider_name == "cohere" else "recorded_fixture"

    @staticmethod
    def _documents(
        retrieval: RetrievalTrace, corpus: Corpus
    ) -> tuple[UntrustedEvidenceDocument, ...]:
        version_by_id = {item.artifact_version_id: item for item in corpus.versions}
        documents: list[UntrustedEvidenceDocument] = []
        for candidate in retrieval.candidates:
            version = version_by_id[candidate.artifact_version_id]
            hostile = candidate.artifact_id == "artifact_hostile_note" or any(
                pattern.search(candidate.content) for _, pattern in ATTACK_PATTERNS
            )
            documents.append(
                UntrustedEvidenceDocument(
                    document_id=candidate.chunk_id,
                    artifact_id=candidate.artifact_id,
                    artifact_version_id=candidate.artifact_version_id,
                    title=candidate.title,
                    version=version.version,
                    locator=candidate.position.locator,
                    content=candidate.content,
                    content_checksum=candidate.content_checksum,
                    hostile=hostile,
                )
            )
        return tuple(documents)
