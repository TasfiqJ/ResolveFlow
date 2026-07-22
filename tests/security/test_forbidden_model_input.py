from __future__ import annotations

from tests.security.test_forbidden_candidate import _retrieve


def test_contractor_rerank_payload_contains_no_restricted_content() -> None:
    trace = _retrieve("contractor")
    serialized = trace.model_dump_json()
    assert "Restricted payments legal memo" not in serialized
    assert "Legal review material" not in serialized
