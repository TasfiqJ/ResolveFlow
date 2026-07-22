from __future__ import annotations

from pathlib import Path


def test_multilingual_scope_is_honest() -> None:
    public_copy = "\n".join(path.read_text() for path in Path("apps/web/app").rglob("*.tsx"))
    lowered = public_copy.lower()
    assert "fully multilingual" not in lowered
    assert "validated french" not in lowered
    assert "english claims only" in lowered


def test_recorded_and_live_labels_are_not_conflated() -> None:
    public_copy = "\n".join(path.read_text() for path in Path("apps/web/app").rglob("*.tsx"))
    assert "RECORDED" in public_copy
    assert "Live mode off" in public_copy
