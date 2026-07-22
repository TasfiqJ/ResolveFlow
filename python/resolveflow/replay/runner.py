from __future__ import annotations

from pathlib import Path

from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.orchestrator import ResolveOrchestrator, ResolveRunConfiguration
from resolveflow.replay.io import load_build_config
from resolveflow.replay.materialize import materialize_scenario
from resolveflow.replay.models import MaterializedScenario, PairedReplay
from resolveflow.telemetry.diff import diff_runs


def _run_build(
    materialized: MaterializedScenario,
    build_id: str,
    orchestrator: ResolveOrchestrator,
) -> RunSnapshot:
    build = load_build_config(build_id)
    digest = materialized.materialization_checksum.split(":", 1)[1][:12]
    configuration = ResolveRunConfiguration(
        run_id=f"run_{materialized.manifest.scenario_id}_{build_id}_{digest}",
        build_id=build_id,
        generated_at=materialized.manifest.frozen.clock,
        scenario_id=materialized.manifest.scenario_id,
        identity=materialized.identity,
        corpus=materialized.corpus,
        authorization_mode=("enforced" if build.pre_retrieval_authorization else "prompt_only"),
        verifier_enforcement=build.verifier_enforcement,
        model_policy=materialized.manifest.frozen.model_policy,
        connector_state=materialized.connector.jira,
        connector_fixture_version=materialized.connector.fixture_version,
        feature_flags={
            **materialized.feature_flags,
            **build.feature_flags,
            "verifier_enforced": build.verifier_enforcement == "enforced",
            "approval_required": build.approval_required,
            "external_writes": build.external_writes,
        },
    )
    return orchestrator.run(materialized.case, configuration)


def run_paired_replay(manifest_path: Path) -> PairedReplay:
    materialized = materialize_scenario(manifest_path)
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(), GovernedAgent(FixtureChatAdapter())
    )
    baseline = _run_build(materialized, "unsafe-v0", orchestrator)
    candidate = _run_build(materialized, "guarded-v1", orchestrator)
    run_diff = diff_runs(baseline, candidate).model_dump(mode="json")
    body = {
        "scenario_id": materialized.manifest.scenario_id,
        "materialization_checksum": materialized.materialization_checksum,
        "baseline": baseline.content_hash,
        "candidate": candidate.content_hash,
        "run_diff": run_diff,
    }
    return PairedReplay(
        scenario_id=materialized.manifest.scenario_id,
        materialization_checksum=materialized.materialization_checksum,
        baseline=baseline,
        candidate=candidate,
        run_diff=run_diff,
        checksum=checksum(body),
    )
