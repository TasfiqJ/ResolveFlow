from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_release_profile import validate_release_profile


def test_repository_technical_preview_profile_is_truthful() -> None:
    payload = json.loads(Path("docs/HUMAN_SIGNOFF.json").read_text(encoding="utf-8"))

    assert validate_release_profile(payload) == "technical_preview"
    assert payload["truth_data"]["human_authored_truth_count"] == 0
    assert payload["practitioner_review"]["reviewer_count"] == 0


def test_technical_preview_rejects_invented_human_claim() -> None:
    payload = json.loads(Path("docs/HUMAN_SIGNOFF.json").read_text(encoding="utf-8"))
    payload["technical_preview"]["human_validation_claimed"] = True

    with pytest.raises(ValueError, match="cannot claim human validation"):
        validate_release_profile(payload)
