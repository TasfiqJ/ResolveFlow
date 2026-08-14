"""Rebuild an A/B summary from run snapshots left on disk by an interrupted run.

A live run that hits the call cap partway through has still spent real money and,
because snapshots are written as each run completes, has left every finished run
on disk. Throwing that away and re-running would spend the budget twice. This
module reconstructs the published summary from the committed snapshots, using the
exact same aggregation the live harness uses, and keeps **only whole
repetitions** so the result is never a lopsided partial trial.

It spends zero provider calls. Metrics are recomputed from each snapshot and the
corpus, identically to a live run -- ``RunMetrics`` reads retrieval candidates,
citations, ACLs and corpus text, never embeddings -- so the numbers are the same
ones the live run would have published for those trials. The real provider-call
ledger written at crash time is attached unchanged, so the artifact still ships
with a full account of what was spent.

    python -m resolveflow.eval.recover_ab --provider cohere
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resolveflow.domain.models import RunSnapshot
from resolveflow.eval.ab_runner import (
    BUILD_IDS,
    EVAL_BUDGETS,
    RunMetrics,
    build_result,
)
from resolveflow.eval.corpus import build_eval_corpus
from resolveflow.eval.scenarios import EvalScenario, all_scenarios
from resolveflow.ingestion.fixtures import ROOT
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter

RESULTS_DIR = ROOT / "eval" / "results"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _trial_of(run_id: str, build_id: str) -> int:
    """Trial 1 has no suffix; later trials end in ``_t<N>``."""
    tail = run_id.rsplit(f"_{build_id}", 1)[-1]
    if tail.startswith("_t") and tail[2:].isdigit():
        return int(tail[2:])
    return 1


def recover(provider: str, runs_dir: Path) -> dict[str, Any]:
    scenarios = all_scenarios()
    by_id: dict[str, EvalScenario] = {s.scenario_id: s for s in scenarios}
    expected_per_trial = len(scenarios) * len(BUILD_IDS)

    snapshot_paths = sorted(runs_dir.glob("run-*.json"))
    if not snapshot_paths:
        raise SystemExit(f"no run snapshots under {runs_dir}")

    # Group snapshots by trial and keep only trials that are complete, so a
    # half-finished repetition can never skew the aggregate.
    by_trial: dict[int, list[tuple[EvalScenario, str, RunSnapshot]]] = defaultdict(list)
    skipped_unknown = 0
    for path in snapshot_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        snapshot = RunSnapshot.model_validate(data)
        scenario = by_id.get(snapshot.scenario_id)
        if scenario is None:
            skipped_unknown += 1
            continue
        trial = _trial_of(snapshot.run_id, snapshot.build_id)
        by_trial[trial].append((scenario, snapshot.build_id, snapshot))

    complete_trials = sorted(
        trial for trial, items in by_trial.items() if len(items) == expected_per_trial
    )
    incomplete = {
        trial: len(items)
        for trial, items in sorted(by_trial.items())
        if len(items) != expected_per_trial
    }
    if not complete_trials:
        raise SystemExit(
            "no complete repetition on disk: "
            + ", ".join(f"trial {t}={n}/{expected_per_trial}" for t, n in incomplete.items())
        )

    # Rebuild the corpus per attack artifact once; RunMetrics needs corpus text
    # and ACLs, not vectors, so the fixture embedder is fine here.
    corpus_cache: dict[str | None, Any] = {}

    def corpus_for(scenario: EvalScenario) -> Any:
        key = scenario.attack_artifact_id
        if key not in corpus_cache:
            corpus_cache[key] = build_eval_corpus(
                embedder=FixtureEmbeddingAdapter(), attack_artifact_id=key
            )
        return corpus_cache[key]

    rows: list[dict[str, Any]] = []
    snapshots: list[RunSnapshot] = []
    for trial in complete_trials:
        for scenario, build_id, snapshot in by_trial[trial]:
            metrics = RunMetrics(scenario, build_id, snapshot, corpus_for(scenario))
            metrics.trial = trial
            rows.append(metrics.as_dict())
            snapshots.append(snapshot)

    generated_at = datetime.now(timezone.utc)
    result = build_result(
        rows=rows,
        snapshots=snapshots,
        scenarios=scenarios,
        provider=provider,
        command_model="command-a-plus-05-2026",
        rerank_model="rerank-v4.0-fast",
        embedding_model="embed-v4.0",
        agent_budgets=EVAL_BUDGETS,
        generated_at=generated_at,
        repetitions=len(complete_trials),
        output_dir=None,
    )

    # Attach the real ledger written at crash time, unchanged, plus a note that
    # this summary was reconstructed and what it dropped.
    ledger_path = RESULTS_DIR / f"provider-calls-{provider}.json"
    if ledger_path.exists():
        result["budget"] = json.loads(ledger_path.read_text(encoding="utf-8"))
    result["recovered_from_snapshots"] = {
        "runs_dir": _rel(runs_dir),
        "complete_trials_used": complete_trials,
        "incomplete_trials_dropped": incomplete,
        "snapshots_unmatched_to_a_scenario": skipped_unknown,
        "note": (
            "This summary was rebuilt from run snapshots left on disk by a run that "
            "hit its call cap before finishing. Only whole repetitions are included. "
            "Metrics were recomputed from the snapshots exactly as the live harness "
            "computes them; the attached ledger is the real provider-call record "
            "written when the run stopped. Zero provider calls were spent rebuilding "
            "this."
        ),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover an A/B summary from snapshots.")
    parser.add_argument("--provider", choices=("fixture", "cohere"), default="cohere")
    parser.add_argument("--runs-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    runs_dir = args.runs_dir or (RESULTS_DIR / "runs" / args.provider)
    result = recover(args.provider, runs_dir)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"ab-summary-{args.provider}.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rec = result["recovered_from_snapshots"]
    print(f"[recover] complete trials used: {rec['complete_trials_used']}")
    print(f"[recover] incomplete trials dropped: {rec['incomplete_trials_dropped']}")
    print(f"[recover] runs aggregated: {result['run_count']} ({result['repetitions']} rep(s))")
    print(f"[recover] wrote {out}")
    print(f"[recover] now run: python -m resolveflow.eval.publish {args.provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
