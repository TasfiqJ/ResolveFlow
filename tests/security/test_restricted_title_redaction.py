from __future__ import annotations

from tests.security.test_forbidden_candidate import _retrieve


def test_public_contractor_trace_does_not_reveal_restricted_title() -> None:
    trace = _retrieve("contractor")
    assert "restricted" not in trace.model_dump_json().lower()
    assert trace.policy_reason_code == "eligible_by_snapshot"
