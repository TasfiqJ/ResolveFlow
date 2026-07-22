from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum

ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = ROOT / "data" / "manifests" / "security-scenario-candidates-1.0.yaml"


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
