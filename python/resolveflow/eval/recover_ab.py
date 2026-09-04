"""Rebuild an A/B summary from run snapshots left on disk by an interrupted run.

A live run interrupted partway through has still spent provider calls and,
because snapshots are written as each run completes, has left every finished run
on disk. Throwing that away and re-running could spend the budget twice. This
module reconstructs the published summary from the committed snapshots, using the
exact same aggregation the live harness uses, and keeps **only whole
repetitions** so the result is never a lopsided partial trial.

It spends zero provider calls. Metrics are recomputed from each snapshot and the
corpus, identically to a live run -- ``RunMetrics`` reads retrieval candidates,
citations, ACLs and corpus text, never embeddings -- so the numbers are the same
ones the live run would have published for those trials. A retained provider-call
ledger is reconciled against the selected snapshots. If it does not match, it is
preserved as unassociated forensic evidence and its aggregate telemetry is void.

    python -m resolveflow.eval.recover_ab --provider cohere
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.eval.ab_runner import (
    BUILD_IDS,
    EVAL_BUDGETS,
    RunMetrics,
    build_result,
    validate_frozen_snapshot_inputs,
)
from resolveflow.eval.corpus import (
    ATTACK_MANIFEST,
    BASE_MANIFEST,
    build_eval_corpus,
    load_attack_variants,
)
from resolveflow.eval.embed_corpus import CACHE_PATH
from resolveflow.eval.embedding_cache import CachedEmbeddingAdapter
from resolveflow.eval.publish import reconcile_provider_telemetry, recovery_receipt_note
from resolveflow.eval.scenarios import EvalScenario, all_scenarios
from resolveflow.eval.snapshot_integrity import validate_snapshot_evidence
from resolveflow.ingestion.fixtures import ROOT, corpus_profile
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter

RESULTS_DIR = ROOT / "eval" / "results"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _trial_of(run_id: str, build_id: str) -> int:
    """Trial 1 has no suffix; later trials end in ``_t<N>``."""
    tail = run_id.rsplit(f"_{build_id}", 1)[-1]
    if tail.startswith("_t") and tail[2:].isdigit():
        return int(tail[2:])
    return 1


def recover(
    provider: str,
    runs_dir: Path,
    *,
    agent_budgets: dict[str, Any] | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required_budget_keys = {
        "policy_id",
        "max_tool_rounds",
        "max_provider_calls",
        "max_total_tokens",
        "max_output_tokens_per_call",
        "wall_clock_seconds",
        "tool_timeout_seconds",
    }
    if provider == "cohere" and agent_budgets is None:
        raise SystemExit(
            "live recovery requires explicit historical agent budgets; pass "
            "--agent-budgets-file from the interrupted execution"
        )
    if agent_budgets is not None:
        if not isinstance(agent_budgets, dict):
            raise SystemExit("historical agent_budgets must be a JSON object")
        missing_budget_keys = sorted(required_budget_keys - set(agent_budgets))
        if missing_budget_keys:
            raise SystemExit(f"historical agent_budgets missing keys: {missing_budget_keys}")
        selected_budgets: dict[str, Any] | Any = dict(agent_budgets)
    else:
        selected_budgets = EVAL_BUDGETS
    scenarios = all_scenarios()
    by_id: dict[str, EvalScenario] = {s.scenario_id: s for s in scenarios}
    expected_per_trial = len(scenarios) * len(BUILD_IDS)
    expected_cells = {
        (scenario.scenario_id, build_id) for scenario in scenarios for build_id in BUILD_IDS
    }

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
        recomputed_hash = checksum(
            snapshot.model_dump(
                mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS
            )
        )
        if recomputed_hash != snapshot.content_hash:
            raise SystemExit(f"snapshot content hash mismatch: {path.name}")
        try:
            validate_snapshot_evidence(snapshot, data, allow_legacy_graph_hash=True)
        except ValueError as exc:
            raise SystemExit(f"snapshot nested evidence is invalid: {path.name}: {exc}") from exc
        scenario_id = snapshot.scenario_id
        scenario = by_id.get(scenario_id) if scenario_id is not None else None
        if scenario is None:
            skipped_unknown += 1
            continue
        trial = _trial_of(snapshot.run_id, snapshot.build_id)
        by_trial[trial].append((scenario, snapshot.build_id, snapshot))

    complete_trials: list[int] = []
    for trial, items in sorted(by_trial.items()):
        cells = [(scenario.scenario_id, build_id) for scenario, build_id, _ in items]
        if len(items) == expected_per_trial and (
            len(set(cells)) != len(cells) or set(cells) != expected_cells
        ):
            missing = sorted(expected_cells - set(cells))
            duplicates = sorted(cell for cell in set(cells) if cells.count(cell) > 1)
            raise SystemExit(
                f"trial {trial} has full cardinality but an invalid scenario/build cell set; "
                f"missing={missing}, duplicates={duplicates}"
            )
        if (
            len(items) == expected_per_trial
            and len(set(cells)) == len(cells)
            and set(cells) == expected_cells
        ):
            complete_trials.append(trial)
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
    expected_trial_sequence = list(range(1, len(complete_trials) + 1))
    if complete_trials != expected_trial_sequence:
        raise SystemExit(
            f"complete repetitions must be contiguous from trial 1; found {complete_trials}"
        )

    selected_items = [item for trial in complete_trials for item in by_trial[trial]]
    cohort_snapshots = [snapshot for _, _, snapshot in selected_items]
    for label, values in (
        ("generated_at", {snapshot.generated_at for snapshot in cohort_snapshots}),
        ("commit", {snapshot.commit for snapshot in cohort_snapshots}),
        ("model_policy", {snapshot.model_policy for snapshot in cohort_snapshots}),
        ("provenance", {snapshot.provenance for snapshot in cohort_snapshots}),
    ):
        if len(values) != 1:
            raise SystemExit(f"mixed execution cohort: selected snapshots differ on {label}")

    command_models = {
        str(trace.get("model"))
        for snapshot in cohort_snapshots
        for trace in snapshot.provider_traces
        if isinstance(trace, dict) and trace.get("model")
    }
    rerank_models = {snapshot.retrieval.rerank_model for snapshot in cohort_snapshots}
    embedding_models = {snapshot.retrieval.embedding_model for snapshot in cohort_snapshots}
    for label, values in (
        ("command_model", command_models),
        ("rerank_model", rerank_models),
        ("embedding_model", embedding_models),
    ):
        if len(values) != 1 or not next(iter(values), None):
            raise SystemExit(f"mixed execution cohort: selected snapshots differ on {label}")
    command_model = next(iter(command_models))
    rerank_model = next(iter(rerank_models))
    embedding_model = next(iter(embedding_models))
    if source_metadata is not None:
        for label, measured in (
            ("command_model", command_model),
            ("rerank_model", rerank_model),
            ("embedding_model", embedding_model),
        ):
            published = source_metadata.get(label)
            if published is not None and published != measured:
                raise SystemExit(
                    f"historical model mismatch: {label}={published!r}, snapshots={measured!r}"
                )

    inputs_by_cell: dict[tuple[str, str], set[str]] = defaultdict(set)
    for scenario, build_id, snapshot in selected_items:
        inputs_by_cell[(scenario.scenario_id, build_id)].add(checksum(snapshot.run_inputs))
    if any(len(values) != 1 for values in inputs_by_cell.values()):
        raise SystemExit("mixed execution cohort: repeated cells differ on run_inputs")

    # Rebuild the corpus per attack artifact once. Live recovery must use the
    # retained Embed cache so the frozen corpus checksum remains identical; it
    # is opened with provider fallback disabled, so recovery cannot make a call.
    corpus_cache: dict[str | None, Any] = {}
    recovery_embedder = (
        CachedEmbeddingAdapter(CACHE_PATH, client=None, allow_provider=False)
        if provider == "cohere"
        else FixtureEmbeddingAdapter()
    )

    def corpus_for(scenario: EvalScenario) -> Any:
        key = scenario.attack_artifact_id
        if key not in corpus_cache:
            corpus_cache[key] = build_eval_corpus(
                embedder=recovery_embedder, attack_artifact_id=key
            )
        return corpus_cache[key]

    def validate_frozen_inputs(
        scenario: EvalScenario, build_id: str, snapshot: RunSnapshot, trial: int
    ) -> None:
        corpus = corpus_for(scenario)
        try:
            validate_frozen_snapshot_inputs(scenario, build_id, snapshot, trial, corpus)
        except ValueError as exc:
            raise SystemExit(f"historical truth mismatch: {exc}") from exc

    rows: list[dict[str, Any]] = []
    snapshots: list[RunSnapshot] = []
    max_output_tokens = (
        int(selected_budgets["max_output_tokens_per_call"])
        if isinstance(selected_budgets, dict)
        else selected_budgets.max_output_tokens_per_call
    )
    for trial in complete_trials:
        trial_items = {
            (scenario.scenario_id, build_id): (scenario, snapshot)
            for scenario, build_id, snapshot in by_trial[trial]
        }
        for scenario in scenarios:
            for build_id in BUILD_IDS:
                scenario, snapshot = trial_items[(scenario.scenario_id, build_id)]
                validate_frozen_inputs(scenario, build_id, snapshot, trial)
                call_records = tuple(
                    {"max_tokens": max_output_tokens} for _ in snapshot.provider_traces
                )
                metrics = RunMetrics(
                    scenario,
                    build_id,
                    snapshot,
                    corpus_for(scenario),
                    call_records=call_records,
                )
                metrics.trial = trial
                rows.append(metrics.as_dict())
                snapshots.append(snapshot)

    generated_at = cohort_snapshots[0].generated_at
    result = build_result(
        rows=rows,
        snapshots=snapshots,
        scenarios=scenarios,
        provider=provider,
        command_model=command_model,
        rerank_model=rerank_model,
        embedding_model=embedding_model,
        agent_budgets=selected_budgets,
        generated_at=generated_at,
        repetitions=len(complete_trials),
        output_dir=None,
    )

    # Reconcile the retained ledger with the selected complete snapshots. A
    # mismatch is retained for audit, but never presented as this summary's
    # provider consumption record.
    result["execution_commit"] = cohort_snapshots[0].commit
    execution_provenance: dict[str, Any] = {
        "git_state": cohort_snapshots[0].commit,
        "controls_not_present_in_execution": sorted(
            field
            for field in (
                "max_tool_calls_per_response",
                "max_tool_calls_per_run",
                "reserved_provider_calls_for_render",
            )
            if field
            not in (
                selected_budgets
                if isinstance(selected_budgets, dict)
                else selected_budgets.model_dump(mode="python")
            )
        ),
    }
    if cohort_snapshots[0].commit == "uncommitted":
        execution_provenance["exact_dirty_diff_retained"] = False
    if isinstance(selected_budgets, dict):
        execution_provenance["historical_agent_budgets"] = (
            "verbatim_from_prior_publication_metadata"
        )
    corpus_pairs = {
        (snapshot.corpus_version, snapshot.retrieval.corpus_snapshot_id)
        for snapshot in cohort_snapshots
        if snapshot.corpus_version != snapshot.retrieval.corpus_snapshot_id
    }
    recorded_corpus_labels = {item[0] for item in corpus_pairs}
    if len(recorded_corpus_labels) > 1:
        raise SystemExit("cohort mixes incompatible legacy corpus labels")
    if corpus_pairs:
        execution_provenance["legacy_snapshot_corpus_label"] = {
            "recorded_value": next(iter(recorded_corpus_labels)),
            "authoritative_snapshot_ids": sorted(item[1] for item in corpus_pairs),
            "verification": "retrieval_snapshot_id_and_frozen_corpus_checksum",
        }
    result["execution_provenance"] = execution_provenance
    # Corpus evidence is regenerated from the frozen manifests instead of being
    # copied blindly from a prior summary. Preserve only historical execution
    # fields that cannot be reconstructed, then overwrite the evidence-bearing
    # fields with freshly checksummed profiles. This keeps recovery useful even
    # if its source summary was partial, while preventing stale corpus metadata
    # from being republished.
    environment = {
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
    result["environment"] = environment

    dry_scenario_ids = {scenarios[0].scenario_id, scenarios[8].scenario_id}
    ledger_path = RESULTS_DIR / f"provider-calls-{provider}.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        validity = reconcile_provider_telemetry(
            [snapshot.model_dump(mode="json") for snapshot in snapshots],
            ledger,
            dry_scenario_ids=dry_scenario_ids,
        )
        result["provider_telemetry_validity"] = validity
        if validity["valid"]:
            result["budget"] = ledger
            observations = validity["ledger_observations"]
            result["dry_pass"] = {
                "dry_scenarios": sorted(dry_scenario_ids),
                "dry_pass_runs": len(dry_scenario_ids) * len(BUILD_IDS),
                "dry_pass_calls": observations["dry_pass_record_count"],
                "full_pass_calls": observations["published_run_record_count"],
                "cap": ledger.get("max_calls"),
                "recovered": True,
            }
        else:
            result["unassociated_provider_ledger"] = ledger
    excluded_dir = runs_dir.parent / f"{provider}-excluded-prior-invocation"
    excluded_paths = sorted(excluded_dir.glob("run-*.json"))
    provider_ledger_reconciled = bool(
        (result.get("provider_telemetry_validity") or {}).get("valid")
    )
    result["recovered_from_snapshots"] = {
        "runs_dir": _rel(runs_dir),
        "complete_trials_used": complete_trials,
        "incomplete_trials_dropped": incomplete,
        "snapshots_unmatched_to_a_scenario": skipped_unknown,
        "excluded_snapshot_directory": _rel(excluded_dir) if excluded_paths else None,
        "excluded_snapshot_count": len(excluded_paths),
        "note": recovery_receipt_note(
            repetitions=len(complete_trials),
            excluded_snapshot_count=len(excluded_paths),
            provider_ledger_reconciled=provider_ledger_reconciled,
            dry_pass_runs=(result.get("dry_pass") or {}).get("dry_pass_runs"),
        ),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover an A/B summary from snapshots.")
    parser.add_argument("--provider", choices=("fixture", "cohere"), default="cohere")
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument(
        "--agent-budgets-file",
        type=Path,
        default=None,
        help="JSON containing the historical agent_budgets block (required for Cohere)",
    )
    args = parser.parse_args(argv)

    runs_dir = args.runs_dir or (RESULTS_DIR / "runs" / args.provider)
    source_metadata: dict[str, Any] | None = None
    historical_budgets: dict[str, Any] | None = None
    if args.agent_budgets_file is not None:
        source_metadata = json.loads(args.agent_budgets_file.read_text(encoding="utf-8"))
        budget_payload = source_metadata.get("agent_budgets", source_metadata)
        if not isinstance(budget_payload, dict):
            raise SystemExit("historical agent_budgets must be a JSON object")
        required_budget_keys = {
            "policy_id",
            "max_tool_rounds",
            "max_provider_calls",
            "max_total_tokens",
            "max_output_tokens_per_call",
            "wall_clock_seconds",
            "tool_timeout_seconds",
        }
        if not required_budget_keys.issubset(budget_payload):
            missing = sorted(required_budget_keys - set(budget_payload))
            raise SystemExit(f"historical agent_budgets missing keys: {missing}")
        historical_budgets = dict(budget_payload)
    result = recover(
        args.provider,
        runs_dir,
        agent_budgets=historical_budgets,
        source_metadata=source_metadata,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"ab-summary-{args.provider}.json"
    out.write_bytes((json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    rec = result["recovered_from_snapshots"]
    print(f"[recover] complete trials used: {rec['complete_trials_used']}")
    print(f"[recover] incomplete trials dropped: {rec['incomplete_trials_dropped']}")
    print(f"[recover] runs aggregated: {result['run_count']} ({result['repetitions']} rep(s))")
    print(f"[recover] wrote {out}")
    print(f"[recover] now run: python -m resolveflow.eval.publish {args.provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
