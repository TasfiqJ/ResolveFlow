"""Build the completion-budget evidence bundle from committed run artifacts."""

from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "eval" / "results" / "completion-budget-study"
PUBLIC = ROOT / "apps" / "web" / "public" / "results" / "completion-budget-study"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    digest = _digest(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _rate(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    numerator = sum(1 for row in rows if row[key])
    return {
        "numerator": numerator,
        "denominator": len(rows),
        "percent": round(numerator / len(rows) * 100, 1) if rows else "unmeasured",
    }


def _build_rates(result: dict[str, Any]) -> dict[str, Any]:
    return {
        build: {
            "completion": _rate(
                [row for row in result["runs"] if row["build_id"] == build], "completed"
            ),
            "forbidden_retrieved": _rate(
                [row for row in result["runs"] if row["build_id"] == build],
                "forbidden_evidence_retrieved",
            ),
            "forbidden_exposed": _rate(
                [row for row in result["runs"] if row["build_id"] == build],
                "forbidden_evidence_exposed",
            ),
        }
        for build in result["builds"]
    }


def _historical_profile(
    row: dict[str, Any], snapshots_dir: Path
) -> dict[str, Any]:
    snapshot = _load(snapshots_dir / f"run-{row['run_id']}.json")
    calls: list[dict[str, Any]] = []
    evidence_seen = 0
    for sequence, trace in enumerate(snapshot["provider_traces"], start=1):
        pass_kind = trace["pass_kind"]
        if pass_kind == "evidence":
            stage = "evidence_pass" if evidence_seen == 0 else f"tool_round_{evidence_seen}"
            evidence_seen += 1
        elif pass_kind == "findings":
            stage = "repair"
        else:
            stage = "render"
        calls.append(
            {
                "sequence": sequence,
                "stage": stage,
                "pass_kind": pass_kind,
                "initiated_tool_round": bool(trace["tool_call_names"]),
                "input_tokens": trace["usage"]["input_tokens"],
                "output_tokens": trace["usage"]["output_tokens"],
                "total_tokens": (
                    trace["usage"]["input_tokens"] + trace["usage"]["output_tokens"]
                ),
                "status": trace["status"],
                "finish_reason": trace["finish_reason"],
                "safe_error_code": trace["safe_error_code"],
                "request_hash": trace["request_hash"],
                "response_hash": trace["response_hash"],
            }
        )
    render = next((call for call in calls if call["pass_kind"] == "structure"), None)
    return {
        "run_id": row["run_id"],
        "scenario_id": row["scenario_id"],
        "trial": row["trial"],
        "build_id": row["build_id"],
        "terminal_reason": row["terminal_reason"],
        "completed": row["completed"],
        "provider_calls_consumed": len(calls),
        "tool_rounds_used": sum(1 for call in calls if call["initiated_tool_round"]),
        "render_attempted": render is not None,
        "calls_to_render": render["sequence"] if render else None,
        "where_run_ended": calls[-1]["stage"] if calls else "before_provider_call",
        "provider_call_profile": calls,
        "run_content_hash": row["run_content_hash"],
    }


def _semantic_reasons(selection: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    claims = {item["claim_id"]: item for item in graph["claims"]}
    requested = set(selection["summary_claim_ids"]) | set(
        selection["recommended_step_claim_ids"]
    )
    if selection["route_claim_id"]:
        requested.add(selection["route_claim_id"])
    reasons: list[str] = []
    if selection["graph_hash"] != graph["graph_hash"]:
        reasons.append("graph_hash_mismatch")
    if not requested.issubset(claims):
        reasons.append("unknown_claim_id")
    if any(
        item in claims and claims[item]["status"] != "supported" for item in requested
    ):
        reasons.append("unsupported_claim_id")
    route_id = selection["route_claim_id"]
    if route_id and route_id in claims and claims[route_id]["kind"] != "route":
        reasons.append("route_not_route_kind")
    if not set(selection["unknown_ids"]).issubset(
        item["unknown_id"] for item in graph["unknowns"]
    ):
        reasons.append("unknown_unknown_id")
    if not set(selection["conflict_ids"]).issubset(
        item["conflict_id"] for item in graph["conflicts"]
    ):
        reasons.append("unknown_conflict_id")
    return reasons


def _render_failures(live: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for row in live["runs"]:
        failure = row.get("structured_response_failure")
        if not failure:
            continue
        snapshot = _load(STUDY / "after-live" / "runs" / f"run-{row['run_id']}.json")
        raw = failure["raw_model_output"]
        selection = json.loads(raw)
        failures.append(
            {
                "run_id": row["run_id"],
                "scenario_id": row["scenario_id"],
                "build_id": row["build_id"],
                "classification": "schema_valid_semantic_reference_invalid",
                "semantic_reasons": _semantic_reasons(selection, snapshot["evidence_graph"]),
                "raw_model_output": raw,
                "response_hash": failure["response_hash"],
                "finish_reason": failure["finish_reason"],
            }
        )
    requested_classes = (
        "truncation",
        "wrong_type",
        "missing_field",
        "prose_instead_of_json",
        "refusal",
    )
    return {
        "requested_taxonomy_counts_by_build": {
            build: {
                classification: sum(
                    1
                    for failure in failures
                    if failure["build_id"] == build
                    and failure["classification"] == classification
                )
                for classification in requested_classes
            }
            for build in BUILD_IDS
        },
        "observed_additional_class_counts_by_build": {
            build: {
                "schema_valid_semantic_reference_invalid": sum(
                    1 for failure in failures if failure["build_id"] == build
                )
            }
            for build in BUILD_IDS
        },
        "semantic_reason_counts_by_build": {
            build: dict(
                Counter(
                    reason
                    for failure in failures
                    if failure["build_id"] == build
                    for reason in failure["semantic_reasons"]
                )
            )
            for build in BUILD_IDS
        },
        "failures": failures,
        "fix": (
            "The render request now supplies field-specific allowed ID lists and "
            "explicitly forbids unsupported claims or a non-route claim in "
            "route_claim_id. No broader retry was added."
        ),
        "live_validation_after_fix": "not_completed_provider_rate_limit_binding",
        "fixture_validation_after_fix": "completed",
    }


BUILD_IDS = ("unsafe-v0", "guarded-v1")


def main() -> int:
    before_fixture_path = STUDY / "before-fixture" / "ab-summary-fixture.json"
    after_fixture_path = STUDY / "after-fixture" / "ab-summary-fixture.json"
    final_fixture_path = (
        STUDY / "after-render-contract-fixture" / "ab-summary-fixture.json"
    )
    live_path = STUDY / "after-live" / "ab-summary-cohere.json"
    ledger_path = STUDY / "after-live" / "provider-calls-cohere.json"
    projection_path = STUDY / "after-live" / "live-call-projection.json"
    historical_path = ROOT / "eval" / "results" / "ab-summary-cohere.json"
    historical_snapshots = ROOT / "eval" / "results" / "runs" / "cohere"
    live_snapshots = STUDY / "after-live" / "runs"

    before_fixture = _load(before_fixture_path)
    after_fixture = _load(after_fixture_path)
    final_fixture = _load(final_fixture_path)
    live = _load(live_path)
    ledger = _load(ledger_path)
    historical = _load(historical_path)
    corpus_hashes = sorted(
        {
            str(_load(path)["run_inputs"]["corpus"])
            for path in live_snapshots.glob("*.json")
        }
    )
    historical_runs = [
        _historical_profile(row, historical_snapshots) for row in historical["runs"]
    ]
    render_calls = [
        row["calls_to_render"] for row in historical_runs if row["calls_to_render"]
    ]
    round_budget_failures = [
        row
        for row in historical_runs
        if row["terminal_reason"] == "tool_round_budget_exhausted"
    ]

    live_terminal_counts = {
        build: dict(
            Counter(
                row["terminal_reason"]
                for row in live["runs"]
                if row["build_id"] == build
            )
        )
        for build in BUILD_IDS
    }
    report = {
        "schema": "resolveflow.completion-budget-study",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "methodology": {
            "os": "Windows",
            "duration_clock_source": "Python time.perf_counter",
            "wall_clock_source": "Python datetime.now().astimezone",
            "live_recorded_at": live["environment"]["recorded_at"],
            "live_generated_at": live["generated_at"],
            "python": live["environment"]["python"],
            "command_model": live["command_model"],
            "rerank_model": live["rerank_model"],
            "cached_embedding_model": live["embedding_model"],
            "observed_live_corpus_hashes": corpus_hashes,
        },
        "historical_published_live": {
            "source_path": str(historical_path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": _digest(historical_path),
            "rates": _build_rates(historical),
            "declared_budgets": historical["agent_budgets"],
            "internal_consistency_warning": (
                "The combined historical artifact declares one tool-round budget, "
                "but tool-round-budget terminal snapshots end on different observed "
                "round counts across trials. Treat its published completion rates as "
                "historical before values, not one clean controlled budget experiment."
            ),
        },
        "task_1_fixture_before": {
            "source_path": str(before_fixture_path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": _digest(before_fixture_path),
            "rates": _build_rates(before_fixture),
            "budgets": before_fixture["agent_budgets"],
            "median_calls_to_render": statistics.median(
                row["calls_to_render"] for row in before_fixture["runs"]
            ),
            "minimum_configured_provider_call_budget_for_median_render": statistics.median(
                row["calls_to_render"] for row in before_fixture["runs"]
            ),
            "incomplete_runs": [
                row["run_id"] for row in before_fixture["runs"] if not row["completed"]
            ],
            "runs": [
                {
                    "run_id": row["run_id"],
                    "scenario_id": row["scenario_id"],
                    "build_id": row["build_id"],
                    "provider_calls_consumed": row["provider_calls_consumed"],
                    "tool_rounds_used": row["tool_rounds_used"],
                    "calls_to_render": row["calls_to_render"],
                    "terminal_reason": row["terminal_reason"],
                    "provider_call_profile": row["provider_call_profile"],
                    "run_content_hash": row["run_content_hash"],
                }
                for row in before_fixture["runs"]
            ],
        },
        "historical_live_call_profile": {
            "median_calls_to_render_among_render_attempts": statistics.median(render_calls),
            "render_attempt_count": len(render_calls),
            "round_budget_failure_count": len(round_budget_failures),
            "observed_round_counts_at_round_budget_terminal": sorted(
                {row["tool_rounds_used"] for row in round_budget_failures}
            ),
            "runs": historical_runs,
        },
        "task_2_budget_change": {
            "before": before_fixture["agent_budgets"],
            "after": after_fixture["agent_budgets"],
            "justification": {
                "max_tool_rounds": (
                    "Historical live snapshots include a tool-round-budget terminal "
                    "on the fifth observed tool round; the new limit admits that "
                    "measured round but no unobserved sixth round."
                ),
                "max_provider_calls": (
                    "Historical render attempts have a measured median of six calls. "
                    "Eight calls cover five observed tool rounds, one findings call, "
                    "one bounded findings-repair call, and one reserved render call."
                ),
                "reserved_provider_calls_for_render": (
                    "The previous subtraction is now an explicit validated budget field."
                ),
            },
            "fixture_after_rates": _build_rates(after_fixture),
        },
        "task_3_structured_response_invalid": _render_failures(live),
        "task_4_live_confirmation": {
            "source_path": str(live_path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": _digest(live_path),
            "projection": _load(projection_path),
            "rates": _build_rates(live),
            "terminal_counts_by_build": live_terminal_counts,
            "api_usage": {
                "calls_by_endpoint": ledger["calls_by_endpoint"],
                "total_calls": ledger["total_calls"],
                "input_tokens": ledger["input_tokens"],
                "output_tokens": ledger["output_tokens"],
                "retry_calls": ledger["retry_calls"],
                "abort_guard_fired": ledger["total_calls"] >= ledger["max_calls"],
                "rate_limited_attempts": sum(
                    1 for record in ledger["records"] if record["status"] == "rate_limited"
                ),
            },
            "target_cleared": False,
            "next_binding_constraints": {
                "provider_rate_limit": sum(
                    1
                    for row in live["runs"]
                    if row["terminal_reason"] == "provider_error"
                ),
                "token_budget_exhausted": sum(
                    1
                    for row in live["runs"]
                    if row["terminal_reason"] == "token_budget_exhausted"
                ),
                "provider_finish_max_tokens": sum(
                    1
                    for row in live["runs"]
                    if row["terminal_reason"] == "provider_finish_max_tokens"
                ),
                "structured_response_invalid": sum(
                    1
                    for row in live["runs"]
                    if row["terminal_reason"] == "structured_response_invalid"
                ),
            },
        },
        "fixture_after_render_contract": {
            "source_path": str(final_fixture_path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": _digest(final_fixture_path),
            "rates": _build_rates(final_fixture),
            "structured_response_invalid": sum(
                1
                for row in final_fixture["runs"]
                if row["terminal_reason"] == "structured_response_invalid"
            ),
        },
        "artifact_sha256": {},
    }

    report_path = STUDY / "completion-budget-study.json"
    readme_path = STUDY / "README.md"
    _write_json(report_path, report)
    readme = f"""# ResolveFlow completion-budget study

This bundle preserves the old published live result, a zero-provider-call fixture
measurement before the budget change, the fixture rerun after the change, the
reduced-scope live confirmation, every invalid structure output, and the final
fixture validation after the render-contract correction.

The historical completion rates are retained as before-values, but their source
artifact combines trials whose observed tool-round terminals are inconsistent
with its single declared budget block. They are not a clean controlled baseline.

The new live run did not clear the completion target. No budget was raised after
that result. Persistent provider rate limits, token exhaustion, and semantic
graph-selection failures are published as the next binding constraints.

## Environment and reproduction

- Branch: `{report['branch']}`
- OS: Windows
- Duration clock: Python `time.perf_counter`
- Wall clock: Python `datetime.now().astimezone`
- Live recorded at: `{live['environment']['recorded_at']}`
- Live generated at: `{live['generated_at']}`
- Python: `{live['environment']['python']}`
- Command model: `{live['command_model']}`
- Rerank model: `{live['rerank_model']}`
- Cached embedding model: `{live['embedding_model']}`
- Observed live corpus hashes: `{', '.join(corpus_hashes)}`
- Live reproduction: `powershell -ExecutionPolicy Bypass -File eval/run-completion-live.ps1`
- Fixture before: `.venv-live\\Scripts\\python.exe -m resolveflow.eval.ab_cli`
  `--provider fixture --skip-dry-pass --repetitions 1`
  `--output eval\\results\\completion-budget-study\\before-fixture`
- Fixture after: `.venv-live\\Scripts\\python.exe -m resolveflow.eval.ab_cli`
  `--provider fixture --skip-dry-pass --repetitions 1`
  `--output eval\\results\\completion-budget-study\\after-fixture`
- Report: `.venv-live\\Scripts\\python.exe eval\\build_completion_budget_report.py`

Every top-level JSON and Markdown artifact has an adjacent SHA-256 sidecar. The
live call ledger records every attempt, retry, duration, status, request hash,
response hash, and provider-reported token count. No corpus embedding call was
performed in this task.
"""
    _write(readme_path, readme)

    raw_artifact_paths = (
        historical_path,
        before_fixture_path,
        after_fixture_path,
        final_fixture_path,
        live_path,
        ledger_path,
        projection_path,
        readme_path,
    )

    report["artifact_sha256"] = {
        str(path.relative_to(ROOT)).replace("\\", "/"): _digest(path)
        for path in raw_artifact_paths
    }
    _write_json(report_path, report)

    artifact_paths = (*raw_artifact_paths, report_path)
    for path in artifact_paths:
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{_digest(path)}  {path.name}\n", encoding="utf-8"
        )

    PUBLIC.mkdir(parents=True, exist_ok=True)
    public_artifacts = {
        report_path: "completion-budget-study.json",
        readme_path: "README.md",
        before_fixture_path: "fixture-before.json",
        after_fixture_path: "fixture-after-budget.json",
        final_fixture_path: "fixture-after-render-contract.json",
        live_path: "ab-summary-cohere.json",
        ledger_path: "provider-calls-cohere.json",
        projection_path: "live-call-projection.json",
    }
    for path, public_name in public_artifacts.items():
        public_path = PUBLIC / public_name
        public_path.write_bytes(path.read_bytes())
        (PUBLIC / f"{public_name}.sha256").write_text(
            f"{_digest(public_path)}  {public_name}\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
