from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from pytest import MonkeyPatch
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.domain.hashing import checksum
from resolveflow.replay.io import load_manifest

SOURCE = Path("data/manifests/replay-role-downgrade-001.yaml")


def _write_variant(tmp_path: Path, mutate) -> Path:  # type: ignore[no-untyped-def]
    raw = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    mutate(raw)
    raw["checksum"] = checksum({key: value for key, value in raw.items() if key != "checksum"})
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return path


def test_unknown_mutation_fails_before_provider_call(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    calls = 0

    def provider_spy(self, request):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(FixtureChatAdapter, "chat", provider_spy)
    path = _write_variant(
        tmp_path, lambda raw: raw["mutations"][0].update({"type": "arbitrary_python"})
    )

    with pytest.raises(ValueError):
        load_manifest(path)
    assert calls == 0


def test_multiple_primary_mutations_are_rejected(tmp_path: Path) -> None:
    def duplicate(raw) -> None:  # type: ignore[no-untyped-def]
        raw["mutations"].append(raw["mutations"][0].copy())

    with pytest.raises(ValueError, match="exactly one primary mutation"):
        load_manifest(_write_variant(tmp_path, duplicate))


def test_checksum_mismatch_is_rejected() -> None:
    raw = SOURCE.read_text(encoding="utf-8").replace("role: contractor", "role: incident_commander")
    path = Path("/tmp/resolveflow-invalid-manifest.yaml")
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_manifest(path)
