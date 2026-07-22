"""Approval-bound actions, durable leases, idempotency, and append-only audit.

Revision ID: 0004_actions_reliability_audit
Revises: 0003_governed_agent_safety
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_actions_reliability_audit"
down_revision = "0003_governed_agent_safety"
branch_labels = None
depends_on = None

ACTION_STATES = (
    "pending_approval",
    "approved",
    "rejected",
    "expired",
    "invalidated",
    "dispatching",
    "reconciling",
    "acknowledged",
    "complete",
    "retry_wait",
    "dead_letter",
    "cancelled",
)
JOB_STATES = ("queued", "leased", "running", "retry_wait", "complete", "dead_letter", "cancelled")


def upgrade() -> None:
    op.add_column("jobs", sa.Column("run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id")))
    op.add_column("jobs", sa.Column("logical_key", sa.String(160)))
    op.add_column("jobs", sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("jobs", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("jobs", sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False))
    op.add_column("jobs", sa.Column("lease_owner", sa.String(96)))
    op.add_column("jobs", sa.Column("lease_expires_at", sa.DateTime(timezone=True)))
    op.add_column("jobs", sa.Column("last_error_code", sa.String(100)))
    op.add_column("jobs", sa.Column("cancellation_requested", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("jobs", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("jobs", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_unique_constraint("uq_jobs_logical_key", "jobs", ["logical_key"])
    op.create_check_constraint("ck_jobs_state", "jobs", f"status IN {JOB_STATES!r}")
    op.create_check_constraint("ck_jobs_attempt_bounds", "jobs", "attempt_count >= 0 AND max_attempts >= 1 AND attempt_count <= max_attempts")
    op.create_index("ix_jobs_claim", "jobs", ["status", "available_at", "lease_expires_at", "created_at"])

    op.create_table(
        "action_proposals",
        sa.Column("proposal_id", sa.String(96), primary_key=True),
        sa.Column("logical_action_id", sa.String(96), nullable=False),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), nullable=False),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("graph_hash", sa.String(72), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_digest", sa.String(72), nullable=False),
        sa.Column("idempotency_key", sa.String(72), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_by_proposal_id", sa.String(96)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(f"state IN {ACTION_STATES!r}", name="ck_action_proposal_state"),
        sa.CheckConstraint("expires_at > created_at", name="ck_action_proposal_expiry"),
        sa.UniqueConstraint("logical_action_id", "revision", name="uq_action_revision"),
        sa.UniqueConstraint("proposal_id", "payload_digest", name="uq_proposal_exact_digest"),
    )
    op.create_index("ix_action_proposals_dispatch", "action_proposals", ["state", "expires_at"])
    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.String(96), primary_key=True),
        sa.Column("proposal_id", sa.String(96), nullable=False),
        sa.Column("payload_digest", sa.String(72), nullable=False),
        sa.Column("approver_id", sa.String(96), nullable=False),
        sa.Column("permission_result", sa.String(64), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["proposal_id", "payload_digest"],
            ["action_proposals.proposal_id", "action_proposals.payload_digest"],
            name="fk_approval_exact_proposal",
        ),
        sa.UniqueConstraint("proposal_id", name="uq_approval_proposal"),
        sa.CheckConstraint("permission_result = 'allowed'", name="ck_approval_allowed_only"),
        sa.CheckConstraint("expires_at > approved_at", name="ck_approval_expiry"),
    )
    op.create_table(
        "action_idempotency",
        sa.Column("logical_action_id", sa.String(96), primary_key=True),
        sa.Column("idempotency_key", sa.String(72), nullable=False, unique=True),
        sa.Column("proposal_id", sa.String(96), sa.ForeignKey("action_proposals.proposal_id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("remote_issue_key", sa.String(96)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("logical_action_id", "idempotency_key", name="uq_idempotency_pair"),
    )
    op.create_table(
        "action_attempts",
        sa.Column("attempt_id", sa.String(96), primary_key=True),
        sa.Column("proposal_id", sa.String(96), sa.ForeignKey("action_proposals.proposal_id"), nullable=False),
        sa.Column("logical_action_id", sa.String(96), nullable=False),
        sa.Column("idempotency_key", sa.String(72), nullable=False),
        sa.Column("payload_digest", sa.String(72), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(72), nullable=False),
        sa.Column("disposition", sa.String(40), nullable=False),
        sa.Column("safe_error_code", sa.String(100)),
        sa.Column("retry_decision", sa.String(32), nullable=False),
        sa.Column("reconciliation", sa.JSON()),
        sa.Column("remote_issue_key", sa.String(96)),
        sa.UniqueConstraint("proposal_id", "attempt_number", name="uq_action_attempt_number"),
        sa.ForeignKeyConstraint(
            ["logical_action_id", "idempotency_key"],
            ["action_idempotency.logical_action_id", "action_idempotency.idempotency_key"],
            name="fk_attempt_idempotency",
        ),
    )
    for name, column in (
        ("actor_id", sa.Column("actor_id", sa.String(96), server_default="resolveflow-service", nullable=False)),
        ("actor_type", sa.Column("actor_type", sa.String(20), server_default="service", nullable=False)),
        ("component", sa.Column("component", sa.String(80), server_default="legacy", nullable=False)),
        ("outcome", sa.Column("outcome", sa.String(40), server_default="ok", nullable=False)),
        ("duration_ms", sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False)),
        ("correlation_ids", sa.Column("correlation_ids", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False)),
        ("versions", sa.Column("versions", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False)),
        ("trace_id", sa.Column("trace_id", sa.String(64))),
        ("span_id", sa.Column("span_id", sa.String(32))),
        ("previous_event_hash", sa.Column("previous_event_hash", sa.String(72))),
    ):
        op.add_column("audit_events", column)
    op.execute(
        """
        CREATE FUNCTION resolveflow_audit_append_only() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_events are append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_no_update_delete
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION resolveflow_audit_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update_delete ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS resolveflow_audit_append_only")
    for column in (
        "previous_event_hash", "span_id", "trace_id", "versions", "correlation_ids",
        "duration_ms", "outcome", "component", "actor_type", "actor_id",
    ):
        op.drop_column("audit_events", column)
    op.drop_table("action_attempts")
    op.drop_table("action_idempotency")
    op.drop_table("approvals")
    op.drop_index("ix_action_proposals_dispatch", table_name="action_proposals")
    op.drop_table("action_proposals")
    op.drop_index("ix_jobs_claim", table_name="jobs")
    op.drop_constraint("ck_jobs_attempt_bounds", "jobs", type_="check")
    op.drop_constraint("ck_jobs_state", "jobs", type_="check")
    op.drop_constraint("uq_jobs_logical_key", "jobs", type_="unique")
    for column in (
        "completed_at", "updated_at", "cancellation_requested", "last_error_code",
        "lease_expires_at", "lease_owner", "max_attempts", "attempt_count",
        "available_at", "logical_key", "run_id",
    ):
        op.drop_column("jobs", column)
