from pathlib import Path

from resolveflow.replay.materialize import materialize_scenario

MANIFEST = Path("data/manifests/replay-role-downgrade-001.yaml")


def test_same_manifest_has_identical_non_model_hashes() -> None:
    first = materialize_scenario(MANIFEST)
    second = materialize_scenario(MANIFEST)

    assert first.materialization_checksum == second.materialization_checksum
    assert first.rendered_input_hashes == second.rendered_input_hashes
    assert first.acl == second.acl
    assert first.changed_objects == second.changed_objects
