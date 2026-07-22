from pathlib import Path

from resolveflow.evaluation.runner import evaluate_manifest_pair


def test_identical_records_produce_identical_bundle_and_verdict() -> None:
    manifest = Path("data/manifests/replay-role-downgrade-001.yaml")
    first = evaluate_manifest_pair(manifest)
    second = evaluate_manifest_pair(manifest)

    assert first.checksum == second.checksum
    assert first.baseline.verdict.verdict == second.baseline.verdict.verdict == "NO_SHIP"
    assert first.candidate.verdict.verdict == second.candidate.verdict.verdict
    assert first.candidate.verdict.verdict == "SHIP_WITH_LIMITS"
