from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_release_profile(payload: dict[str, Any]) -> str:
    profile = payload.get("release_profile")
    _require(
        profile in {"validated_release", "technical_preview"},
        "release_profile must be validated_release or technical_preview",
    )

    multilingual = payload.get("multilingual", {})
    language_is_scoped = multilingual.get("status") == "claim_removed" or (
        multilingual.get("status") == "validated"
        and multilingual.get("fluent_reviewer_confirmed") is True
    )
    _require(language_is_scoped, "multilingual claims are neither validated nor removed")

    if profile == "validated_release":
        truth_data = payload.get("truth_data", {})
        practitioner = payload.get("practitioner_review", {})
        _require(truth_data.get("status") == "complete", "truth data is incomplete")
        _require(
            truth_data.get("human_authored_truth_count", 0) >= 36,
            "validated release requires at least 36 human-authored truths",
        )
        _require(payload.get("gate_rules_locked") is True, "gate rules are not locked")
        _require(payload.get("held_out_locked") is True, "held-out data is not locked")
        _require(
            practitioner.get("status") == "complete",
            "practitioner review is incomplete",
        )
        _require(
            practitioner.get("reviewer_count", 0) >= 3,
            "validated release requires at least 3 practitioners",
        )
        _require(
            practitioner.get("case_count", 0) >= 10,
            "validated release requires at least 10 reviewed cases",
        )
        return profile

    preview = payload.get("technical_preview", {})
    _require(preview.get("operator_authorized") is True, "technical preview is not authorized")
    _require(
        preview.get("limitations_acknowledged") is True,
        "technical-preview limitations are not acknowledged",
    )
    _require(preview.get("publication_allowed") is True, "preview publication is not allowed")
    _require(
        preview.get("human_validation_claimed") is False,
        "technical preview cannot claim human validation",
    )
    _require(
        preview.get("final_release_verdict_claimed") is False,
        "technical preview cannot claim a final release verdict",
    )
    _require(
        multilingual.get("status") == "claim_removed",
        "technical preview must remove multilingual quality claims",
    )
    return profile


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the selected ResolveFlow release profile"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("docs/HUMAN_SIGNOFF.json"),
        help="Release authorization JSON",
    )
    args = parser.parse_args()
    payload = json.loads(args.file.read_text(encoding="utf-8"))
    profile = validate_release_profile(payload)
    print(f"Release profile passed: {profile}")


if __name__ == "__main__":
    main()
