from __future__ import annotations

from pathlib import Path


def test_foundation_migration_has_required_tables_and_downgrade() -> None:
    text = Path("migrations/versions/0001_foundation.py").read_text(encoding="utf-8")
    for table in ("tenants", "cases", "agent_runs", "audit_events", "jobs"):
        assert f'"{table}"' in text
    assert "def downgrade()" in text
    assert "uq_audit_run_sequence" in text


def test_governed_agent_migration_has_trace_and_evidence_tables() -> None:
    text = Path("migrations/versions/0003_governed_agent_safety.py").read_text(encoding="utf-8")
    for table in (
        "provider_calls",
        "tool_calls",
        "evidence_graphs",
        "claims",
        "citations",
        "verifier_results",
        "final_responses",
    ):
        assert f'"{table}"' in text
    assert "ck_model_tool_never_writes" in text
    assert "def downgrade()" in text


def test_action_migration_has_exact_approval_queue_and_append_only_controls() -> None:
    text = Path("migrations/versions/0004_actions_reliability_audit.py").read_text(encoding="utf-8")
    for table in (
        "action_proposals",
        "approvals",
        "action_idempotency",
        "action_attempts",
    ):
        assert f'"{table}"' in text
    assert "FOR UPDATE" not in text  # claiming belongs to the runtime repository
    assert "fk_approval_exact_proposal" in text
    assert "audit_events_no_update_delete" in text
    assert "def downgrade()" in text
