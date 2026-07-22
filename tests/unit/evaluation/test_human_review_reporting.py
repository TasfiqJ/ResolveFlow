from __future__ import annotations

import csv
from pathlib import Path

from resolveflow.evaluation.review import analyze_review_export, blinded_order


def test_blinding_is_deterministic_and_balanced_by_assignment() -> None:
    assert blinded_order("a", "sha256:x") == blinded_order("a", "sha256:x")
    assert {blinded_order(str(index), "sha256:x") for index in range(20)} == {
        ("baseline", "candidate"),
        ("candidate", "baseline"),
    }


def test_exact_counts(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["reviewer_id", "decision"])
        writer.writeheader()
        writer.writerows(
            [
                {"reviewer_id": "r1", "decision": "accept"},
                {"reviewer_id": "r2", "decision": "minor_edit"},
                {"reviewer_id": "r1", "decision": "reject"},
            ]
        )
    result = analyze_review_export(path).as_dict()
    assert result["reviewer_count"] == 2
    assert result["assignment_count"] == 3
    assert result["percentages"]["accept"] == {"numerator": 1, "denominator": 3}


def test_empty_export_never_fabricates_results(tmp_path: Path) -> None:
    result = analyze_review_export(tmp_path / "absent.csv").as_dict()
    assert result["status"] == "human_review_not_yet_completed"
    assert result["reviewer_count"] == 0
