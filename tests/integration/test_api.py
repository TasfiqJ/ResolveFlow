from __future__ import annotations

from fastapi.testclient import TestClient
from resolveflow.api.main import action_store, app

client = TestClient(app)


def test_health_and_version_endpoints() -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    version = client.get("/version")
    assert version.status_code == 200
    assert version.json()["build_id"] == "foundation-v1"


def test_web_created_case_runs_the_canonical_path() -> None:
    response = client.post("/v1/cases", json={"scenario_id": "hero-payments-001"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["case"]["source_system"] == "web"
    assert payload["response"]["route"] == "Payments Platform"
    assert payload["action"]["state"] == "pending_approval"


def test_arbitrary_scenarios_are_not_accepted() -> None:
    response = client.post("/v1/cases", json={"scenario_id": "arbitrary"})
    assert response.status_code == 422


def test_action_api_requires_permission_and_exact_digest() -> None:
    action_store.clear()
    run = client.get("/v1/runs/run_hero_foundation_001").json()
    proposal_id = run["action"]["proposal_id"]
    digest = run["action"]["payload_digest"]
    denied = client.post(
        f"/v1/actions/{proposal_id}/approve",
        json={"payload_digest": digest},
    )
    assert denied.status_code == 403
    mismatch = client.post(
        f"/v1/actions/{proposal_id}/approve",
        json={"payload_digest": "sha256:" + "0" * 64},
        headers={"X-ResolveFlow-Permissions": "approve_jira"},
    )
    assert mismatch.status_code == 409
    approved = client.post(
        f"/v1/actions/{proposal_id}/approve",
        json={"payload_digest": digest},
        headers={"X-ResolveFlow-Permissions": "approve_jira"},
    )
    assert approved.status_code == 200
    assert approved.json()["proposal"]["state"] == "approved"


def test_trace_events_and_public_exports_are_available() -> None:
    events = client.get("/v1/runs/run_hero_foundation_001/events")
    assert events.status_code == 200
    assert len(events.json()) == 14
    assert events.json()[-1]["event_name"] == "proposal.created"
    trace = client.get("/v1/runs/run_hero_foundation_001/trace")
    assert trace.status_code == 200
    assert trace.json()["run_id"] == "run_hero_foundation_001"
    json_export = client.get("/v1/runs/run_hero_foundation_001/export.json")
    assert json_export.status_code == 200
    assert "export_checksum" in json_export.json()
    markdown = client.get("/v1/runs/run_hero_foundation_001/export.md")
    assert markdown.status_code == 200
    assert "## Timeline" in markdown.text
