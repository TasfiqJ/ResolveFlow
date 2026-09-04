from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.verify_public_snapshots import (
    _audit_event_hash,
    _run_snapshot_content_hash,
    _validate_run_snapshot,
    _validate_snapshot_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_HERO = ROOT / "data" / "published" / "hero-foundation-497eecf867ae8a1d.json"
CURRENT_HERO = ROOT / "data" / "published" / "hero-foundation.json"


def _historical_payload() -> dict[str, object]:
    payload = json.loads(HISTORICAL_HERO.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_verifier_accepts_published_timing_v1_without_rehashing_timing() -> None:
    payload = _historical_payload()

    snapshot = _validate_run_snapshot(payload)

    assert snapshot.timing is None
    assert _run_snapshot_content_hash(payload) == snapshot.content_hash


def test_verifier_accepts_current_hardened_fixture_snapshot() -> None:
    payload = json.loads(CURRENT_HERO.read_text(encoding="utf-8"))

    snapshot = _validate_run_snapshot(payload)

    assert snapshot.timing is not None
    assert snapshot.timing.schema_version == "1.1"
    assert _run_snapshot_content_hash(payload) == snapshot.content_hash


def test_verifier_keeps_current_timing_strict_and_outside_content_hash() -> None:
    payload = _historical_payload()
    payload["timing"] = {
        "schema_version": "1.1",
        "clock": "time.perf_counter_ns",
        "clock_resolution_ns": 100,
        "platform": "test platform",
        "unit": "milliseconds",
        "measured": True,
        "wall_clock_ms": 1.0,
        "provider_call_ms": 0.25,
        "provider_call_count": 1,
        "stages": [],
    }

    snapshot = _validate_run_snapshot(payload)

    assert snapshot.timing is not None
    assert snapshot.timing.schema_version == "1.1"
    assert _run_snapshot_content_hash(payload) == snapshot.content_hash


def test_verifier_rejects_malformed_historical_timing() -> None:
    payload = _historical_payload()
    timing = payload["timing"]
    assert isinstance(timing, dict)
    timing["wall_clock_ms"] = -1

    with pytest.raises(ValidationError):
        _validate_run_snapshot(payload)


def test_verifier_hashes_historical_audit_event_without_float_coercion() -> None:
    payload = _historical_payload()
    trace = payload["trace"]
    assert isinstance(trace, list)
    event = trace[0]
    assert isinstance(event, dict)
    assert event["duration_ms"] == 0

    assert _audit_event_hash(event) == event["event_hash"]


def test_verifier_rejects_resealed_snapshot_with_malformed_provider_hash() -> None:
    payload = json.loads(CURRENT_HERO.read_text(encoding="utf-8"))
    payload["provider_traces"][0]["request_hash"] = "not-a-sha256"
    payload["content_hash"] = _run_snapshot_content_hash(payload)

    snapshot = _validate_run_snapshot(payload)
    with pytest.raises(ValidationError, match="request_hash"):
        _validate_snapshot_evidence(snapshot)


def test_verifier_rejects_resealed_snapshot_with_invalid_graph_hash() -> None:
    payload = json.loads(CURRENT_HERO.read_text(encoding="utf-8"))
    payload["evidence_graph"]["graph_hash"] = "sha256:" + "0" * 64
    payload["response"]["graph_hash"] = "sha256:" + "0" * 64
    payload["content_hash"] = _run_snapshot_content_hash(payload)

    snapshot = _validate_run_snapshot(payload)
    with pytest.raises(ValueError, match="evidence graph hash"):
        _validate_snapshot_evidence(snapshot)
