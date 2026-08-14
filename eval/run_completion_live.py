"""Budget-projected live confirmation for the completion-rate correction."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resolveflow.eval.ab_cli import _build_harness
from resolveflow.eval.ab_runner import BUILD_IDS, EVAL_BUDGETS, run_ab
from resolveflow.eval.budget import BudgetExceeded
from resolveflow.eval.scenarios import all_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "eval" / "results" / "completion-budget-study" / "after-live"
HARD_ABORT_CALLS = 300
PROJECTION_CEILING = 250


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_bytes(rendered.encode("utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )


def _branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def main() -> int:
    scenarios = all_scenarios()
    benign = tuple(item for item in scenarios if item.kind == "benign")
    attacks = tuple(item for item in scenarios if item.kind == "attack")
    selected = benign[:3] + attacks
    dry_scenarios = (benign[0], attacks[0])

    dry_run_count = len(dry_scenarios) * len(BUILD_IDS)
    full_run_count = len(selected) * len(BUILD_IDS)
    projected_executions = dry_run_count + full_run_count
    projected_chat_calls = projected_executions * EVAL_BUDGETS.max_provider_calls
    projected_rerank_calls = projected_executions
    projected_total_calls = projected_chat_calls + projected_rerank_calls
    projection = {
        "schema": "resolveflow.completion-live-projection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": _branch(),
        "hard_abort_calls": HARD_ABORT_CALLS,
        "projection_ceiling": PROJECTION_CEILING,
        "agent_budgets": EVAL_BUDGETS.model_dump(mode="json"),
        "full_scenario_count_available": len(scenarios),
        "selected_scenario_count": len(selected),
        "selected_scenario_ids": [item.scenario_id for item in selected],
        "substitution": (
            "The full scenario set was reduced before live execution because its "
            "worst-case call projection exceeded the projection ceiling. All attack "
            "scenarios and the first three benign scenarios were retained; budgets "
            "were not reduced."
        ),
        "dry_run_count": dry_run_count,
        "full_run_count": full_run_count,
        "projected_execution_count": projected_executions,
        "projected_calls_by_endpoint": {
            "chat": projected_chat_calls,
            "rerank": projected_rerank_calls,
            "embed": "not_performed_cached_corpus_only",
        },
        "projected_total_calls": projected_total_calls,
        "basis": {
            "chat": "configured per-run hard ceiling measured and selected in Task 2",
            "rerank": "one observed rerank call per run execution",
            "retries": "not projected; remaining hard-cap headroom absorbs counted retries",
        },
    }
    projection_path = OUTPUT / "live-call-projection.json"
    _write_json(projection_path, projection)
    print(json.dumps(projection, indent=2))
    if projected_total_calls > PROJECTION_CEILING:
        print("projection still exceeds the live ceiling; aborting before provider access")
        return 4
    if projected_total_calls > HARD_ABORT_CALLS:
        print("projection exceeds the hard abort; aborting before provider access")
        return 4

    harness, client = _build_harness("cohere", HARD_ABORT_CALLS)
    assert client is not None
    try:
        before_dry = client.total_calls
        dry_result = run_ab(
            harness=harness,
            scenarios=dry_scenarios,
            output_dir=OUTPUT / "runs-dry",
        )
        after_dry = client.total_calls
        print(f"[dry-pass] calls consumed: {after_dry - before_dry}")
        print(client.summary_line())

        result = run_ab(
            harness=harness,
            scenarios=selected,
            output_dir=OUTPUT / "runs",
        )
    except BudgetExceeded:
        ledger = client.ledger().model_dump(mode="json")
        _write_json(OUTPUT / "provider-calls-cohere.json", ledger)
        raise

    ledger = client.ledger().model_dump(mode="json")
    result["projection"] = projection
    result["dry_pass"] = {
        "provider_calls": after_dry - before_dry,
        "scenario_ids": [item.scenario_id for item in dry_scenarios],
        "result_hash": dry_result["results_hash"],
    }
    result["budget"] = ledger
    result["environment"] = {
        "python": sys.version,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "branch": _branch(),
    }
    _write_json(OUTPUT / "ab-summary-cohere.json", result)
    _write_json(OUTPUT / "provider-calls-cohere.json", ledger)
    print(client.summary_line())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
