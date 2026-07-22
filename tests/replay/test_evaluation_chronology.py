from pathlib import Path

from resolveflow.evaluation.io import load_gate
from resolveflow.replay.io import load_truth_catalog


def test_gate_remains_draft_and_held_out_candidates_are_not_locked() -> None:
    gate = load_gate()
    catalog = load_truth_catalog()

    assert gate.registration_status == "DRAFT_PRE_REGISTERED_NO_HELD_OUT_RESULTS"
    assert gate.declared_commit == "uncommitted-stage-05"
    assert catalog.lock_status == "DRAFT_NOT_LOCKED"
    assert all(
        item.lock_status == "DRAFT_NOT_LOCKED"
        for item in catalog.truths
        if item.split == "held_out_candidate"
    )
    assert not Path("data/splits/held-out.lock.json").exists()
