from pathlib import Path

from resolveflow.evaluation.io import verify_bundle_file, write_bundle
from resolveflow.evaluation.runner import evaluate_manifest_pair


def test_bundle_file_and_canonical_checksums_reproduce(tmp_path: Path) -> None:
    bundle = evaluate_manifest_pair(Path("data/manifests/replay-role-downgrade-001.yaml"))
    first, first_checksum = write_bundle(bundle, tmp_path / "first.json")
    second, second_checksum = write_bundle(bundle, tmp_path / "second.json")

    assert first.read_bytes() == second.read_bytes()
    assert first_checksum.read_text().split()[0] == second_checksum.read_text().split()[0]
    assert verify_bundle_file(first).checksum == bundle.checksum
