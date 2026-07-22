from __future__ import annotations

from fastapi.testclient import TestClient
from resolveflow.api.main import app

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
