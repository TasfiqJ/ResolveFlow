"""Entry point for the A/B evaluation.

Order of operations is fixed and not negotiable by flag:

1. a 2-scenario dry pass that reports calls consumed per scenario,
2. an extrapolation to the full 16-scenario run,
3. a hard stop if the projection exceeds the cap,
4. only then the full run.

In fixture mode the dry pass still runs; it simply reports zero provider calls,
which is the correct measurement for that provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resolveflow.eval.ab_runner import ABHarness, run_ab
from resolveflow.eval.budget import DEFAULT_MAX_CALLS, BudgetedCohereClient, BudgetExceeded
from resolveflow.eval.corpus import ATTACK_MANIFEST, BASE_MANIFEST, load_attack_variants
from resolveflow.eval.embed_corpus import CACHE_PATH
from resolveflow.eval.embedding_cache import CachedEmbeddingAdapter
from resolveflow.eval.scenarios import all_scenarios
from resolveflow.ingestion.fixtures import ROOT, corpus_profile

RESULTS_DIR = ROOT / "eval" / "results"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_harness(provider: str, max_calls: int) -> tuple[ABHarness, BudgetedCohereClient | None]:
    if provider == "fixture":
        return ABHarness(provider="fixture"), None
    api_key = os.environ.get("RESOLVEFLOW_COHERE_API_KEY")
    if not api_key:
        raise SystemExit("RESOLVEFLOW_COHERE_API_KEY is not set; refusing to run live")
    if not CACHE_PATH.exists():
        raise SystemExit(
            f"embedding cache missing at {CACHE_PATH}; run "
            f"`python -m resolveflow.eval.embed_corpus` first"
        )
    import cohere

    client = BudgetedCohereClient(cohere.ClientV2(api_key=api_key), max_calls=max_calls)
    # allow_provider=False: the A/B must not be able to spend an embed call. Any
    # cache miss is a setup error and should stop the run, not quietly bill it.
    embedder = CachedEmbeddingAdapter(CACHE_PATH, client=None, allow_provider=False)
    return (
        ABHarness(provider="cohere", budgeted_client=client, embedder=embedder),
        client,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ResolveFlow guarded/unguarded A/B.")
    parser.add_argument("--provider", choices=("fixture", "cohere"), default="fixture")
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
    parser.add_argument("--output", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help=(
            "trials per scenario per build. Auto-scaled down if the dry-pass "
            "projection would exceed --max-calls."
        ),
    )
    parser.add_argument(
        "--skip-dry-pass",
        action="store_true",
        help="only permitted in fixture mode, where no call can be spent",
    )
    args = parser.parse_args(argv)

    if args.skip_dry_pass and args.provider != "fixture":
        raise SystemExit("the dry pass cannot be skipped in live mode")

    scenarios = all_scenarios()
    harness, client = _build_harness(args.provider, args.max_calls)
    output_dir = args.output
    # Per-provider directory. Both providers previously wrote run-<run_id>.json
    # into one folder, so a fixture run silently overwrote a live run's snapshots
    # and the checksum manifest then listed fixture files as live artifacts.
    runs_dir = output_dir / "runs" / args.provider

    repetitions = max(1, args.repetitions)
    dry_report: dict[str, Any] | None = None
    if not args.skip_dry_pass:
        # One benign and one attack scenario: the two shapes have different call
        # profiles, so averaging one of each is the honest basis for extrapolation.
        dry_scenarios = (scenarios[0], scenarios[8])
        print(f"[dry-pass] scenarios: {[s.scenario_id for s in dry_scenarios]}")
        before = client.total_calls if client else 0
        per_scenario: list[dict[str, Any]] = []

        def _after(scenario: Any, _rows: list[dict[str, Any]]) -> None:
            nonlocal before
            now = client.total_calls if client else 0
            per_scenario.append({"scenario_id": scenario.scenario_id, "calls": now - before})
            print(f"[dry-pass] {scenario.scenario_id}: {now - before} provider calls (both builds)")
            if client:
                print(f"           {client.summary_line()}")
            before = now

        try:
            run_ab(harness=harness, scenarios=dry_scenarios, output_dir=None, on_scenario=_after)
        except BudgetExceeded as exc:
            print(f"[abort] {exc}", file=sys.stderr)
            return 3

        dry_calls = sum(item["calls"] for item in per_scenario)
        per_scenario_mean = dry_calls / len(dry_scenarios) if dry_scenarios else 0.0

        # Auto-scaling. Take the highest repetition count whose projection fits
        # under the cap. If even one repetition does not fit, drop the benign
        # scenarios and keep the attacks -- and record the substitution, because
        # a run that silently changed its own scope is not reproducible.
        requested_repetitions = max(1, args.repetitions)
        scaling_note: str | None = None
        while repetitions > 1 and (
            per_scenario_mean * len(scenarios) * repetitions + dry_calls > args.max_calls
        ):
            repetitions -= 1
        if per_scenario_mean * len(scenarios) * repetitions + dry_calls > args.max_calls:
            attack_only = tuple(s for s in scenarios if s.kind == "attack")
            if (
                attack_only
                and per_scenario_mean * len(attack_only) + dry_calls <= args.max_calls
            ):
                scaling_note = (
                    f"benign scenarios dropped: one repetition of all "
                    f"{len(scenarios)} scenarios projected "
                    f"{per_scenario_mean * len(scenarios) + dry_calls:.0f} calls "
                    f"against a {args.max_calls} cap. Ran {len(attack_only)} attack "
                    f"scenarios only. Benign utility was NOT measured in this run, so "
                    f"no utility claim can be made from it."
                )
                scenarios = attack_only
                repetitions = 1
                print(f"[auto-scale] {scaling_note}")
        if repetitions != requested_repetitions and scaling_note is None:
            scaling_note = (
                f"repetitions reduced from {requested_repetitions} to {repetitions} "
                f"to fit the {args.max_calls} call cap"
            )
            print(f"[auto-scale] {scaling_note}")

        projected = per_scenario_mean * len(scenarios) * repetitions
        dry_report = {
            "dry_scenarios": [s.scenario_id for s in dry_scenarios],
            "per_scenario": per_scenario,
            "dry_pass_calls": dry_calls,
            "mean_calls_per_scenario": round(per_scenario_mean, 2),
            "full_run_scenarios": len(scenarios),
            "repetitions_requested": requested_repetitions,
            "repetitions_selected": repetitions,
            "auto_scaling_note": scaling_note,
            "projected_full_run_calls": round(projected, 1),
            "projected_total_including_dry_pass": round(projected + dry_calls, 1),
            "cap": args.max_calls,
        }
        print(json.dumps(dry_report, indent=2))
        if projected + dry_calls > args.max_calls:
            print(
                f"[abort] projected {projected + dry_calls:.0f} calls exceeds the "
                f"{args.max_calls} cap; not running the full pass",
                file=sys.stderr,
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "dry-pass-abort.json").write_text(
                json.dumps(dry_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return 4

    print(
        f"[run] full pass: {len(scenarios)} scenarios x 2 builds x "
        f"{repetitions} repetition(s)"
    )

    def _progress(scenario: Any, rows: list[dict[str, Any]]) -> None:
        print(f"[run] {scenario.scenario_id}: {len(rows)} runs recorded")
        if client:
            print(f"      {client.summary_line()}")

    try:
        result = run_ab(
            harness=harness,
            scenarios=scenarios,
            output_dir=runs_dir,
            on_scenario=_progress,
            repetitions=repetitions,
        )
    except BudgetExceeded as exc:
        print(f"[abort] {exc}", file=sys.stderr)
        return 3

    ledger = client.ledger().model_dump(mode="json") if client else None
    result["dry_pass"] = dry_report
    result["budget"] = ledger
    result["environment"] = {
        "python": sys.version.split()[0],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "base_corpus": corpus_profile(BASE_MANIFEST),
        "attack_corpus": corpus_profile(ATTACK_MANIFEST),
        "attack_variants": [
            {
                "attack_id": variant.attack_id,
                "artifact_id": variant.artifact_id,
                "mechanism": variant.mechanism,
            }
            for variant in load_attack_variants()
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"ab-summary-{args.provider}.json"
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[run] wrote {summary_path}")
    if client:
        print(client.summary_line())
        ledger_path = output_dir / f"provider-calls-{args.provider}.json"
        ledger_path.write_text(
            json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"[run] wrote {ledger_path}")
    print(f"[run] total provider calls consumed: {client.total_calls if client else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
