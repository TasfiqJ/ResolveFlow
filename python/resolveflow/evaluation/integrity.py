from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.security import detect_hostile_evidence
from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum
from resolveflow.replay.io import load_truth_catalog
from resolveflow.replay.security_matrix import expand_security_matrix, load_security_matrix

ROOT = Path(__file__).resolve().parents[3]
ATTACK_FIXTURES = ROOT / "data" / "security" / "prompt-injection-fixtures.json"


class EvaluationIntegrityAudit(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    audit_id: Literal["evaluation-integrity-audit-1.0"] = "evaluation-integrity-audit-1.0"
    catalog_entry_count: int
    unique_semantic_truth_count: int
    duplicate_truth_groups: tuple[tuple[str, ...], ...]
    dataset_distinctness_verified: bool
    held_out_lock_status: str
    held_out_lock_verified: bool
    human_reviewed_truth_count: int
    security_matrix_declared_count: int
    security_matrix_expanded_count: int
    security_matrix_full_replay_execution_count: int
    attack_family_count: int
    attack_family_payload_coverage_count: int
    unique_attack_payload_count: int
    required_variant_payload_count: int
    attack_payload_control_execution_count: int
    attack_payload_control_pass_count: int
    security_matrix_execution_verified: bool
    limitations: tuple[str, ...]
    checksum: str


def _truth_semantics(truth: object) -> dict[str, object]:
    item = truth.model_dump(mode="python")  # type: ignore[attr-defined]
    return {
        key: item[key]
        for key in (
            "t0",
            "timeline",
            "tenant_id",
            "service",
            "region",
            "severity",
            "error_code",
            "correct_route",
            "evidence",
            "answerable",
            "required_unknowns",
            "permitted_action",
            "expected_mutation_behavior",
        )
    }


def audit_evaluation_integrity(
    attack_fixture_path: Path = ATTACK_FIXTURES,
) -> EvaluationIntegrityAudit:
    catalog = load_truth_catalog()
    semantic_groups: dict[str, list[str]] = {}
    for truth in catalog.truths:
        semantic_groups.setdefault(checksum(_truth_semantics(truth)), []).append(truth.truth_id)
    duplicate_groups = tuple(tuple(sorted(ids)) for ids in semantic_groups.values() if len(ids) > 1)

    matrix = load_security_matrix()
    expanded = expand_security_matrix(matrix)
    fixture_payload = json.loads(attack_fixture_path.read_text(encoding="utf-8"))
    fixtures = fixture_payload.get("fixtures", ())
    fixture_families = {str(item["family"]) for item in fixtures}
    unique_payloads = {str(item["content"]) for item in fixtures}
    declared_families = set(matrix.attack_families)
    payload_control_results = []
    for item in fixtures:
        document = UntrustedEvidenceDocument(
            document_id=str(item["fixture_id"]),
            artifact_id=str(item["fixture_id"]),
            artifact_version_id=f"{item['fixture_id']}_v1",
            title=f"Synthetic attack fixture {item['family']}",
            version="1",
            locator="security-fixture",
            content=str(item["content"]),
            content_checksum=checksum(item["content"]),
            hostile=True,
        )
        observed_effects = {event.effect.value for event in detect_hostile_evidence((document,))}
        payload_control_results.append(
            set(str(effect) for effect in item["expected_blocked_effects"]) <= observed_effects
        )

    distinctness_verified = len(semantic_groups) == len(catalog.truths)
    held_out_verified = catalog.lock_status != "DRAFT_NOT_LOCKED" and all(
        truth.lock_status != "DRAFT_NOT_LOCKED"
        for truth in catalog.truths
        if truth.split == "held_out_candidate"
    )
    matrix_execution_count = 0
    matrix_execution_verified = matrix_execution_count == matrix.declared_scenario_count
    limitations = (
        (
            f"{len(catalog.truths)} catalog IDs collapse to "
            f"{len(semantic_groups)} unique semantic truth template."
        ),
        (
            f"The security matrix declares {matrix.declared_scenario_count} cells but records "
            f"{matrix_execution_count} full Replay executions."
        ),
        (
            f"{len(fixture_families & declared_families)} of {len(declared_families)} declared "
            "attack families have a matching payload family."
        ),
        (
            f"The matrix declares {len(declared_families) * len(matrix.variants)} "
            f"family/variant payload slots but stores {len(unique_payloads)} unique payloads."
        ),
        (
            f"{sum(payload_control_results)} of {len(payload_control_results)} stored attack "
            "payloads exercise their expected deterministic forbidden-effect controls; this is "
            "not a substitute for a full Replay execution."
        ),
        "All truth candidates remain synthetic-agent-authored and pending human review.",
    )
    body = {
        "schema_version": "1.0",
        "audit_id": "evaluation-integrity-audit-1.0",
        "catalog_entry_count": len(catalog.truths),
        "unique_semantic_truth_count": len(semantic_groups),
        "duplicate_truth_groups": duplicate_groups,
        "dataset_distinctness_verified": distinctness_verified,
        "held_out_lock_status": catalog.lock_status,
        "held_out_lock_verified": held_out_verified,
        "human_reviewed_truth_count": sum(
            truth.provenance.human_review_status != "pending" for truth in catalog.truths
        ),
        "security_matrix_declared_count": matrix.declared_scenario_count,
        "security_matrix_expanded_count": len(expanded),
        "security_matrix_full_replay_execution_count": matrix_execution_count,
        "attack_family_count": len(declared_families),
        "attack_family_payload_coverage_count": len(fixture_families & declared_families),
        "unique_attack_payload_count": len(unique_payloads),
        "required_variant_payload_count": len(declared_families) * len(matrix.variants),
        "attack_payload_control_execution_count": len(payload_control_results),
        "attack_payload_control_pass_count": sum(payload_control_results),
        "security_matrix_execution_verified": matrix_execution_verified,
        "limitations": limitations,
    }
    return EvaluationIntegrityAudit(**body, checksum=checksum(body))


def write_evaluation_integrity_audit(
    audit: EvaluationIntegrityAudit,
    output: Path,
) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(audit.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8")
    file_digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{file_digest}  {output.name}\n", encoding="utf-8")
    return output, checksum_path
