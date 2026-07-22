"""Governed agent, provider/tool trace, evidence graph, and verifier records.

Revision ID: 0003_governed_agent_safety
Revises: 0002_evidence_retrieval
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_governed_agent_safety"
down_revision = "0002_evidence_retrieval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_calls",
        sa.Column("provider_call_id", sa.String(96), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), nullable=False),
        sa.Column("pass_kind", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("request_hash", sa.String(72), nullable=False),
        sa.Column("response_hash", sa.String(72)),
        sa.Column("provider_response_id", sa.String(160)),
        sa.Column("finish_reason", sa.String(32)),
        sa.Column("usage", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("safe_error_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("duration_ms >= 0", name="ck_provider_call_duration"),
    )
    op.create_table(
        "tool_calls",
        sa.Column("tool_call_id", sa.String(120), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("arguments_hash", sa.String(72), nullable=False),
        sa.Column("authorization", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provenance_ids", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("safe_error_code", sa.String(80)),
        sa.Column("external_write", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("external_write = false", name="ck_model_tool_never_writes"),
    )
    op.create_table(
        "evidence_graphs",
        sa.Column("graph_id", sa.String(96), primary_key=True),
        sa.Column(
            "run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), nullable=False, unique=True
        ),
        sa.Column("graph_hash", sa.String(72), nullable=False, unique=True),
        sa.Column("graph_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "claims",
        sa.Column("claim_id", sa.String(96), primary_key=True),
        sa.Column(
            "graph_id", sa.String(96), sa.ForeignKey("evidence_graphs.graph_id"), nullable=False
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("material", sa.Boolean(), nullable=False),
        sa.Column("verifier_codes", sa.JSON(), nullable=False),
    )
    op.create_table(
        "citations",
        sa.Column("citation_id", sa.String(96), primary_key=True),
        sa.Column("claim_id", sa.String(96), sa.ForeignKey("claims.claim_id"), nullable=False),
        sa.Column(
            "artifact_version_id",
            sa.String(120),
            sa.ForeignKey("artifact_versions.artifact_version_id"),
        ),
        sa.Column("document_id", sa.String(96), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("verifier_checks", sa.JSON(), nullable=False),
    )
    op.create_table(
        "verifier_results",
        sa.Column("verifier_result_id", sa.String(96), primary_key=True),
        sa.Column("claim_id", sa.String(96), sa.ForeignKey("claims.claim_id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("codes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "final_responses",
        sa.Column("final_response_id", sa.String(96), primary_key=True),
        sa.Column(
            "run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), nullable=False, unique=True
        ),
        sa.Column("graph_hash", sa.String(72), nullable=False),
        sa.Column("disposition", sa.String(32), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("final_responses")
    op.drop_table("verifier_results")
    op.drop_table("citations")
    op.drop_table("claims")
    op.drop_table("evidence_graphs")
    op.drop_table("tool_calls")
    op.drop_table("provider_calls")
