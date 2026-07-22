import json
from pathlib import Path

from resolveflow.replay.io import load_truth_catalog


def test_truth_catalog_has_exact_draft_counts_and_labels() -> None:
    catalog = load_truth_catalog()
    assert len(catalog.truths) == 36
    assert sum(item.split == "development" for item in catalog.truths) == 18
    assert sum(item.split == "calibration" for item in catalog.truths) == 8
    assert sum(item.split == "held_out_candidate" for item in catalog.truths) == 10
    assert all(
        item.provenance.content_label == "DRAFT_PENDING_HUMAN_REVIEW" for item in catalog.truths
    )
    assert all(item.provenance.human_review_status == "pending" for item in catalog.truths)


def test_all_repository_json_truth_content_has_required_draft_label() -> None:
    for path in Path("data/truths").glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["content_label"] == "DRAFT_PENDING_HUMAN_REVIEW", path
