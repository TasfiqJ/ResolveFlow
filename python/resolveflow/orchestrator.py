from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from resolveflow.actions.models import ActionProposal
from resolveflow.actions.service import ActionService, fixture_now
from resolveflow.agent.security import score_forbidden_effects
from resolveflow.agent.service import GovernedAgent, GovernedRunResult
from resolveflow.context.ports import ContextRepository
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import ActionBoundary, AuditEvent, CanonicalCase, RunSnapshot
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


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

    def run(self, case: CanonicalCase) -> RunSnapshot:
        run_id = "run_hero_foundation_001"
        context = self.context_repository.enrich(case)
        identity = make_identity_snapshot(
            tenant_id=case.tenant_id,
            actor_id="user_incident_commander_synthetic",
            role="incident_commander",
            region=case.region,
            case_time=case.case_time,
        )
        retrieval = self.retriever.retrieve(case.raw_text, identity)
        governed = self.agent.resolve(
            run_id=run_id,
            case=case,
            context=context,
            identity=identity,
            retrieval=retrieval,
            corpus=self.corpus,
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
            run_id, case, context, retrieval.eligible_chunk_count, governed, proposal
        )
        body = {
            "generated_at": datetime(2026, 7, 21, 0, 0, tzinfo=timezone.utc),
            "run_id": run_id,
            "build_id": "governed-fixture-v1",
            "commit": _git_sha(),
            "model_policy": self.agent.budgets.policy_id,
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
        }
        return RunSnapshot(**body, content_hash=checksum(body))

    @staticmethod
    def _events(
        run_id: str,
        case: CanonicalCase,
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
                {"role": "incident_commander", "region": case.region},
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
                "evidence_graph.verified",
                "ok" if not governed.response.needs_review else "needs_information",
                {
                    "claims": len(governed.evidence_graph.claims),
                    "graph_hash": governed.evidence_graph.graph_hash,
                    "route": governed.response.route,
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
                "versions": {"schema": "1.0", "build": "governed-fixture-v1"},
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
