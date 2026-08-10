"""Partial indexes that actually serve the job-claim predicate.

`ix_jobs_claim` is `(status, available_at, lease_expires_at, created_at)`, but the claim
query in `PostgreSQLActionRepository.claim` filters on `cancellation_requested`, `kind`
and `attempt_count < max_attempts`, then ORs across two different status/timestamp pairs
before `ORDER BY available_at, created_at, job_id`. An OR across two ranges is not
indexable as one scan and `available_at` is not the leading column, so the planner falls
back to Seq Scan + Sort over the whole table -- including every completed and
dead-lettered row, which nothing prunes. With N workers polling that is N full scans per
tick.

Each arm of the OR gets its own partial index here, leading with `kind` (the one
selective column the worker always supplies) and continuing in the query's sort order so
the ORDER BY is satisfied by the scan. Both are partial on `cancellation_requested =
false`, which keeps completed and cancelled history out of the index entirely.

Revision ID: 0006_job_claim_indexes
Revises: 0005_replay_release_gate
"""

from alembic import op

revision = "0006_job_claim_indexes"
down_revision = "0005_replay_release_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_jobs_claim_ready ON jobs (kind, available_at, created_at, job_id)
        WHERE cancellation_requested = false AND status IN ('queued', 'retry_wait')
        """
    )
    op.execute(
        """
        CREATE INDEX ix_jobs_claim_expired ON jobs
            (kind, lease_expires_at, available_at, created_at, job_id)
        WHERE cancellation_requested = false AND status IN ('leased', 'running')
        """
    )
    # Superseded by the two partial indexes above.
    op.drop_index("ix_jobs_claim", table_name="jobs")


def downgrade() -> None:
    op.create_index(
        "ix_jobs_claim",
        "jobs",
        ["status", "available_at", "lease_expires_at", "created_at"],
    )
    op.execute("DROP INDEX IF EXISTS ix_jobs_claim_expired")
    op.execute("DROP INDEX IF EXISTS ix_jobs_claim_ready")
