from pathlib import Path

from resolveflow.evaluation.scoring import score_run
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.replay.runner import run_paired_replay


def test_unexercised_hard_invariants_are_not_credited_as_passing(candidate_bundle) -> None:  # type: ignore[no-untyped-def]
    metrics = {item.metric_id: item for item in candidate_bundle.candidate.metrics}

    assert metrics["unapproved_write"].evidence_status == "not_exercised"
    assert metrics["payload_mismatch"].evidence_status == "not_exercised"
    assert metrics["duplicate_action"].evidence_status == "not_exercised"
    assert metrics["public_write_credential"].evidence_status == "not_verified"
    assert metrics["held_out_integrity"].evidence_status == "not_verified"


def test_tampered_run_event_hash_blocks_the_audit_invariant() -> None:
    paired_run = run_paired_replay(Path("data/manifests/replay-role-downgrade-001.yaml")).candidate
    first = paired_run.trace[0]
    tampered = first.model_copy(update={"safe_detail": {"role": "tampered"}})
    tampered_run = paired_run.model_copy(update={"trace": (tampered, *paired_run.trace[1:])})

    metrics = score_run(
        tampered_run,
        truth_id="dev-payments-001",
        correct_route="Payments Platform",
        corpus=load_hero_corpus(),
        external_writes=False,
    )
    audit_metric = next(item for item in metrics if item.metric_id == "missing_audit_chain")
    assert audit_metric.numerator == 1
    assert audit_metric.evidence_status == "observed"
