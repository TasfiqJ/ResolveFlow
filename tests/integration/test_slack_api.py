from __future__ import annotations

import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from resolveflow.api.main import app, slack_audit_events, slack_store
from resolveflow.config import get_settings


def sign(secret: str, timestamp: str, body: bytes) -> str:
    base = b"v0:" + timestamp.encode() + b":" + body
    return "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()


def test_verified_delivery_is_queued_and_deduplicated(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("RESOLVEFLOW_SLACK_SIGNING_SECRET", "fixture-secret")
    get_settings.cache_clear()
    slack_store.cases_by_delivery.clear()
    timestamp = str(int(time.time()))
    body = json.dumps(
        {
            "event_id": "Ev-integration-1",
            "event_time": int(timestamp),
            "team_id": "T_SYNTHETIC",
            "event": {"event_ts": "1.0", "text": "Synthetic PYM-431 report"},
        }
    ).encode()
    headers = {
        "x-slack-request-timestamp": timestamp,
        "x-slack-signature": sign("fixture-secret", timestamp, body),
        "content-type": "application/json",
    }
    client = TestClient(app)
    first = client.post("/integrations/slack/events", content=body, headers=headers)
    second = client.post("/integrations/slack/events", content=body, headers=headers)
    assert first.status_code == 200
    assert first.json()["acknowledgement"] == "queued"
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    get_settings.cache_clear()


def test_invalid_signature_is_audited(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("RESOLVEFLOW_SLACK_SIGNING_SECRET", "fixture-secret")
    get_settings.cache_clear()
    timestamp = str(int(time.time()))
    response = TestClient(app).post(
        "/integrations/slack/events",
        content=b"{}",
        headers={"x-slack-request-timestamp": timestamp, "x-slack-signature": "v0=invalid"},
    )
    assert response.status_code == 401
    assert slack_audit_events[-1]["event_name"] == "slack.request.rejected"
    get_settings.cache_clear()
