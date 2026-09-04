from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.eval.publish import (
    _RESULT_HASH_FIELDS,
    RESULTS_DIR,
    _provider_snapshot_paths,
    _publication_commit,
    checksum_manifest,
    methodology,
    open_issues,
    reconcile_provider_telemetry,
    recovery_receipt_note,
    results_table,
)


def load_summary(provider: str) -> dict[str, Any]:
    return json.loads((RESULTS_DIR / f"ab-summary-{provider}.json").read_text(encoding="utf-8"))


def test_live_methodology_reports_the_current_bounded_evidence() -> None:
    report = methodology(load_summary("cohere"), "cohere")

    assert "post-fix live Cohere A/B: **32 runs**" in report
    assert "Total provider calls consumed: **233**" in report
    assert "required 4-run dry pass" in report
    assert "unsafe-v0 retrieved forbidden evidence in 16/16 runs" in report
    assert "guarded-v1 did so in 0/16" in report
    assert "separate earlier Embed v4 pass" in report
    assert "Rerank search-unit usage: **unavailable**" in report
    assert "Historical Embed token usage: **unavailable**" in report
    assert "quality metrics are **VOID**" in report
    assert "63 snapshots" in report
    assert "different execution identity" in report
    assert "Execution git state: `uncommitted`" in report
    assert "No live Cohere run has been performed" not in report


def test_fixture_methodology_is_scoped_to_the_fixture_artifact() -> None:
    report = methodology(load_summary("fixture"), "fixture")

    assert "provider-specific publication contains no live Cohere calls" in report
    assert "separately published live Cohere artifact" in report
    assert "No live Cohere run has been performed" not in report


def test_void_table_describes_low_completion_without_blaming_one_budget() -> None:
    table = results_table(load_summary("cohere"))

    assert "low-completion harness outcome" in table
    assert "reflect the agent's token ceiling" not in table


def test_open_issue_copy_names_repeated_variants_once() -> None:
    issues = open_issues(load_summary("cohere"))

    assert any("variant(s) b1, b2 were delivered" in issue for issue in issues)
    assert all("b1, b1" not in issue for issue in issues)


def _write_snapshot_set(root: Path) -> tuple[Path, Path]:
    canonical = load_summary("cohere")
    canonical.pop("recovered_from_snapshots", None)
    canonical["dry_pass"]["recovered"] = False
    summary = root / "ab-summary-test.json"
    runs = root / "runs"
    runs.mkdir()
    summary.write_text(json.dumps(canonical), encoding="utf-8")
    shutil.copyfile(RESULTS_DIR / "provider-calls-cohere.json", root / "provider-calls-cohere.json")
    for row in canonical["runs"]:
        run_id = row["run_id"]
        shutil.copyfile(
            RESULTS_DIR / "runs" / "cohere" / f"run-{run_id}.json",
            runs / f"run-{run_id}.json",
        )
    return summary, runs


def _reseal_snapshot_and_summary(summary: Path, victim: Path, payload: dict[str, Any]) -> None:
    """Reseal the outer envelopes so nested-integrity checks are the only guard."""

    typed_snapshot = RunSnapshot.model_validate(payload)
    payload["content_hash"] = checksum(
        typed_snapshot.model_dump(
            mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS
        )
    )
    victim.write_text(json.dumps(payload), encoding="utf-8")
    summary_payload = json.loads(summary.read_text(encoding="utf-8"))
    row = next(item for item in summary_payload["runs"] if item["run_id"] == payload["run_id"])
    row["run_content_hash"] = payload["content_hash"]
    summary_payload["results_hash"] = checksum(
        {field: summary_payload[field] for field in _RESULT_HASH_FIELDS}
    )
    summary.write_text(json.dumps(summary_payload), encoding="utf-8")


def test_publication_snapshot_set_must_equal_canonical_summary(tmp_path: Path) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    assert len(_provider_snapshot_paths(summary, runs)) == 32

    (runs / "run-unretained.json").write_text(
        json.dumps({"run_id": "unretained"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unexpected=.*run-unretained"):
        _provider_snapshot_paths(summary, runs)


def test_publication_snapshot_payload_id_must_match_filename_and_summary(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = sorted(runs.glob("*.json"))[-1]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["run_id"] = "different-run"
    victim.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="payload run_id does not match"):
        _provider_snapshot_paths(summary, runs)


def test_publication_recomputes_snapshot_content_hash(tmp_path: Path) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = sorted(runs.glob("*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["model_policy"] = "tampered-policy"
    victim.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="content_hash does not match its payload"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_snapshot_with_invalid_evidence_graph_hash(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = sorted(runs.glob("*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["evidence_graph"]["claims"][0]["text"] = "tampered nested claim"
    _reseal_snapshot_and_summary(summary, victim, payload)

    with pytest.raises(ValueError, match="evidence graph hash"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_snapshot_with_unbound_response(tmp_path: Path) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = sorted(runs.glob("*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["response"]["graph_hash"] = "sha256:" + "0" * 64
    _reseal_snapshot_and_summary(summary, victim, payload)

    with pytest.raises(ValueError, match="response is not bound"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_snapshot_with_impossible_tool_trace(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = next(
        path
        for path in sorted(runs.glob("*.json"))
        if json.loads(path.read_text(encoding="utf-8"))["tool_traces"]
    )
    payload = json.loads(victim.read_text(encoding="utf-8"))
    trace = payload["tool_traces"][0]
    trace["status"] = "ok"
    trace["authorization"] = "not_evaluated"
    trace["safe_error_code"] = None
    _reseal_snapshot_and_summary(summary, victim, payload)

    with pytest.raises(ValueError, match="tool trace.*authorization"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_snapshot_with_broken_audit_hash_chain(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    victim = sorted(runs.glob("*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["trace"][0]["safe_detail"]["tampered"] = True
    _reseal_snapshot_and_summary(summary, victim, payload)

    with pytest.raises(ValueError, match="audit event hash"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_snapshot_with_changed_frozen_case(tmp_path: Path) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    summary_payload = json.loads(summary.read_text(encoding="utf-8"))
    victim = sorted(runs.glob("*.json"))[0]
    snapshot_payload = json.loads(victim.read_text(encoding="utf-8"))
    snapshot_payload["case"]["raw_text"] = "arbitrary replacement case"
    typed_snapshot = RunSnapshot.model_validate(snapshot_payload)
    snapshot_payload["content_hash"] = checksum(
        typed_snapshot.model_dump(
            mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS
        )
    )
    victim.write_text(json.dumps(snapshot_payload), encoding="utf-8")
    row = next(
        item for item in summary_payload["runs"] if item["run_id"] == snapshot_payload["run_id"]
    )
    row["run_content_hash"] = snapshot_payload["content_hash"]
    summary_payload["results_hash"] = checksum(
        {field: summary_payload[field] for field in _RESULT_HASH_FIELDS}
    )
    summary.write_text(json.dumps(summary_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="case differs from the frozen scenario"):
        _provider_snapshot_paths(summary, runs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("policy_id", "alien-policy"),
        ("max_provider_calls", 1),
        ("max_total_tokens", 1),
        ("max_tool_rounds", 999),
        ("wall_clock_seconds", 1),
        ("tool_timeout_seconds", 999),
    ],
)
def test_publication_rejects_unbound_or_impossible_budget_metadata(
    tmp_path: Path, field: str, value: object
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["agent_budgets"][field] = value
    payload["results_hash"] = checksum({name: payload[name] for name in _RESULT_HASH_FIELDS})
    summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="budget|cap"):
        _provider_snapshot_paths(summary, runs)


@pytest.mark.parametrize("omitted", ["recovered_from_snapshots", "execution_provenance"])
def test_publication_requires_recovery_and_provenance_beside_excluded_snapshots(
    tmp_path: Path, omitted: str
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    excluded = tmp_path / "cohere-excluded-prior-invocation"
    excluded.mkdir()
    source = next(
        iter(sorted((RESULTS_DIR / "runs" / "cohere-excluded-prior-invocation").glob("run-*.json")))
    )
    shutil.copyfile(source, excluded / source.name)
    payload["execution_provenance"] = load_summary("cohere")["execution_provenance"]
    payload["recovered_from_snapshots"] = {
        "runs_dir": runs.as_posix(),
        "complete_trials_used": [1],
        "incomplete_trials_dropped": {},
        "snapshots_unmatched_to_a_scenario": 0,
        "excluded_snapshot_directory": excluded.as_posix(),
        "excluded_snapshot_count": 1,
        "note": recovery_receipt_note(
            repetitions=1,
            excluded_snapshot_count=1,
            provider_ledger_reconciled=True,
            dry_pass_runs=4,
        ),
    }
    payload["dry_pass"]["recovered"] = True
    payload.pop(omitted)
    summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="recovery|provenance"):
        _provider_snapshot_paths(summary, runs)


def test_publication_rejects_resealed_excluded_snapshot_with_broken_evidence(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    summary_payload = json.loads(summary.read_text(encoding="utf-8"))
    excluded = tmp_path / "cohere-excluded-prior-invocation"
    excluded.mkdir()
    source = next(
        path
        for path in sorted(
            (RESULTS_DIR / "runs" / "cohere-excluded-prior-invocation").glob("run-*.json")
        )
        if json.loads(path.read_text(encoding="utf-8"))["evidence_graph"]["claims"]
    )
    victim = excluded / source.name
    shutil.copyfile(source, victim)
    victim_payload = json.loads(victim.read_text(encoding="utf-8"))
    victim_payload["evidence_graph"]["claims"][0]["text"] = "tampered excluded claim"
    typed_snapshot = RunSnapshot.model_validate(victim_payload)
    victim_payload["content_hash"] = checksum(
        typed_snapshot.model_dump(
            mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS
        )
    )
    victim.write_text(json.dumps(victim_payload), encoding="utf-8")

    summary_payload["execution_provenance"] = load_summary("cohere")["execution_provenance"]
    summary_payload["recovered_from_snapshots"] = {
        "runs_dir": runs.as_posix(),
        "complete_trials_used": [1],
        "incomplete_trials_dropped": {},
        "snapshots_unmatched_to_a_scenario": 0,
        "excluded_snapshot_directory": excluded.as_posix(),
        "excluded_snapshot_count": 1,
        "note": recovery_receipt_note(
            repetitions=1,
            excluded_snapshot_count=1,
            provider_ledger_reconciled=True,
            dry_pass_runs=4,
        ),
    }
    summary_payload["dry_pass"]["recovered"] = True
    summary.write_text(json.dumps(summary_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="excluded snapshot.*invalid nested evidence"):
        _provider_snapshot_paths(summary, runs)


def test_publication_binds_snapshot_hash_to_summary_row(tmp_path: Path) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["runs"][0]["run_content_hash"] = "sha256:" + "0" * 64
    summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="content_hash does not match canonical summary"):
        _provider_snapshot_paths(summary, runs)


def test_publication_recomputes_aggregates_even_if_result_hash_is_resealed(
    tmp_path: Path,
) -> None:
    summary, runs = _write_snapshot_set(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["run_count"] = 999
    payload["scenario_count"] = 1
    payload["by_build"]["guarded-v1"]["runs"] = 999
    payload["results_hash"] = checksum({field: payload[field] for field in _RESULT_HASH_FIELDS})
    summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="aggregate .* does not match retained snapshots"):
        _provider_snapshot_paths(summary, runs)


def test_checksum_manifest_paths_are_posix_portable() -> None:
    manifest = checksum_manifest([RESULTS_DIR / "ab-summary-cohere.json"])

    assert "`eval/results/ab-summary-cohere.json`" in manifest
    assert "\\" not in manifest


def test_retained_ledger_reconciles_to_full_pass_plus_dry_pass() -> None:
    summary = load_summary("cohere")
    paths = _provider_snapshot_paths(
        RESULTS_DIR / "ab-summary-cohere.json", RESULTS_DIR / "runs" / "cohere"
    )
    ledger = json.loads((RESULTS_DIR / "provider-calls-cohere.json").read_text(encoding="utf-8"))
    validity = reconcile_provider_telemetry(
        [json.loads(path.read_text(encoding="utf-8")) for path in paths],
        ledger,
        dry_scenario_ids=set(summary["dry_pass"]["dry_scenarios"]),
    )

    assert validity["status"] == "VALID_INCLUDES_DRY_PASS"
    assert validity["reason_codes"] == []
    assert validity["retained_snapshot_observations"]["matched_chat_trace_count"] == 174
    assert validity["ledger_observations"]["dry_pass_record_count"] == 27
    assert validity["ledger_observations"]["published_run_record_count"] == 206
    assert validity["ledger_observations"]["reported_search_units"] is None
    assert validity["ledger_observations"]["search_unit_accounting"] == "legacy_unavailable"


def _canonical_telemetry() -> tuple[list[dict[str, Any]], dict[str, Any], set[str]]:
    summary = load_summary("cohere")
    paths = _provider_snapshot_paths(
        RESULTS_DIR / "ab-summary-cohere.json", RESULTS_DIR / "runs" / "cohere"
    )
    snapshots = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    ledger = json.loads((RESULTS_DIR / "provider-calls-cohere.json").read_text(encoding="utf-8"))
    return snapshots, ledger, set(summary["dry_pass"]["dry_scenarios"])


def _recompute_ledger_totals(ledger: dict[str, Any]) -> None:
    records = ledger["records"]
    dict_records = [record for record in records if isinstance(record, dict)]
    ledger["total_calls"] = len(records)
    ledger["calls_by_endpoint"] = dict(Counter(record.get("endpoint") for record in dict_records))
    ledger["input_tokens"] = sum(int(record.get("input_tokens") or 0) for record in dict_records)
    ledger["output_tokens"] = sum(int(record.get("output_tokens") or 0) for record in dict_records)
    ledger["search_units"] = sum(int(record.get("search_units") or 0) for record in dict_records)
    ledger["provider_call_ms"] = sum(
        float(record.get("duration_ms") or 0.0) for record in dict_records
    )
    ledger["throttle_sleep_ms"] = sum(
        float(record.get("throttle_sleep_ms") or 0.0) for record in dict_records
    )
    ledger["retry_calls"] = sum(
        1 for record in dict_records if record.get("retry_of_sequence") is not None
    )
    ledger.setdefault("max_calls", max(1, len(records)))
    ledger.setdefault("schema_version", "1.0")


def test_reconciliation_rejects_wrong_rerank_model() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    next(record for record in ledger["records"] if record["endpoint"] == "rerank")["model"] = (
        "wrong-rerank-model"
    )

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_rerank_calls_do_not_match_retained_snapshots" in validity["reason_codes"]


def test_reconciliation_rejects_calls_above_the_declared_hard_cap() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    ledger["max_calls"] = 1

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_total_calls_exceed_hard_cap" in validity["reason_codes"]


def test_reconciliation_rejects_rerank_record_without_request_hash() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    next(record for record in ledger["records"] if record["endpoint"] == "rerank").pop(
        "request_hash"
    )

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "provider_ledger_schema_is_invalid" in validity["reason_codes"]


def test_reconciliation_rejects_unknown_endpoint_even_when_totals_balance() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    next(record for record in ledger["records"] if record["endpoint"] == "rerank")["endpoint"] = (
        "embed"
    )
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_contains_unknown_endpoints" in validity["reason_codes"]


def test_reconciliation_rejects_malformed_ledger_record() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    ledger["records"].append("not-a-record")
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_contains_malformed_records" in validity["reason_codes"]


def test_reconciliation_rejects_dry_chat_with_unknown_build() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    full_hashes = {
        checksum({"id": str(trace["response_id"])})
        for snapshot in snapshots
        for trace in snapshot["provider_traces"]
    }
    extra = next(
        record
        for record in ledger["records"]
        if record["endpoint"] == "chat" and record["response_hash"] not in full_hashes
    )
    extra["build_id"] = "alien-build"

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_contains_unknown_scenario_or_build" in validity["reason_codes"]


def test_reconciliation_binds_chat_durations_to_snapshot_traces() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    for record in ledger["records"]:
        record["duration_ms"] = 0.0
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_chat_durations_do_not_match_retained_snapshots" in validity["reason_codes"]


def test_reconciliation_rejects_non_ok_terminal_chat_with_a_response() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    next(
        record
        for record in reversed(ledger["records"])
        if record["endpoint"] == "chat" and record["response_hash"] is not None
    )["status"] = "error"

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_contains_invalid_terminal_chat_status" in validity["reason_codes"]


def test_reconciliation_requires_chat_coverage_for_every_dry_cell() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    full_hashes = {
        checksum({"id": str(trace["response_id"])})
        for snapshot in snapshots
        for trace in snapshot["provider_traces"]
    }
    ledger["records"] = [
        record
        for record in ledger["records"]
        if record["endpoint"] != "chat" or record["response_hash"] in full_hashes
    ]
    for sequence, record in enumerate(ledger["records"], start=1):
        record["sequence"] = sequence
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_dry_pass_chat_coverage_is_incomplete" in validity["reason_codes"]


def test_reconciliation_rejects_an_unsuccessful_terminal_dry_chat() -> None:
    snapshots, ledger, dry_ids = _canonical_telemetry()
    full_hashes = {
        checksum({"id": str(trace["response_id"])})
        for snapshot in snapshots
        for trace in snapshot["provider_traces"]
    }
    extra = next(
        record
        for record in ledger["records"]
        if record["endpoint"] == "chat" and record["response_hash"] not in full_hashes
    )
    extra.update(
        {
            "status": "error",
            "response_hash": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "error_code": "SyntheticDryFailure",
        }
    )
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger, dry_scenario_ids=dry_ids)

    assert validity["valid"] is False
    assert "ledger_contains_unsuccessful_terminal_dry_chat_calls" in validity["reason_codes"]


def test_reconciliation_uses_transport_identity_not_post_validation_status() -> None:
    snapshots = [
        {
            "scenario_id": "scenario-a",
            "build_id": "guarded-v1",
            "provider_traces": [
                {
                    "response_id": "response-1",
                    "response_hash": checksum("raw-provider-shape"),
                    "status": "malformed",
                    "model": "command-a-plus-05-2026",
                    "usage": {"input_tokens": 3, "output_tokens": 2},
                    "duration_ms": 4.0,
                }
            ],
            "retrieval": {
                "rerank_model": "rerank-v4.0-fast",
                "rerank_payload_checksum": checksum("payload"),
            },
        }
    ]
    ledger = {
        "records": [
            {
                "sequence": 1,
                "attempt": 1,
                "scenario_id": "scenario-a",
                "build_id": "guarded-v1",
                "endpoint": "chat",
                "request_hash": checksum("chat-request"),
                "response_hash": checksum({"id": "response-1"}),
                "status": "ok",
                "model": "command-a-plus-05-2026",
                "input_tokens": 3,
                "output_tokens": 2,
                "duration_ms": 4.0,
                "throttle_sleep_ms": 0.0,
                "retry_of_sequence": None,
            },
            {
                "sequence": 2,
                "attempt": 1,
                "scenario_id": "scenario-a",
                "build_id": "guarded-v1",
                "endpoint": "rerank",
                "request_hash": checksum("rerank-request"),
                "response_hash": checksum("rerank"),
                "status": "ok",
                "model": "rerank-v4.0-fast",
                "input_tokens": 0,
                "output_tokens": 0,
                "duration_ms": 1.0,
                "throttle_sleep_ms": 0.0,
                "retry_of_sequence": None,
            },
        ],
        "total_calls": 2,
        "calls_by_endpoint": {"chat": 1, "rerank": 1},
        "input_tokens": 3,
        "output_tokens": 2,
        "provider_call_ms": 5.0,
        "throttle_sleep_ms": 0.0,
        "retry_calls": 0,
        "max_calls": 2,
        "schema_version": "1.0",
    }

    assert reconcile_provider_telemetry(snapshots, ledger)["valid"] is True


@pytest.mark.parametrize("retry_endpoint", ["chat", "rerank"])
def test_reconciliation_accepts_a_valid_successful_retry_chain(
    retry_endpoint: str,
) -> None:
    snapshots = [
        {
            "scenario_id": "scenario-a",
            "build_id": "guarded-v1",
            "provider_traces": [
                {
                    "response_id": "response-1",
                    "model": "command-a-plus-05-2026",
                    "usage": {"input_tokens": 3, "output_tokens": 2},
                    "duration_ms": 3.0,
                }
            ],
            "retrieval": {
                "rerank_model": "rerank-v4.0-fast",
                "rerank_payload_checksum": checksum("payload"),
            },
        }
    ]
    chat_success = {
        "scenario_id": "scenario-a",
        "build_id": "guarded-v1",
        "endpoint": "chat",
        "request_hash": checksum("chat-request"),
        "response_hash": checksum({"id": "response-1"}),
        "status": "ok",
        "model": "command-a-plus-05-2026",
        "input_tokens": 3,
        "output_tokens": 2,
        "duration_ms": 1.0,
        "throttle_sleep_ms": 0.0,
    }
    rerank_success = {
        "scenario_id": "scenario-a",
        "build_id": "guarded-v1",
        "endpoint": "rerank",
        "request_hash": checksum("rerank-request"),
        "response_hash": checksum("rerank-response"),
        "status": "ok",
        "model": "rerank-v4.0-fast",
        "input_tokens": 0,
        "output_tokens": 0,
        "duration_ms": 1.0,
        "throttle_sleep_ms": 0.0,
    }
    successes = {"chat": chat_success, "rerank": rerank_success}
    records: list[dict[str, Any]] = []
    for endpoint in ("chat", "rerank"):
        success = deepcopy(successes[endpoint])
        if endpoint == retry_endpoint:
            root_sequence = len(records) + 1
            failed = deepcopy(success)
            failed.update(
                {
                    "sequence": root_sequence,
                    "attempt": 1,
                    "retry_of_sequence": None,
                    "response_hash": None,
                    "status": "rate_limited",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "duration_ms": 0.5,
                    "error_code": "TooManyRequestsError",
                }
            )
            records.append(failed)
            success.update(
                {
                    "sequence": root_sequence + 1,
                    "attempt": 2,
                    "retry_of_sequence": root_sequence,
                }
            )
        else:
            success.update(
                {
                    "sequence": len(records) + 1,
                    "attempt": 1,
                    "retry_of_sequence": None,
                }
            )
        records.append(success)
    ledger: dict[str, Any] = {"records": records}
    _recompute_ledger_totals(ledger)

    validity = reconcile_provider_telemetry(snapshots, ledger)

    assert validity["valid"] is True
    assert validity["status"] == "VALID_TOTALS_RETRY_SPLIT_UNATTRIBUTED"
    assert validity["ledger_observations"]["record_count"] == 3
    assert validity["ledger_observations"]["call_split_attribution"].startswith("unattributed")


def test_publication_commit_always_records_the_current_projection_commit(tmp_path: Path) -> None:
    site = tmp_path / "site.json"
    site.write_text(
        json.dumps({"results_hash": "sha256:same", "publication_base_commit": "old"}),
        encoding="utf-8",
    )

    assert _publication_commit({"results_hash": "sha256:same"}, site, "current") == "current"
    assert _publication_commit({"results_hash": "sha256:new"}, site, "current") == "current"


def test_results_summary_hash_register_matches_current_artifacts() -> None:
    repo_root = RESULTS_DIR.parents[1]
    report = (repo_root / "docs" / "RESULTS-SUMMARY.md").read_text(encoding="utf-8")
    registered = (
        "eval/results/ab-summary-cohere.json",
        "eval/results/ab-site-cohere.json",
        "eval/results/provider-calls-cohere.json",
        "eval/results/detector-eval.md",
        "eval/results/detector-eval.json",
        "eval/results/embedding-separation.md",
        "eval/results/embedding-separation.json",
        "eval/results/SHA256SUMS-cohere.md",
    )

    for relative_path in registered:
        digest = hashlib.sha256((repo_root / relative_path).read_bytes()).hexdigest()
        assert f"`{relative_path}` —\n  `{digest}`" in report
