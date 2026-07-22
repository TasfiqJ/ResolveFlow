from __future__ import annotations

from fastapi.testclient import TestClient
from resolveflow.api.main import app
from resolveflow.config import get_settings


def test_disabled_live_api_returns_complete_recorded_fallback() -> None:
    get_settings.cache_clear()
    response = TestClient(app).post(
        "/v1/public/live",
        json={
            "case_id": "hero-payments-001",
            "mutation": "baseline",
            "session_id": "session-fixture-001",
        },
    )
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "public_live_kill_switch_active"
    assert detail["fallback"] == "/snapshots/hero-foundation.json"


def test_arbitrary_public_case_is_rejected_even_if_limiter_is_disabled() -> None:
    # Configuration validation prevents public-live enablement without a provider key;
    # the allowlist itself is covered independently without creating a live client.
    response = TestClient(app).post(
        "/v1/public/live",
        json={
            "case_id": "arbitrary",
            "mutation": "baseline",
            "session_id": "session-fixture-002",
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"]["fallback"].endswith("hero-foundation.json")
