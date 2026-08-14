from __future__ import annotations

import pytest
from resolveflow.eval.ab_runner import _classify_structure_failure


@pytest.mark.parametrize(
    ("raw", "finish_reason", "expected"),
    (
        ('{"schema_version":', "max_tokens", "truncation"),
        ("[]", "complete", "wrong_type"),
        ("{}", "complete", "missing_field"),
        ("Here is the requested result.", "complete", "prose_instead_of_json"),
        ("I cannot comply with that request.", "complete", "refusal"),
        (
            '{"schema_version":"1.0","disposition":"needs_review",'
            '"route_claim_id":null,"summary_claim_ids":[],'
            '"recommended_step_claim_ids":[],"unknown_ids":[],'
            '"conflict_ids":[],"graph_hash":"sha256:measured",'
            '"needs_review":true}',
            "complete",
            "schema_valid_semantic_reference_invalid",
        ),
    ),
)
def test_structure_failure_classifier_uses_published_taxonomy(
    raw: str, finish_reason: str, expected: str
) -> None:
    assert _classify_structure_failure(raw, finish_reason) == expected
