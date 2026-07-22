from __future__ import annotations

import json
from pathlib import Path


def test_exploratory_slice_has_separate_conditions_and_no_claim() -> None:
    fixture = json.loads(Path("data/languages/exploratory-fr-1.0.json").read_text())
    assert fixture["status"] == "EXPLORATORY_UNVALIDATED"
    assert fixture["claim_allowed"] is False
    assert fixture["provenance"]["human_review_status"] == "pending"
    assert len(fixture["conditions"]) == 4
    assert len(set(fixture["conditions"])) == 4
