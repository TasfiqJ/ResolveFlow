from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

DECISIONS = ("accept", "minor_edit", "major_edit", "reject")


def blinded_order(assignment_id: str, pair_checksum: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"{assignment_id}:{pair_checksum}".encode()).digest()
    return ("candidate", "baseline") if digest[0] & 1 else ("baseline", "candidate")


@dataclass(frozen=True)
class ReviewSummary:
    reviewer_count: int
    assignment_count: int
    decision_counts: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "status": "completed" if self.assignment_count else "human_review_not_yet_completed",
            "reviewer_count": self.reviewer_count,
            "assignment_count": self.assignment_count,
            "decision_counts": self.decision_counts,
            "percentages": {
                key: {"numerator": count, "denominator": self.assignment_count}
                for key, count in self.decision_counts.items()
            },
        }


def analyze_review_export(path: Path) -> ReviewSummary:
    if not path.exists():
        return ReviewSummary(0, 0, {decision: 0 for decision in DECISIONS})
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    reviewers = {row["reviewer_id"] for row in rows if row.get("reviewer_id")}
    counts = {decision: 0 for decision in DECISIONS}
    for row in rows:
        decision = row.get("decision", "")
        if decision not in counts:
            raise ValueError(f"invalid review decision: {decision}")
        counts[decision] += 1
    return ReviewSummary(len(reviewers), len(rows), counts)


def write_review_analysis(source: Path, output: Path) -> None:
    output.write_text(json.dumps(analyze_review_export(source).as_dict(), indent=2) + "\n")
