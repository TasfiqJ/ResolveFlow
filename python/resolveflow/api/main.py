from __future__ import annotations

from fastapi import FastAPI, HTTPException

from resolveflow import __version__
from resolveflow.agent.fixture import FixtureAgent
from resolveflow.config import get_settings
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.models import CaseCreate, HealthResponse, RunSnapshot, VersionResponse
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator, _git_sha

app = FastAPI(title="ResolveFlow Replay API", version=__version__)
orchestrator = ResolveOrchestrator(FixtureContextRepository(), FixtureAgent())


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


def run() -> None:
    import uvicorn

    uvicorn.run("resolveflow.api.main:app", host="0.0.0.0", port=8000)
