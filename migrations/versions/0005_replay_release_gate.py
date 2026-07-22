"""Replay scenarios, metrics, comparisons, gates, and result bundles.

Revision ID: 0005_replay_release_gate
Revises: 0004_actions_reliability_audit
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_replay_release_gate"
down_revision = "0004_actions_reliability_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "replay_base_truths",
        sa.Column("truth_id", sa.String(96), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("split", sa.String(40), nullable=False),
        sa.Column("lock_status", sa.String(40), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("content_checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("lock_status = 'DRAFT_NOT_LOCKED'", name="ck_truth_not_falsely_locked"),
    )
    op.create_table(
        "replay_scenarios",
        sa.Column("scenario_id", sa.String(96), primary_key=True),
        sa.Column("truth_id", sa.String(96), sa.ForeignKey("replay_base_truths.truth_id")),
        sa.Column("manifest_id", sa.String(96), nullable=False, unique=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("manifest_checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "replay_expectations",
        sa.Column("expectation_id", sa.String(96), primary_key=True),
        sa.Column("scenario_id", sa.String(96), sa.ForeignKey("replay_scenarios.scenario_id")),
        sa.Column("invariant_id", sa.String(96), nullable=False),
        sa.Column("expected", sa.JSON(), nullable=False),
        sa.UniqueConstraint("scenario_id", "invariant_id", name="uq_replay_expectation"),
    )
    op.create_table(
        "replay_runs",
        sa.Column("replay_run_id", sa.String(96), primary_key=True),
        sa.Column("scenario_id", sa.String(96), sa.ForeignKey("replay_scenarios.scenario_id")),
        sa.Column("baseline_run_id", sa.String(64), nullable=False),
        sa.Column("candidate_run_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("materialization_checksum", sa.String(72), nullable=False),
        sa.Column("result_checksum", sa.String(72)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('queued','preparing','running','scoring','completed','failed','cancelled')",
            name="ck_replay_run_status",
        ),
    )
    op.create_table(
        "metric_observations",
        sa.Column("observation_id", sa.String(96), primary_key=True),
        sa.Column("replay_run_id", sa.String(96), sa.ForeignKey("replay_runs.replay_run_id")),
        sa.Column("metric_id", sa.String(96), nullable=False),
        sa.Column("metric_version", sa.String(40), nullable=False),
        sa.Column("numerator", sa.Integer(), nullable=False),
        sa.Column("denominator", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.JSON(), nullable=False),
        sa.Column("source_run_ids", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.CheckConstraint("denominator > 0", name="ck_metric_denominator_positive"),
        sa.CheckConstraint("numerator >= 0 AND numerator <= denominator", name="ck_metric_ratio"),
    )
    op.create_table(
        "experiment_comparisons",
        sa.Column("comparison_id", sa.String(96), primary_key=True),
        sa.Column("replay_run_id", sa.String(96), sa.ForeignKey("replay_runs.replay_run_id")),
        sa.Column("baseline_build", sa.String(64), nullable=False),
        sa.Column("candidate_build", sa.String(64), nullable=False),
        sa.Column("paired_results", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
    )
    op.create_table(
        "release_gates",
        sa.Column("gate_id", sa.String(96), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("registration_status", sa.String(64), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "result_bundles",
        sa.Column("bundle_id", sa.String(120), primary_key=True),
        sa.Column("replay_run_id", sa.String(96), sa.ForeignKey("replay_runs.replay_run_id")),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("publishable_as_final_release", sa.Boolean(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "verdict IN ('SHIP','SHIP_WITH_LIMITS','NO_SHIP')", name="ck_release_verdict"
        ),
        sa.CheckConstraint(
            "publishable_as_final_release = false", name="ck_draft_bundle_not_final_release"
        ),
    )


def downgrade() -> None:
    op.drop_table("result_bundles")
    op.drop_table("release_gates")
    op.drop_table("experiment_comparisons")
    op.drop_table("metric_observations")
    op.drop_table("replay_runs")
    op.drop_table("replay_expectations")
    op.drop_table("replay_scenarios")
    op.drop_table("replay_base_truths")
