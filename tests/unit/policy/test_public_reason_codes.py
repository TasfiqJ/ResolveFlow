from __future__ import annotations

from resolveflow.domain.evidence import RetrievalTrace


def test_public_reason_code_is_safe_and_closed() -> None:
    field = RetrievalTrace.model_fields["policy_reason_code"]
    assert field.default == "eligible_by_snapshot"
