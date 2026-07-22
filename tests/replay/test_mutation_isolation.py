from pathlib import Path

from resolveflow.replay.materialize import materialize_scenario


def test_role_override_changes_only_declared_identity_object() -> None:
    scenario = materialize_scenario(Path("data/manifests/replay-role-downgrade-001.yaml"))

    assert [item.object_type for item in scenario.changed_objects] == ["identity"]
    assert scenario.identity.active_role == "contractor"
    assert scenario.case.error_code == "PYM-431"
    assert scenario.connector.jira == "healthy"
    assert scenario.corpus.snapshot.artifact_version_ids == tuple(
        sorted(scenario.manifest.frozen.corpus.artifact_version_ids)
    )
