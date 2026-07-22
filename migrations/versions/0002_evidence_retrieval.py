"""Versioned evidence, ACL snapshots, pgvector, and retrieval traces.

Revision ID: 0002_evidence_retrieval
Revises: 0001_foundation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

revision = "0002_evidence_retrieval"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.String(96), primary_key=True),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("source_key", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("owner", sa.String(200), nullable=False),
        sa.Column("modality", sa.String(20), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "source_system", "source_key", name="uq_artifact_source"),
    )
    op.create_table(
        "artifact_versions",
        sa.Column("artifact_version_id", sa.String(120), primary_key=True),
        sa.Column("artifact_id", sa.String(96), sa.ForeignKey("artifacts.artifact_id"), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_checksum", sa.String(72), nullable=False),
        sa.Column("parser_name", sa.String(100), nullable=False),
        sa.Column("parser_version", sa.String(40), nullable=False),
        sa.Column("chunker_name", sa.String(100), nullable=False),
        sa.Column("chunker_version", sa.String(40), nullable=False),
        sa.Column("parsing_quality", sa.String(20), nullable=False),
        sa.Column("language", sa.String(12), nullable=False),
        sa.Column("classification", sa.SmallInteger(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_effective_interval"),
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_version"),
    )
    op.create_table(
        "chunks",
        sa.Column("chunk_id", sa.String(96), primary_key=True),
        sa.Column("artifact_version_id", sa.String(120), sa.ForeignKey("artifact_versions.artifact_version_id"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("position_kind", sa.String(20), nullable=False),
        sa.Column("position_locator", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_tsv", TSVECTOR(), sa.Computed("to_tsvector('simple', content)", persisted=True)),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.CheckConstraint("length(btrim(content)) > 0", name="ck_chunk_nonempty"),
        sa.UniqueConstraint("artifact_version_id", "ordinal", name="uq_chunk_ordinal"),
    )
    op.create_index("ix_chunks_content_tsv", "chunks", ["content_tsv"], postgresql_using="gin")
    op.create_table(
        "chunk_acls",
        sa.Column("acl_id", sa.String(96), primary_key=True),
        sa.Column("chunk_id", sa.String(96), sa.ForeignKey("chunks.chunk_id"), nullable=False),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.UniqueConstraint("chunk_id", "tenant_id", "role", "region", "policy_version", name="uq_chunk_acl_rule"),
    )
    op.create_index("ix_chunk_acls_eligibility", "chunk_acls", ["tenant_id", "role", "region", "policy_version", "chunk_id"])
    op.create_table(
        "embeddings",
        sa.Column("embedding_id", sa.String(96), primary_key=True),
        sa.Column("chunk_id", sa.String(96), sa.ForeignKey("chunks.chunk_id"), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("input_type", sa.String(30), nullable=False),
        sa.Column("preprocessing_version", sa.String(64), nullable=False),
        sa.Column("content_checksum", sa.String(72), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.UniqueConstraint("chunk_id", "model", "dimension", "input_type", "preprocessing_version", "content_checksum", name="uq_embedding_cache"),
    )
    op.execute("ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector USING embedding::vector")
    op.create_table(
        "corpus_snapshots",
        sa.Column("snapshot_id", sa.String(96), primary_key=True),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("embedding_policy", sa.String(100), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "corpus_snapshot_versions",
        sa.Column("snapshot_id", sa.String(96), sa.ForeignKey("corpus_snapshots.snapshot_id"), primary_key=True),
        sa.Column("artifact_version_id", sa.String(120), sa.ForeignKey("artifact_versions.artifact_version_id"), primary_key=True),
    )
    op.create_table(
        "identity_snapshots",
        sa.Column("snapshot_id", sa.String(96), primary_key=True),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("actor_id", sa.String(96), nullable=False),
        sa.Column("active_role", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("maximum_classification", sa.SmallInteger(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("case_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "acl_snapshots",
        sa.Column("snapshot_id", sa.String(96), primary_key=True),
        sa.Column(
            "identity_snapshot_id",
            sa.String(96),
            sa.ForeignKey("identity_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "corpus_snapshot_id",
            sa.String(96),
            sa.ForeignKey("corpus_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column("eligible_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("checksum", sa.String(72), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "retrieval_candidates",
        sa.Column("run_id", sa.String(64), sa.ForeignKey("agent_runs.run_id"), primary_key=True),
        sa.Column("chunk_id", sa.String(96), sa.ForeignKey("chunks.chunk_id"), primary_key=True),
        sa.Column("lexical_rank", sa.Integer()),
        sa.Column("lexical_score", sa.Float()),
        sa.Column("vector_rank", sa.Integer()),
        sa.Column("vector_score", sa.Float()),
        sa.Column("fused_rank", sa.Integer(), nullable=False),
        sa.Column("fused_score", sa.Float(), nullable=False),
        sa.Column("rerank_rank", sa.Integer()),
        sa.Column("rerank_score", sa.Float()),
        sa.Column("provenance_checksum", sa.String(72), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("retrieval_candidates")
    op.execute("DROP TABLE IF EXISTS acl_snapshots")
    op.drop_table("identity_snapshots")
    op.drop_table("corpus_snapshot_versions")
    op.drop_table("corpus_snapshots")
    op.drop_table("embeddings")
    op.drop_index("ix_chunk_acls_eligibility", table_name="chunk_acls")
    op.drop_table("chunk_acls")
    op.drop_index("ix_chunks_content_tsv", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("artifact_versions")
    op.drop_table("artifacts")
