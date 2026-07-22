from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from resolveflow.agent.ports import AgentPort
from resolveflow.context.ports import ContextRepository
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import ActionBoundary, CanonicalCase, RunSnapshot, TraceEvent
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


class ResolveOrchestrator:
    """Shared production path used by web intake, fixtures, snapshots, and future Replay."""

    def __init__(self, context_repository: ContextRepository, agent: AgentPort) -> None:
        self.context_repository = context_repository
        self.agent = agent
        self.retriever = HybridRetriever(
            load_hero_corpus(),
            AuthorizationPolicy(),
            FixtureEmbeddingAdapter(),
            FixtureRerankAdapter(),
        )

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
        response = self.agent.resolve(case, context)
        events = self._events(run_id, case, context, retrieval.eligible_chunk_count)
        body = {
            "generated_at": datetime(2026, 7, 21, 0, 0, tzinfo=timezone.utc),
            "run_id": run_id,
            "commit": _git_sha(),
            "identity_snapshot": identity,
            "retrieval": retrieval,
            "case": case,
            "context": context,
            "response": response,
            "action": ActionBoundary(summary="Investigate PYM-431 after issuer-routing-v3 rollout"),
            "trace": events,
        }
        return RunSnapshot(**body, content_hash=checksum(body))

    @staticmethod
    def _events(
        run_id: str, case: CanonicalCase, context: tuple[object, ...], eligible_count: int
    ) -> tuple[TraceEvent, ...]:
        at = case.case_time
        raw = (
            ("intake", "case.normalized", "ok", {"source": case.source_system}),
            ("context", "context.enriched", "needs_information", {"operations": len(context)}),
            (
                "retrieval",
                "hybrid.authorized.completed",
                "ok",
                {"mode": "eligible_fixture", "eligible_count": eligible_count},
            ),
            ("agent", "fixture.response.loaded", "ok", {"provider": "recorded_fixture"}),
            ("verifier", "fixture.citations.checked", "ok", {"citations": 2}),
            ("actions", "proposal.created", "ok", {"state": "pending_approval"}),
        )
        return tuple(
            TraceEvent(
                sequence=index,
                event_id=f"evt_{index:03d}",
                occurred_at=at,
                actor="resolveflow-service",
                component=component,
                event_name=name,
                outcome=outcome,
                correlation_id=run_id,
                safe_detail=detail,
            )
            for index, (component, name, outcome, detail) in enumerate(raw, 1)
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
