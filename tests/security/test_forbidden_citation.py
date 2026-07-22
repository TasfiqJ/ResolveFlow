from __future__ import annotations

from tests.security.test_forbidden_candidate import _retrieve


def test_candidate_projection_cannot_supply_forbidden_citation() -> None:
    trace = _retrieve("contractor")
    assert all(item.artifact_id != "artifact_restricted_legal" for item in trace.candidates)
