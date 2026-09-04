from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.eval.snapshot_integrity import validate_snapshot_evidence
from resolveflow.evaluation.integrity import EvaluationIntegrityAudit
from resolveflow.evaluation.io import verify_bundle_file
from resolveflow.telemetry.stages import StageTiming
from resolveflow.verifier.models import EvidenceGraph


class _HistoricalRunTimingV1(FrozenModel):
    """Timing envelope emitted before high-resolution timing schema 1.1.

    Timing is deliberately outside a run's content hash, but published 1.0
    snapshots should still have their historical envelope shape validated before
    the current ``RunSnapshot`` model validates the content-bearing fields.
    """

    schema_version: Literal["1.0"]
    clock: Literal["time.monotonic"]
    unit: Literal["milliseconds"]
    measured: bool
    wall_clock_ms: float = Field(ge=0.0)
    provider_call_ms: float = Field(ge=0.0)
    provider_call_count: int = Field(ge=0)
    stages: tuple[StageTiming, ...]


def _validate_run_snapshot(payload: dict[str, Any]) -> RunSnapshot:
    """Validate current snapshots plus the immutable published timing 1.0 shape."""
    timing = payload.get("timing")
    if isinstance(timing, dict) and timing.get("schema_version") == "1.0":
        _HistoricalRunTimingV1.model_validate(timing)
        payload = {**payload, "timing": None}
    return RunSnapshot.model_validate(payload)


def _validate_snapshot_evidence(
    snapshot: RunSnapshot,
    payload: dict[str, Any] | None = None,
    *,
    allow_legacy_graph_hash: bool = False,
) -> EvidenceGraph:
    """Use the same nested-evidence validator as A/B recovery and publication."""

    return validate_snapshot_evidence(
        snapshot,
        payload if payload is not None else snapshot.model_dump(mode="json"),
        allow_legacy_graph_hash=allow_legacy_graph_hash,
    )


def _run_snapshot_content_hash(payload: dict[str, Any]) -> str:
    """Mirror the orchestrator's content fields without rewriting historical JSON."""
    excluded = {"content_hash"} | RunSnapshot.UNHASHED_FIELDS
    return checksum({key: value for key, value in payload.items() if key not in excluded})


def _audit_event_hash(payload: dict[str, Any]) -> str:
    """Verify an audit event using its immutable published numeric representation."""
    return checksum(
        {key: value for key, value in payload.items() if key not in {"event_id", "event_hash"}}
    )


def _verify_sha256_sidecar(path: Path) -> None:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.exists():
        raise SystemExit(f"missing checksum sidecar for {path}")
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise SystemExit(f"checksum sidecar mismatch for {path}")


def main() -> None:
    hero_path = Path("data/published/hero-foundation.json")
    hero_payload = json.loads(hero_path.read_text(encoding="utf-8"))
    hero = _validate_run_snapshot(hero_payload)
    _validate_snapshot_evidence(hero, hero_payload)
    if _run_snapshot_content_hash(hero_payload) != hero.content_hash:
        raise SystemExit("hero snapshot content hash mismatch")
    web_hero = Path("apps/web/public/snapshots/hero-foundation.json")
    if web_hero.read_bytes() != hero_path.read_bytes():
        raise SystemExit("web hero snapshot differs from canonical published snapshot")
    live_path = Path("data/published/hero-cohere-live.json")
    if live_path.exists():
        live_payload = json.loads(live_path.read_text(encoding="utf-8"))
        live = _validate_run_snapshot(live_payload)
        _validate_snapshot_evidence(live, live_payload, allow_legacy_graph_hash=True)
        if _run_snapshot_content_hash(live_payload) != live.content_hash:
            raise SystemExit("live hero snapshot content hash mismatch")
        if live.provenance != "live_provider" or live.response.provider != "cohere":
            raise SystemExit("live hero snapshot does not have live-provider provenance")
        if not live.provider_traces or not any(
            trace.get("usage", {}).get("input_tokens", 0) > 0 for trace in live.provider_traces
        ):
            raise SystemExit("live hero snapshot has no provider usage evidence")
        if (
            live.retrieval.embedding_model == "fixture-embed-v1"
            or live.retrieval.rerank_model == "fixture-rerank-v1"
        ):
            raise SystemExit("live hero snapshot used a fixture retrieval adapter")
        candidates = {item.chunk_id: item for item in live.retrieval.candidates}
        claims = {item.get("claim_id") for item in live.evidence_graph.get("claims", [])}
        if not live.response.citations:
            raise SystemExit("live hero snapshot has no verifier-accepted citation")
        for citation in live.response.citations:
            candidate = candidates.get(citation.source_id)
            if candidate is None or citation.claim_id not in claims:
                raise SystemExit("live citation does not close over a retrieved source and claim")
            if citation.excerpt not in candidate.content:
                raise SystemExit("live citation excerpt is not exact source text")
            required = {
                "citation_exists",
                "citation_authorized",
                "citation_version_valid",
                "citation_fresh",
                "citation_in_context",
                "citation_span_exact",
                "citation_supports_claim",
            }
            if not required.issubset(citation.verifier_codes):
                raise SystemExit("live citation did not pass every deterministic check")
        previous_hash: str | None = None
        for event, event_payload in zip(live.trace, live_payload["trace"], strict=True):
            if event.previous_event_hash != previous_hash:
                raise SystemExit("live hero audit chain link mismatch")
            if _audit_event_hash(event_payload) != event.event_hash:
                raise SystemExit("live hero audit event hash mismatch")
            previous_hash = event.event_hash
        web_live = Path("apps/web/public/snapshots/hero-cohere-live.json")
        if web_live.read_bytes() != live_path.read_bytes():
            raise SystemExit("web live hero snapshot differs from canonical published snapshot")
    result_path = Path("data/published/replay-development-result.json")
    verify_bundle_file(result_path)
    web_result = Path("apps/web/public/snapshots/replay-development-result.json")
    if web_result.read_bytes() != result_path.read_bytes():
        raise SystemExit("web result snapshot differs from canonical published result")
    audit_path = Path("data/published/evaluation-integrity-audit.json")
    audit = EvaluationIntegrityAudit.model_validate(
        json.loads(audit_path.read_text(encoding="utf-8"))
    )
    if checksum(audit.model_dump(mode="python", exclude={"checksum"})) != audit.checksum:
        raise SystemExit("evaluation integrity audit canonical checksum mismatch")
    if audit.security_matrix_full_replay_execution_count != len(audit.security_matrix_results):
        raise SystemExit("security matrix site count does not match per-cell JSON results")
    if audit.security_matrix_pass_count != sum(
        item.passed for item in audit.security_matrix_results
    ):
        raise SystemExit("security matrix pass count does not match per-cell JSON results")
    if audit.security_matrix_failure_count != sum(
        not item.passed for item in audit.security_matrix_results
    ):
        raise SystemExit("security matrix failure count does not match per-cell JSON results")
    if any(not item.passed and not item.failure_reasons for item in audit.security_matrix_results):
        raise SystemExit("security matrix contains an unexplained failing cell")
    expected_file_hash = audit_path.with_suffix(".json.sha256").read_text().split()[0]
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != expected_file_hash:
        raise SystemExit("evaluation integrity audit file checksum mismatch")
    web_audit = Path("apps/web/public/snapshots/evaluation-integrity-audit.json")
    if web_audit.read_bytes() != audit_path.read_bytes():
        raise SystemExit("web evaluation integrity audit differs from canonical artifact")
    canonical_ab = Path("eval/results/ab-site-cohere.json")
    if canonical_ab.exists():
        web_ab = Path("apps/web/public/snapshots/ab-site-cohere.json")
        web_current = Path("apps/web/public/snapshots/ab-site-current.json")
        for public_copy in (web_ab, web_current):
            if public_copy.read_bytes() != canonical_ab.read_bytes():
                raise SystemExit(f"{public_copy} differs from canonical Cohere A/B artifact")
            _verify_sha256_sidecar(public_copy)
    print(
        "Public snapshot integrity passed: recorded hero, optional live hero, Replay result, "
        "evaluation integrity, and Cohere A/B copies/checksums verified"
    )


if __name__ == "__main__":
    main()
