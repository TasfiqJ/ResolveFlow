from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import Field

from resolveflow import __version__
from resolveflow.actions.models import (
    ActionDecision,
    ActionProposal,
    ApprovalCommand,
    RejectionCommand,
)
from resolveflow.actions.service import ActionService
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.config import get_settings
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.models import CaseCreate, HealthResponse, RunSnapshot, VersionResponse
from resolveflow.evaluation.models import ResultBundle
from resolveflow.evaluation.runner import evaluate_manifest_pair
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator, _git_sha
from resolveflow.replay.io import manifest_path
from resolveflow.telemetry.export import export_run_json, export_run_markdown
from resolveflow.telemetry.projection import public_projection

app = FastAPI(title="ResolveFlow Replay API", version=__version__)
orchestrator = ResolveOrchestrator(FixtureContextRepository(), GovernedAgent(FixtureChatAdapter()))
action_service = ActionService()
action_store: dict[str, ActionProposal] = {}
replay_store: dict[str, ResultBundle] = {}


class ApprovalRequest(FrozenModel):
    payload_digest: str
    actor_id: str = "user_incident_commander_synthetic"


class RejectionRequest(FrozenModel):
    reason: str = Field(min_length=1, max_length=500)
    actor_id: str = "user_incident_commander_synthetic"


class ReplayRequest(FrozenModel):
    manifest_id: str = "replay-role-downgrade-001"
    baseline_build: str = "unsafe-v0"
    candidate_build: str = "guarded-v1"


def _fixture_proposal(proposal_id: str) -> ActionProposal:
    existing = action_store.get(proposal_id)
    if existing is not None:
        return existing
    orchestrator.run(canonical_hero_case())
    proposal = orchestrator.latest_proposal
    if proposal is None or proposal.proposal_id != proposal_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    now = datetime.now(timezone.utc)
    proposal = proposal.model_copy(
        update={"created_at": now, "expires_at": now + timedelta(hours=2)}
    )
    action_store[proposal.proposal_id] = proposal
    return proposal


def _permissions(raw: str | None) -> frozenset[str]:
    return frozenset(item.strip() for item in (raw or "").split(",") if item.strip())


@app.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    get_settings()
    return HealthResponse(status="ready")


@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(version=__version__, build_id=settings.build_id, commit=_git_sha())


@app.post("/v1/cases", response_model=RunSnapshot, status_code=201)
def create_case(request: CaseCreate) -> RunSnapshot:
    if request.scenario_id != "hero-payments-001":
        raise HTTPException(
            status_code=422, detail="Only predefined synthetic scenarios are accepted"
        )
    return orchestrator.run(canonical_hero_case())


@app.get("/v1/runs/run_hero_foundation_001", response_model=RunSnapshot)
def get_hero_run() -> RunSnapshot:
    return orchestrator.run(canonical_hero_case())


def _hero_run(run_id: str) -> RunSnapshot:
    if run_id != "run_hero_foundation_001":
        raise HTTPException(status_code=404, detail="Run not found")
    return orchestrator.run(canonical_hero_case())


@app.get("/v1/runs/{run_id}/events")
def get_run_events(run_id: str) -> list[dict[str, object]]:
    return [event.model_dump(mode="json") for event in _hero_run(run_id).trace]


@app.get("/v1/runs/{run_id}/trace")
def get_run_trace(
    run_id: str,
    projection: str = Query(default="public", pattern="^(public|maintainer)$"),
) -> dict[str, object]:
    snapshot = _hero_run(run_id)
    if projection == "public":
        return public_projection(snapshot)
    return snapshot.model_dump(mode="json")


@app.get("/v1/runs/{run_id}/export.json")
def get_run_json_export(run_id: str) -> Response:
    return Response(
        export_run_json(_hero_run(run_id), public=True),
        media_type="application/json",
    )


@app.get("/v1/runs/{run_id}/export.md")
def get_run_markdown_export(run_id: str) -> Response:
    return Response(
        export_run_markdown(_hero_run(run_id), public=True),
        media_type="text/markdown",
    )


def _public_replay_bundle() -> ResultBundle:
    bundle = evaluate_manifest_pair(manifest_path("replay-role-downgrade-001"))
    replay_store[bundle.bundle_id] = bundle
    return bundle


@app.post("/v1/replays", response_model=ResultBundle, status_code=201)
def create_replay(request: ReplayRequest) -> ResultBundle:
    if (
        request.manifest_id != "replay-role-downgrade-001"
        or request.baseline_build != "unsafe-v0"
        or request.candidate_build != "guarded-v1"
    ):
        raise HTTPException(status_code=422, detail="Only predefined Replay pairs are accepted")
    return _public_replay_bundle()


@app.get("/v1/replays/{replay_id}", response_model=ResultBundle)
def get_replay(replay_id: str) -> ResultBundle:
    bundle = replay_store.get(replay_id)
    if bundle is None:
        generated = _public_replay_bundle()
        if generated.bundle_id != replay_id:
            raise HTTPException(status_code=404, detail="Replay not found")
        bundle = generated
    return bundle


@app.get("/v1/releases/{build_id}")
def get_release(build_id: str) -> dict[str, object]:
    bundle = _public_replay_bundle()
    if build_id == "guarded-v1":
        result = bundle.candidate
    elif build_id == "unsafe-v0":
        result = bundle.baseline
    else:
        raise HTTPException(status_code=404, detail="Release result not found")
    return {
        "schema_version": "1.0",
        "build_id": build_id,
        "decision_scope": result.verdict.decision_scope,
        "publishable_as_final_release": False,
        "dataset_lock_status": bundle.dataset_lock_status,
        "verdict": result.verdict.model_dump(mode="json"),
        "bundle_id": bundle.bundle_id,
        "bundle_checksum": bundle.checksum,
    }


@app.get("/v1/actions/{proposal_id}", response_model=ActionProposal)
def get_action(proposal_id: str) -> ActionProposal:
    return _fixture_proposal(proposal_id)


@app.post("/v1/actions/{proposal_id}/approve", response_model=ActionDecision)
def approve_action(
    proposal_id: str,
    request: ApprovalRequest,
    x_resolveflow_permissions: str | None = Header(default=None),
) -> ActionDecision:
    proposal = _fixture_proposal(proposal_id)
    decision = action_service.approve(
        proposal,
        ApprovalCommand(
            proposal_id=proposal_id,
            payload_digest=request.payload_digest,
            actor_id=request.actor_id,
            permissions=_permissions(x_resolveflow_permissions),
        ),
        datetime.now(timezone.utc),
    )
    action_store[proposal_id] = decision.proposal
    if not decision.accepted:
        status = 403 if decision.code.startswith("denied_") else 409
        raise HTTPException(status_code=status, detail=decision.code)
    return decision


@app.post("/v1/actions/{proposal_id}/reject", response_model=ActionDecision)
def reject_action(
    proposal_id: str,
    request: RejectionRequest,
    x_resolveflow_permissions: str | None = Header(default=None),
) -> ActionDecision:
    proposal = _fixture_proposal(proposal_id)
    decision = action_service.reject(
        proposal,
        RejectionCommand(
            proposal_id=proposal_id,
            actor_id=request.actor_id,
            reason=request.reason,
            permissions=_permissions(x_resolveflow_permissions),
        ),
        datetime.now(timezone.utc),
    )
    action_store[proposal_id] = decision.proposal
    if not decision.accepted:
        status = 403 if decision.code.startswith("denied_") else 409
        raise HTTPException(status_code=status, detail=decision.code)
    return decision


def run() -> None:
    import uvicorn

    uvicorn.run("resolveflow.api.main:app", host="0.0.0.0", port=8000)
