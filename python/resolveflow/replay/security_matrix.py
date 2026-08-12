from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum

ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = ROOT / "data" / "manifests" / "security-scenario-candidates-1.0.yaml"
EXECUTION_PATH = ROOT / "data" / "evaluation" / "security-matrix-replay-execution-1.0.json"


class SecurityScenarioCandidate(FrozenModel):
    scenario_id: str
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"]
    truth_id: str
    attack_family: str
    variant: int
    mutation_type: Literal["add_artifact"] = "add_artifact"
    artifact_version_id: Literal["artifact_hostile_note_v1"] = "artifact_hostile_note_v1"
    expected_invariant: Literal["prompt_injection_effect"] = "prompt_injection_effect"
    execution_suite: Literal["deterministic_application_control"] = (
        "deterministic_application_control"
    )


class SecurityScenarioMatrix(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    matrix_id: str
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"]
    lock_status: Literal["DRAFT_NOT_LOCKED"]
    base_truth_ids: tuple[str, ...]
    attack_families: tuple[str, ...]
    variants: tuple[int, ...]
    declared_scenario_count: int
    live_provider_calls: Literal[0] = 0
    checksum: str


class SecurityMatrixCellExecution(FrozenModel):
    scenario_id: str
    truth_id: str
    attack_family: str
    variant: int
    build_id: Literal["guarded-v1"] = "guarded-v1"
    provider: Literal["recorded_fixture"] = "recorded_fixture"
    executed_artifact_version_id: Literal["artifact_hostile_note_v1"] = "artifact_hostile_note_v1"
    manifest_checksum: str
    materialization_checksum: str | None
    run_id: str | None
    run_content_hash: str | None
    trace_event_count: int
    trace_final_event_hash: str | None
    audit_chain_verified: bool
    attempted_effects: tuple[str, ...]
    successful_effects: tuple[str, ...]
    passed: bool
    failure_reasons: tuple[str, ...]
    checksum: str


class SecurityMatrixReplayExecution(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    execution_id: Literal["security-matrix-replay-execution-1.0"] = (
        "security-matrix-replay-execution-1.0"
    )
    matrix_id: str
    matrix_checksum: str
    execution_suite: Literal["deterministic_application_control"] = (
        "deterministic_application_control"
    )
    build_id: Literal["guarded-v1"] = "guarded-v1"
    provider: Literal["recorded_fixture"] = "recorded_fixture"
    declared_count: int
    executed_count: int
    pass_count: int
    failure_count: int
    results: tuple[SecurityMatrixCellExecution, ...]
    limitations: tuple[str, ...]
    checksum: str


def load_security_matrix(path: Path = MATRIX_PATH) -> SecurityScenarioMatrix:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("security scenario matrix YAML root must be an object")
    body = {key: value for key, value in raw.items() if key != "checksum"}
    if raw.get("checksum") != checksum(body):
        raise ValueError("security scenario matrix checksum mismatch")
    matrix = SecurityScenarioMatrix.model_validate(raw)
    expected = len(matrix.base_truth_ids) * len(matrix.attack_families) * len(matrix.variants)
    if matrix.declared_scenario_count != expected:
        raise ValueError("declared security scenario count does not match the Cartesian matrix")
    return matrix


def expand_security_matrix(
    matrix: SecurityScenarioMatrix | None = None,
) -> tuple[SecurityScenarioCandidate, ...]:
    source = matrix or load_security_matrix()
    scenarios = []
    for index, (truth_id, family, variant) in enumerate(
        product(source.base_truth_ids, source.attack_families, source.variants), 1
    ):
        scenarios.append(
            SecurityScenarioCandidate(
                scenario_id=f"security-draft-{index:03d}",
                content_label=source.content_label,
                truth_id=truth_id,
                attack_family=family,
                variant=variant,
            )
        )
    return tuple(scenarios)


def load_security_matrix_execution(
    path: Path = EXECUTION_PATH,
) -> SecurityMatrixReplayExecution:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("security matrix execution JSON root must be an object")
    body = {key: value for key, value in raw.items() if key != "checksum"}
    if raw.get("checksum") != checksum(body):
        raise ValueError("security matrix execution checksum mismatch")
    execution = SecurityMatrixReplayExecution.model_validate(raw)
    if execution.executed_count != len(execution.results):
        raise ValueError("security matrix executed count does not match per-cell results")
    if execution.pass_count != sum(item.passed for item in execution.results):
        raise ValueError("security matrix pass count does not match per-cell results")
    if execution.failure_count != sum(not item.passed for item in execution.results):
        raise ValueError("security matrix failure count does not match per-cell results")
    if len({item.scenario_id for item in execution.results}) != len(execution.results):
        raise ValueError("security matrix execution contains duplicate scenario IDs")
    for item in execution.results:
        item_body = item.model_dump(mode="python", exclude={"checksum"})
        if item.checksum != checksum(item_body):
            raise ValueError(f"security matrix cell checksum mismatch: {item.scenario_id}")
    return execution
