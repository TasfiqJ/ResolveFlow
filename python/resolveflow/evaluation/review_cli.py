from __future__ import annotations

import argparse
import csv
from pathlib import Path

from resolveflow.evaluation.review import write_review_analysis

FIELDS = (
    "assignment_id",
    "reviewer_id",
    "reviewer_role",
    "familiarity",
    "routing_usefulness",
    "evidence_sufficiency",
    "action_safety",
    "clarity",
    "edit_effort",
    "decision",
    "unsafe_or_unsupported_claim",
    "duration_seconds",
    "optional_rationale",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Blinded human-review export tooling")
    subcommands = parser.add_subparsers(dest="command", required=True)
    template = subcommands.add_parser("template")
    template.add_argument("--output", required=True, type=Path)
    analyze = subcommands.add_parser("analyze")
    analyze.add_argument("--input", required=True, type=Path)
    analyze.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "template":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS).writeheader()
        print(f"Empty private review export template: {args.output} (0 responses)")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_review_analysis(args.input, args.output)
    print(f"Exact-count review analysis: {args.output}")
