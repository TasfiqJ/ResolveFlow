from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field

from resolveflow.actions.models import ActionProposal
from resolveflow.actions.service import ActionService, fixture_now
from resolveflow.agent.security import score_forbidden_effects
from resolveflow.agent.service import GovernedAgent, GovernedRunResult
from resolveflow.context.ports import ContextRepository
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import Corpus, IdentitySnapshot
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import ActionBoundary, AuditEvent, CanonicalCase, RunSnapshot
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.policy.replay import UnsafeReplayAuthorizationPolicy
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


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


class ResolveOrchestrator:
    """Shared production path used by web intake, fixtures, snapshots, and future Replay."""

    def __init__(self, context_repository: ContextRepository, agent: GovernedAgent) -> None:
        self.context_repository = context_repository
        self.agent = agent
        self.corpus = load_hero_corpus()
        self.retriever = HybridRetriever(
            self.corpus,
            AuthorizationPolicy(),
            FixtureEmbeddingAdapter(),
            FixtureRerankAdapter(),
        )
        self.latest_proposal: ActionProposal | None = None

    def run(
        self, case: CanonicalCase, configuration: ResolveRunConfiguration | None = None
    ) -> RunSnapshot:
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
        context = self.context_repository.enrich(case)
        identity = configuration.identity
        policy = (
            AuthorizationPolicy()
            if configuration.authorization_mode == "enforced"
            else UnsafeReplayAuthorizationPolicy()
        )
        retriever = HybridRetriever(
            configuration.corpus,
            policy,
            FixtureEmbeddingAdapter(),
            FixtureRerankAdapter(),
        )
        retrieval = retriever.retrieve(case.raw_text, identity)
        governed = self.agent.resolve(
            run_id=run_id,
            case=case,
            context=context,
            identity=identity,
            retrieval=retrieval,
            corpus=configuration.corpus,
            verifier_enforcement=configuration.verifier_enforcement,
        )
        proposal_allowed = bool(governed.evidence_graph.permitted_proposals)
        proposal = (
            ActionService().create_proposal(
                run_id=run_id,
                tenant_id=case.tenant_id,
                graph=governed.evidence_graph,
                response=governed.response,
                now=fixture_now(),
            )
            if proposal_allowed
            else None
        )
        self.latest_proposal = proposal
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
            "generated_at": configuration.generated_at,
            "run_id": run_id,
            "build_id": configuration.build_id,
            "scenario_id": configuration.scenario_id,
            "commit": _git_sha(),
            "model_policy": configuration.model_policy,
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
        return RunSnapshot(**body, content_hash=checksum(body))

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
    ) -> tuple[AuditEvent, ...]:
        at = case.case_time
        raw = (
            (
                "identity",
                "identity.snapshot.captured",
                "ok",
                {"role": identity.active_role, "region": identity.region},
            ),
            ("intake", "case.normalized", "ok", {"source": case.source_system}),
            ("context", "context.enriched", "needs_information", {"operations": len(context)}),
            (
                "policy",
                "retrieval.authorization.applied",
                "ok",
                {"reason_code": "eligible_by_snapshot", "eligible_count": eligible_count},
            ),
            ("retrieval", "retrieval.lexical.completed", "ok", {"authorized": True}),
            ("retrieval", "retrieval.vector.completed", "ok", {"authorized": True}),
            ("retrieval", "retrieval.fusion.completed", "ok", {"authorized": True}),
            ("retrieval", "retrieval.rerank.completed", "ok", {"authorized": True}),
            (
                "agent",
                "model.evidence_pass.completed",
                "ok" if governed.terminal_reason == "complete" else "failed",
                {
                    "provider_calls": governed.provider_calls,
                    "terminal_reason": governed.terminal_reason,
                },
            ),
            (
                "agent",
                "tools.bounded.completed",
                "ok",
                {"tool_calls": len(governed.tool_traces)},
            ),
            (
                "security",
                "untrusted_evidence.checked",
                "ok",
                {"attempted_effects": len(governed.security_events)},
            ),
            (
                "verifier",
                (
                    "evidence_graph.verified"
                    if verifier_enforcement == "enforced"
                    else "evidence_graph.observed"
                ),
                "ok" if not governed.response.needs_review else "needs_information",
                {
                    "claims": len(governed.evidence_graph.claims),
                    "graph_hash": governed.evidence_graph.graph_hash,
                    "route": governed.response.route,
                    "enforcement": verifier_enforcement,
                },
            ),
            (
                "agent",
                "structured_response.rendered",
                "ok" if not governed.response.needs_review else "needs_information",
                {"disposition": governed.response.disposition},
            ),
            (
                "actions",
                "proposal.created"
                if governed.evidence_graph.permitted_proposals
                else "proposal.blocked",
                "ok" if governed.evidence_graph.permitted_proposals else "rejected",
                {
                    "state": (
                        "pending_approval"
                        if governed.evidence_graph.permitted_proposals
                        else "not_proposed"
                    ),
                    "payload_digest": proposal.payload_digest if proposal else None,
                },
            ),
        )
        events: list[AuditEvent] = []
        previous_hash: str | None = None
        for index, (component, name, outcome, detail) in enumerate(raw, 1):
            body = {
                "sequence": index,
                "occurred_at": at,
                "actor": "resolveflow-service",
                "component": component,
                "event_name": name,
                "outcome": outcome,
                "correlation_id": run_id,
                "duration_ms": 0,
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
        return subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"
