from __future__ import annotations

from pathlib import Path

from resolveflow.domain.hashing import checksum
from resolveflow.evaluation.gate import evaluate_release_gate
from resolveflow.evaluation.io import load_gate
from resolveflow.evaluation.models import (
    BuildEvaluation,
    ExperimentComparison,
    ResultBundle,
)
from resolveflow.evaluation.scoring import aggregate_metrics, score_run
from resolveflow.evaluation.statistics import paired_cluster_bootstrap
from resolveflow.orchestrator import _git_sha
from resolveflow.replay.io import load_manifest
from resolveflow.replay.materialize import materialize_scenario
from resolveflow.replay.runner import run_paired_replay


def evaluate_manifest_pair(manifest_path: Path) -> ResultBundle:
    manifest = load_manifest(manifest_path)
    materialized = materialize_scenario(manifest)
    paired = run_paired_replay(manifest_path)
    baseline_metrics = aggregate_metrics(
        score_run(
            paired.baseline,
            truth_id=materialized.truth.truth_id,
            correct_route=materialized.truth.correct_route,
            corpus=materialized.corpus,
            external_writes=materialized.connector.external_writes,
        )
    )
    candidate_metrics = aggregate_metrics(
        score_run(
            paired.candidate,
            truth_id=materialized.truth.truth_id,
            correct_route=materialized.truth.correct_route,
            corpus=materialized.corpus,
            external_writes=materialized.connector.external_writes,
        )
    )
    gate = load_gate()
    baseline_verdict = evaluate_release_gate(
        gate=gate,
        metrics=baseline_metrics,
        candidate_build=paired.baseline.build_id,
        baseline_build=paired.baseline.build_id,
        dataset_id="replay-development-draft-1.0",
    )
    candidate_verdict = evaluate_release_gate(
        gate=gate,
        metrics=candidate_metrics,
        candidate_build=paired.candidate.build_id,
        baseline_build=paired.baseline.build_id,
        dataset_id="replay-development-draft-1.0",
    )
    baseline_route = next(item for item in baseline_metrics if item.metric_id == "route_accuracy")
    candidate_route = next(item for item in candidate_metrics if item.metric_id == "route_accuracy")
    uncertainty = paired_cluster_bootstrap(
        {
            materialized.truth.truth_id: (
                baseline_route.value,
                candidate_route.value,
            )
        }
    )
    comparison_body = {
        "comparison_id": f"comparison_{manifest.scenario_id}",
        "baseline_build": paired.baseline.build_id,
        "candidate_build": paired.candidate.build_id,
        "paired_scenario_ids": (manifest.scenario_id,),
        "metric_id": "route_accuracy",
        "baseline_value": baseline_route.value,
        "candidate_value": candidate_route.value,
        "delta": candidate_route.value - baseline_route.value,
        "uncertainty": uncertainty,
    }
    comparison = ExperimentComparison(**comparison_body, checksum=checksum(comparison_body))
    body = {
        "schema_version": "1.0",
        "bundle_id": f"bundle_{manifest.scenario_id}_{paired.checksum.split(':', 1)[1][:12]}",
        "provenance": "deterministic_recorded_fixture",
        "content_label": "DRAFT_PENDING_HUMAN_REVIEW",
        "dataset_id": "replay-development-draft-1.0",
        "dataset_lock_status": "DRAFT_NOT_LOCKED",
        "manifest_id": manifest.manifest_id,
        "manifest_checksum": manifest.checksum,
        "materialization_checksum": materialized.materialization_checksum,
        "commit": _git_sha(),
        "baseline": BuildEvaluation(
            build_id=paired.baseline.build_id,
            metrics=baseline_metrics,
            verdict=baseline_verdict,
        ),
        "candidate": BuildEvaluation(
            build_id=paired.candidate.build_id,
            metrics=candidate_metrics,
            verdict=candidate_verdict,
        ),
        "comparison": comparison,
        "paired_run_checksum": paired.checksum,
    }
    return ResultBundle(**body, checksum=checksum(body))
