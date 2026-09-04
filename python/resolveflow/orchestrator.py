from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, model_validator

from resolveflow.actions.models import ActionProposal
from resolveflow.actions.service import ActionService, fixture_now
from resolveflow.agent.findings import UnknownDraft
from resolveflow.agent.renderer import DeterministicRenderer
from resolveflow.agent.security import score_forbidden_effects
from resolveflow.agent.service import GovernedAgent, GovernedRunResult
from resolveflow.context.ports import ContextRepository
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import Corpus, IdentitySnapshot, RetrievalTrace, stable_id
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import (
    ActionBoundary,
    AuditEvent,
    CanonicalCase,
    ContextResult,
    RunSnapshot,
)
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.policy.replay import UnsafeReplayAuthorizationPolicy
from resolveflow.retrieval.cohere import ProviderAdapterError
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter
from resolveflow.retrieval.ports import EmbeddingPort, RerankPort
from resolveflow.telemetry.stages import (
    STAGE_ACL,
    STAGE_ACTION,
    STAGE_CONTEXT,
    STAGE_EVIDENCE_PASS,
    STAGE_FUSION,
    STAGE_HOSTILE_SCAN,
    STAGE_INTAKE,
    STAGE_LEXICAL,
    STAGE_RENDERING,
    STAGE_RERANK,
    STAGE_TOOLS,
    STAGE_VECTOR,
    STAGE_VERIFICATION,
    RunTiming,
    StageRecorder,
)
from resolveflow.verifier.models import EvidenceGraph


class ContextEnrichmentError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _context_before_deadline(
    deadline: float, repository: ContextRepository, case: CanonicalCase
) -> tuple[ContextResult, ...]:
    """Invoke only context ports that explicitly accept the remaining deadline."""

    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise ContextEnrichmentError("wall_clock_budget_exhausted")
    if not getattr(repository, "supports_deadline", False):
        raise ContextEnrichmentError("context_deadline_unsupported")
    try:
        result = repository.enrich(case, timeout_seconds=remaining)
    except Exception as exc:
        raise ContextEnrichmentError("context_enrichment_failed") from exc
    if time.perf_counter() > deadline:
        raise ContextEnrichmentError("wall_clock_budget_exhausted")
    return result


# Maps each audit event to the stage whose measured duration it reports. An event
# with no mapped stage keeps duration_ms=0, which means "not separately measured",
# not "took no time".
EVENT_STAGE: dict[str, str] = {
    "identity.snapshot.captured": STAGE_INTAKE,
    "case.normalized": STAGE_INTAKE,
    "context.enriched": STAGE_CONTEXT,
    "retrieval.authorization.applied": STAGE_ACL,
    "retrieval.lexical.completed": STAGE_LEXICAL,
    "retrieval.vector.completed": STAGE_VECTOR,
    "retrieval.fusion.completed": STAGE_FUSION,
    "retrieval.rerank.completed": STAGE_RERANK,
    "model.evidence_pass.completed": STAGE_EVIDENCE_PASS,
    "tools.bounded.completed": STAGE_TOOLS,
    "untrusted_evidence.checked": STAGE_HOSTILE_SCAN,
    "evidence_graph.verified": STAGE_VERIFICATION,
    "evidence_graph.observed": STAGE_VERIFICATION,
    "structured_response.rendered": STAGE_RENDERING,
    "proposal.created": STAGE_ACTION,
    "proposal.blocked": STAGE_ACTION,
}


class ResolveRunConfiguration(FrozenModel):
    run_id: str
    build_id: str
    generated_at: datetime
    scenario_id: str | None = None
    identity: IdentitySnapshot
    corpus: Corpus
    authorization_mode: Literal["enforced", "prompt_only"] = "enforced"
    verifier_enforcement: Literal["enforced", "observe_only"] = "enforced"
    model_policy: str
    connector_state: str = "synthetic_not_dispatched"
    connector_fixture_version: str = "synthetic-jira-1.0"
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    rerank_model: str | None = None
    rerank_escalation_reason: str | None = None
    # "deterministic" keeps audit-event durations at zero so recorded-fixture replays
    # stay byte-identical and the hash chain remains reproducible. "measured" writes
    # real monotonic-clock stage durations into the audit events. Measured stage
    # timings are always emitted on RunSnapshot.timing regardless of this setting;
    # the flag only controls whether they enter the hashed audit chain.
    timing_mode: Literal["deterministic", "measured"] = "deterministic"

    @model_validator(mode="after")
    def validate_rerank_escalation(self) -> ResolveRunConfiguration:
        reason = self.rerank_escalation_reason
        if reason is not None and not reason.strip():
            raise ValueError("rerank escalation reason must be nonblank")
        if self.rerank_model is not None and self.rerank_model.lower().endswith("-pro"):
            if reason is None:
                raise ValueError("every Pro rerank run requires an escalation reason")
        elif reason is not None:
            raise ValueError("rerank escalation reason is only valid for a Pro rerank model")
        return self


class ResolveOrchestrator:
    """Shared production path used by web intake, fixtures, snapshots, and future Replay."""

    def __init__(
        self,
        context_repository: ContextRepository,
        agent: GovernedAgent,
        *,
        embedding_adapter: EmbeddingPort | None = None,
        rerank_adapter: RerankPort | None = None,
        pro_rerank_adapter: RerankPort | None = None,
    ) -> None:
        self.context_repository = context_repository
        self.agent = agent
        self.corpus = load_hero_corpus()
        self.embedding_adapter = embedding_adapter or FixtureEmbeddingAdapter()
        self.rerank_adapter = rerank_adapter or FixtureRerankAdapter()
        self.pro_rerank_adapter = pro_rerank_adapter
        self.latest_proposal: ActionProposal | None = None

    @property
    def provenance(self) -> Literal["recorded_fixture", "live_provider"]:
        return (
            "live_provider" if self.agent.provider.provider_name == "cohere" else "recorded_fixture"
        )

    def run(
        self, case: CanonicalCase, configuration: ResolveRunConfiguration | None = None
    ) -> RunSnapshot:
        run_started_ns = self.agent.clock()
        run_deadline = time.perf_counter() + self.agent.budgets.wall_clock_seconds
        if configuration is None:
            identity = make_identity_snapshot(
                tenant_id=case.tenant_id,
                actor_id="user_incident_commander_synthetic",
                role="incident_commander",
                region=case.region,
                case_time=case.case_time,
            )
            configuration = ResolveRunConfiguration(
                run_id="run_hero_foundation_001",
                build_id="governed-fixture-v1",
                generated_at=datetime(2026, 7, 21, 0, 0, tzinfo=timezone.utc),
                identity=identity,
                corpus=self.corpus,
                model_policy=self.agent.budgets.policy_id,
                feature_flags={"replay": False},
            )
        run_id = configuration.run_id
        recorder = StageRecorder()
        with recorder.stage(STAGE_INTAKE):
            identity = configuration.identity
            policy = (
                AuthorizationPolicy()
                if configuration.authorization_mode == "enforced"
                else UnsafeReplayAuthorizationPolicy()
            )
            selected_reranker = self._reranker_for(configuration)
            retriever = HybridRetriever(
                configuration.corpus,
                policy,
                self.embedding_adapter,
                selected_reranker,
            )
        context: tuple[ContextResult, ...] = ()
        retrieval_provider_call_count = 0
        retrieval_provider_call_ms = 0.0
        try:
            with recorder.stage(STAGE_CONTEXT):
                context = _context_before_deadline(run_deadline, self.context_repository, case)
            retrieval = retriever.retrieve(
                case.raw_text,
                identity,
                rerank_model=configuration.rerank_model,
                escalation_reason=configuration.rerank_escalation_reason,
                recorder=recorder,
                deadline=run_deadline,
            )
            governed = self.agent.resolve(
                run_id=run_id,
                case=case,
                context=context,
                identity=identity,
                retrieval=retrieval,
                corpus=configuration.corpus,
                verifier_enforcement=configuration.verifier_enforcement,
                recorder=recorder,
                started_at_ns=run_started_ns,
            )
            retrieval_provider_call_count = retriever.last_provider_call_count
            retrieval_provider_call_ms = retriever.last_provider_call_ms
        except ContextEnrichmentError as exc:
            failure_code = exc.reason_code
            retrieval = self._failed_retrieval(
                case=case,
                identity=identity,
                corpus=configuration.corpus,
                policy=policy,
                failure_code=failure_code,
                failure_stage="context",
                rerank_adapter=selected_reranker,
                rerank_escalation_reason=configuration.rerank_escalation_reason,
            )
            governed = self._failed_governed_run(run_id, failure_code)
        except ProviderAdapterError as exc:
            failure_code = (
                "wall_clock_budget_exhausted"
                if exc.endpoint == "deadline"
                else (
                    "retrieval_deadline_unsupported"
                    if exc.endpoint == "unbounded_adapter"
                    else f"retrieval_{exc.endpoint}_provider_error"
                )
            )
            retrieval_provider_call_count = exc.provider_call_count
            retrieval_provider_call_ms = exc.provider_call_ms
            failure_stage: Literal["context", "vector", "rerank"] = (
                "rerank" if exc.failure_stage == "rerank" else "vector"
            )
            retrieval = self._failed_retrieval(
                case=case,
                identity=identity,
                corpus=configuration.corpus,
                policy=policy,
                failure_code=failure_code,
                failure_stage=failure_stage,
                rerank_adapter=selected_reranker,
                rerank_escalation_reason=configuration.rerank_escalation_reason,
            )
            governed = self._failed_governed_run(run_id, failure_code)
        with recorder.stage(STAGE_ACTION):
            proposal = None
            proposal_blocked_reason: str | None = None
            if governed.evidence_graph.permitted_proposals:
                try:
                    proposal = ActionService().create_proposal(
                        run_id=run_id,
                        tenant_id=case.tenant_id,
                        graph=governed.evidence_graph,
                        response=governed.response,
                        now=fixture_now(),
                    )
                except ValueError as exc:
                    # The action service refuses proposals whose evidence is not
                    # authorized, fresh, and supporting. A graph can permit a
                    # proposal that the service then refuses -- notably in the
                    # unsafe prompt-only baseline, where claims are marked
                    # supported without their citations ever being authorized.
                    # That refusal is the control working. Record it and continue
                    # with no proposal; do not let it end the run, because a
                    # crashed run reports no security outcome at all.
                    proposal_blocked_reason = str(exc)
            else:
                proposal_blocked_reason = "evidence_graph_permits_no_proposal"
        self.latest_proposal = proposal
        timing = recorder.snapshot(
            provider_call_ms=(
                float(sum(item.duration_ms for item in governed.provider_traces))
                + retrieval_provider_call_ms
            ),
            provider_call_count=(len(governed.provider_traces) + retrieval_provider_call_count),
        )
        events = self._events(
            run_id,
            configuration.build_id,
            configuration.verifier_enforcement,
            case,
            identity,
            context,
            retrieval.eligible_chunk_count,
            governed,
            proposal,
            timing if configuration.timing_mode == "measured" else None,
            proposal_blocked_reason,
            retrieval.failure_code,
            retrieval.failure_stage,
        )
        run_inputs = {
            "clock": checksum(configuration.generated_at),
            "identity": identity.checksum,
            "acl": retrieval.acl_snapshot_id,
            "corpus": configuration.corpus.snapshot.checksum,
            "policy": checksum(configuration.model_policy),
            "connector": checksum(
                {
                    "state": configuration.connector_state,
                    "fixture_version": configuration.connector_fixture_version,
                }
            ),
            "feature_flags": checksum(configuration.feature_flags),
            "authorization_mode": configuration.authorization_mode,
            "verifier_enforcement": configuration.verifier_enforcement,
        }
        body = {
            "provenance": self.provenance,
            "generated_at": configuration.generated_at,
            "run_id": run_id,
            "build_id": configuration.build_id,
            "scenario_id": configuration.scenario_id,
            "commit": _git_sha(),
            "model_policy": configuration.model_policy,
            "corpus_version": retrieval.corpus_snapshot_id,
            "identity_snapshot": identity,
            "retrieval": retrieval,
            "case": case,
            "context": context,
            "response": governed.response,
            "evidence_graph": governed.evidence_graph.model_dump(mode="json"),
            "provider_traces": tuple(
                item.model_dump(mode="json") for item in governed.provider_traces
            ),
            "tool_traces": tuple(item.model_dump(mode="json") for item in governed.tool_traces),
            "security_events": tuple(
                item.model_dump(mode="json") for item in governed.security_events
            ),
            "forbidden_effect_score": score_forbidden_effects(governed.security_events).model_dump(
                mode="json"
            ),
            "action": self._action_projection(proposal),
            "trace": events,
            "run_inputs": run_inputs,
        }
        snapshot = RunSnapshot(**body, timing=timing, content_hash="sha256:" + "0" * 64)
        return snapshot.model_copy(
            update={
                "content_hash": checksum(
                    snapshot.model_dump(
                        mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS
                    )
                )
            }
        )

    def _reranker_for(self, configuration: ResolveRunConfiguration) -> RerankPort:
        requested = configuration.rerank_model
        if requested is None or requested == self.rerank_adapter.model:
            return self.rerank_adapter
        if self.pro_rerank_adapter is not None and requested == self.pro_rerank_adapter.model:
            return self.pro_rerank_adapter
        raise ValueError("requested rerank model has no configured production adapter")

    def _failed_retrieval(
        self,
        *,
        case: CanonicalCase,
        identity: IdentitySnapshot,
        corpus: Corpus,
        policy: AuthorizationPolicy,
        failure_code: str,
        failure_stage: Literal["context", "vector", "rerank"],
        rerank_adapter: RerankPort,
        rerank_escalation_reason: str | None,
    ) -> RetrievalTrace:
        eligible_ids = policy.eligible_chunk_ids(
            identity, corpus.versions, corpus.chunks, corpus.acls
        )
        acl_snapshot = policy.snapshot(identity, corpus.snapshot.snapshot_id, eligible_ids)
        body = {
            "query_checksum": checksum(case.raw_text),
            "corpus_snapshot_id": corpus.snapshot.snapshot_id,
            "identity_snapshot_id": identity.snapshot_id,
            "acl_snapshot_id": acl_snapshot.snapshot_id,
            "cache_key": policy.cache_key(identity, corpus.snapshot.snapshot_id, case.raw_text),
            "eligible_chunk_count": len(eligible_ids),
            "lexical_candidate_ids": (),
            "vector_candidate_ids": (),
            "embedding_model": self.embedding_adapter.model,
            "embedding_source": "unavailable",
            "rerank_model": rerank_adapter.model,
            "rerank_escalation_reason": rerank_escalation_reason,
            "rerank_payload_checksum": None,
            "candidates": (),
            "failure_code": failure_code,
            "failure_stage": failure_stage,
        }
        return RetrievalTrace(**body, checksum=checksum(body))

    def _failed_governed_run(self, run_id: str, failure_code: str) -> GovernedRunResult:
        unknown = UnknownDraft(
            unknown_id="unknown_retrieval_provider",
            field="retrieval",
            text="Evidence retrieval is unavailable; no resolution was attempted.",
            reason_code=failure_code,
        )
        graph_body = {
            "schema_version": "1.0",
            "graph_id": stable_id("graph", {"run_id": run_id, "failure": failure_code}),
            "run_id": run_id,
            "claims": (),
            "citations": (),
            "unknowns": (unknown,),
            "conflicts": (),
            "route_candidates": (),
            "permitted_proposals": (),
            "model_context_ids": (),
        }
        graph = EvidenceGraph(**graph_body, graph_hash=checksum(graph_body))
        response = DeterministicRenderer().fallback(
            graph,
            provider=(
                "cohere" if self.agent.provider.provider_name == "cohere" else "recorded_fixture"
            ),
        )
        return GovernedRunResult(
            response=response,
            evidence_graph=graph,
            provider_traces=(),
            tool_traces=(),
            security_events=(),
            terminal_reason=failure_code,
            provider_calls=0,
            total_tokens=0,
        )

    @staticmethod
    def _events(
        run_id: str,
        build_id: str,
        verifier_enforcement: str,
        case: CanonicalCase,
        identity: IdentitySnapshot,
        context: tuple[object, ...],
        eligible_count: int,
        governed: GovernedRunResult,
        proposal: ActionProposal | None,
        timing: RunTiming | None = None,
        proposal_blocked_reason: str | None = None,
        retrieval_failure_code: str | None = None,
        retrieval_failure_stage: str | None = None,
    ) -> tuple[AuditEvent, ...]:
        at = case.case_time
        measured = timing.by_stage() if timing is not None else {}
        retrieval_detail: dict[str, object] = {"authorized": True}
        if retrieval_failure_code is not None:
            retrieval_detail["failure_code"] = retrieval_failure_code
            retrieval_detail["failure_stage"] = retrieval_failure_stage

        stage_order = {"context": 0, "vector": 3, "rerank": 5}
        failed_order = stage_order.get(retrieval_failure_stage or "", 99)

        def retrieval_event(
            order: int, completed_name: str, success_detail: dict[str, object]
        ) -> tuple[str, str, str, dict[str, object]]:
            if retrieval_failure_code is None or order < failed_order:
                return "retrieval", completed_name, "ok", success_detail
            if order == failed_order:
                return "retrieval", completed_name, "failed", retrieval_detail
            return (
                "retrieval",
                completed_name.removesuffix(".completed") + ".not_attempted",
                "rejected",
                {
                    "reason_code": retrieval_failure_code,
                    "failure_stage": retrieval_failure_stage,
                },
            )

        downstream_not_attempted = retrieval_failure_code is not None
        not_attempted_detail: dict[str, object] = {
            "reason_code": retrieval_failure_code,
            "failure_stage": retrieval_failure_stage,
        }
        raw: tuple[tuple[str, str, str, dict[str, object]], ...] = (
            (
                "identity",
                "identity.snapshot.captured",
                "ok",
                {"role": identity.active_role, "region": identity.region},
            ),
            ("intake", "case.normalized", "ok", {"source": case.source_system}),
            (
                "context",
                "context.enriched"
                if retrieval_failure_stage != "context"
                else "context.enrichment.failed",
                (
                    "needs_information"
                    if retrieval_failure_stage != "context"
                    else (
                        "timeout"
                        if retrieval_failure_code == "wall_clock_budget_exhausted"
                        else "failed"
                    )
                ),
                {
                    "operations": len(context),
                    **(not_attempted_detail if retrieval_failure_stage == "context" else {}),
                },
            ),
            (
                "policy",
                (
                    "retrieval.authorization.not_attempted"
                    if retrieval_failure_stage == "context"
                    else "retrieval.authorization.applied"
                ),
                "rejected" if retrieval_failure_stage == "context" else "ok",
                (
                    not_attempted_detail
                    if retrieval_failure_stage == "context"
                    else {"reason_code": "eligible_by_snapshot", "eligible_count": eligible_count}
                ),
            ),
            retrieval_event(2, "retrieval.lexical.completed", {"authorized": True}),
            retrieval_event(3, "retrieval.vector.completed", {"authorized": True}),
            retrieval_event(4, "retrieval.fusion.completed", {"authorized": True}),
            retrieval_event(5, "retrieval.rerank.completed", {"authorized": True}),
            (
                "agent",
                (
                    "model.evidence_pass.not_attempted"
                    if downstream_not_attempted
                    else "model.evidence_pass.completed"
                ),
                (
                    "rejected"
                    if downstream_not_attempted
                    else ("ok" if governed.terminal_reason == "complete" else "failed")
                ),
                not_attempted_detail
                if downstream_not_attempted
                else {
                    "provider_calls": governed.provider_calls,
                    "terminal_reason": governed.terminal_reason,
                },
            ),
            (
                "agent",
                "tools.bounded.not_attempted"
                if downstream_not_attempted
                else "tools.bounded.completed",
                "rejected" if downstream_not_attempted else "ok",
                not_attempted_detail
                if downstream_not_attempted
                else {"tool_calls": len(governed.tool_traces)},
            ),
            (
                "security",
                (
                    "untrusted_evidence.not_attempted"
                    if downstream_not_attempted
                    else "untrusted_evidence.checked"
                ),
                "rejected" if downstream_not_attempted else "ok",
                not_attempted_detail
                if downstream_not_attempted
                else {"attempted_effects": len(governed.security_events)},
            ),
            (
                "verifier",
                (
                    "evidence_graph.verification.not_attempted"
                    if downstream_not_attempted
                    else (
                        "evidence_graph.verified"
                        if verifier_enforcement == "enforced"
                        else "evidence_graph.observed"
                    )
                ),
                (
                    "rejected"
                    if downstream_not_attempted
                    else ("ok" if not governed.response.needs_review else "needs_information")
                ),
                not_attempted_detail
                if downstream_not_attempted
                else {
                    "claims": len(governed.evidence_graph.claims),
                    "graph_hash": governed.evidence_graph.graph_hash,
                    "route": governed.response.route,
                    "enforcement": verifier_enforcement,
                },
            ),
            (
                "agent",
                (
                    "structured_response.fallback_rendered"
                    if downstream_not_attempted
                    else "structured_response.rendered"
                ),
                "needs_information"
                if downstream_not_attempted or governed.response.needs_review
                else "ok",
                (
                    {**not_attempted_detail, "disposition": governed.response.disposition}
                    if downstream_not_attempted
                    else {"disposition": governed.response.disposition}
                ),
            ),
            (
                "actions",
                "proposal.created" if proposal is not None else "proposal.blocked",
                "ok" if proposal is not None else "rejected",
                {
                    "state": ("pending_approval" if proposal is not None else "not_proposed"),
                    "payload_digest": proposal.payload_digest if proposal else None,
                    "blocked_reason": proposal_blocked_reason,
                },
            ),
        )
        events: list[AuditEvent] = []
        previous_hash: str | None = None
        for index, (component, name, outcome, detail) in enumerate(raw, 1):
            stage = EVENT_STAGE.get(name)
            body = {
                "sequence": index,
                "occurred_at": at,
                "actor": "resolveflow-service",
                "component": component,
                "event_name": name,
                "outcome": outcome,
                "correlation_id": run_id,
                "duration_ms": (max(0.0, round(measured[stage], 6)) if stage in measured else 0.0),
                "versions": {"schema": "1.0", "build": build_id},
                "trace_id": f"trace_{run_id}",
                "span_id": f"span_{index:03d}",
                "safe_detail": detail,
                "previous_event_hash": previous_hash,
            }
            event_hash = checksum(body)
            event = AuditEvent(
                sequence=index,
                event_id=f"evt_{index:03d}",
                **{key: value for key, value in body.items() if key != "sequence"},
                event_hash=event_hash,
            )
            events.append(event)
            previous_hash = event_hash
        return tuple(events)

    @staticmethod
    def _action_projection(proposal: ActionProposal | None) -> ActionBoundary:
        if proposal is None:
            return ActionBoundary(state="not_proposed", summary="No verified proposal")
        payload = proposal.payload
        return ActionBoundary(
            proposal_id=proposal.proposal_id,
            state="pending_approval",
            summary=payload.summary,
            team=payload.team,
            priority=payload.priority,
            verified_description=payload.verified_description,
            evidence_refs=payload.evidence_refs,
            unknowns=payload.unknowns,
            risk=payload.risk,
            expires_at=proposal.expires_at,
            payload_digest=proposal.payload_digest,
            idempotency_key=proposal.idempotency_key,
        )


def _git_sha() -> str:
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if status.strip():
            return "uncommitted"
        return subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"
