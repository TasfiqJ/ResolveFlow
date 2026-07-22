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
