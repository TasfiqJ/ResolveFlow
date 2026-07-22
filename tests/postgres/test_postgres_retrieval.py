from __future__ import annotations

from datetime import datetime, timezone

import pytest
from resolveflow.retrieval.postgres import PostgreSQLSearchAdapter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = "postgresql+asyncpg://resolveflow:resolveflow@localhost:5432/resolveflow"


@pytest.mark.asyncio
async def test_postgresql_fts_and_pgvector_share_pre_authorized_relation() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 7, 15, 14, 22, tzinfo=timezone.utc)
    async with session_factory() as session:
        transaction = await session.begin()
        await session.execute(
            text("INSERT INTO tenants (tenant_id, display_name) VALUES (:id, 'Postgres test')"),
            {"id": "tenant_pg_retrieval_test"},
        )
        for suffix, classification, content, vector in (
            ("allowed", 1, "PYM-431 payments rollback procedure", "[1,0,0]"),
            ("restricted", 2, "PYM-431 restricted legal payments memo", "[1,0,0]"),
        ):
            await session.execute(
                text(
                    """INSERT INTO artifacts
                    (artifact_id, tenant_id, source_system, source_key, title, owner,
                     modality, checksum, created_at)
                    VALUES (:artifact, :tenant, 'test', :suffix, :title, 'test',
                            'text', :artifact_checksum, :now)"""
                ),
                {
                    "artifact": f"artifact_pg_{suffix}",
                    "tenant": "tenant_pg_retrieval_test",
                    "suffix": suffix,
                    "title": suffix,
                    "artifact_checksum": f"sha256:artifact_{suffix}",
                    "now": now,
                },
            )
            await session.execute(
                text(
                    """INSERT INTO artifact_versions
                    (artifact_version_id, artifact_id, version, source_path, source_checksum,
                     parser_name, parser_version, chunker_name, chunker_version,
                     parsing_quality, language, classification, effective_from, checksum,
                     created_at)
                    VALUES (:version, :artifact, '1', :suffix, :source_checksum,
                            'test', '1', 'test', '1', 'complete', 'en', :classification,
                            :effective_from, :version_checksum, :now)"""
                ),
                {
                    "version": f"version_pg_{suffix}",
                    "artifact": f"artifact_pg_{suffix}",
                    "suffix": suffix,
                    "source_checksum": f"sha256:source_{suffix}",
                    "classification": classification,
                    "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "version_checksum": f"sha256:version_{suffix}",
                    "now": now,
                },
            )
            await session.execute(
                text(
                    """INSERT INTO chunks
                    (chunk_id, artifact_version_id, ordinal, position_kind,
                     position_locator, content, token_count, checksum)
                    VALUES (:chunk, :version, 0, 'section', 'test', :content, 4, :checksum)"""
                ),
                {
                    "chunk": f"chunk_pg_{suffix}",
                    "version": f"version_pg_{suffix}",
                    "content": content,
                    "checksum": f"sha256:chunk_{suffix}",
                },
            )
            role = "contractor" if suffix == "allowed" else "incident_commander"
            await session.execute(
                text(
                    """INSERT INTO chunk_acls
                    (acl_id, chunk_id, tenant_id, role, region, policy_version, checksum)
                    VALUES (:acl, :chunk, :tenant, :role, 'ca-central',
                            'synthetic-acl-1.0', :checksum)"""
                ),
                {
                    "acl": f"acl_pg_{suffix}",
                    "chunk": f"chunk_pg_{suffix}",
                    "tenant": "tenant_pg_retrieval_test",
                    "role": role,
                    "checksum": f"sha256:acl_{suffix}",
                },
            )
            await session.execute(
                text(
                    """INSERT INTO embeddings
                    (embedding_id, chunk_id, model, dimension, input_type,
                     preprocessing_version, content_checksum, embedding, checksum)
                    VALUES (:embedding_id, :chunk, 'fixture', 3, 'search_document',
                            '1', :content_checksum, CAST(:vector AS vector), :checksum)"""
                ),
                {
                    "embedding_id": f"embedding_pg_{suffix}",
                    "chunk": f"chunk_pg_{suffix}",
                    "content_checksum": f"sha256:chunk_{suffix}",
                    "vector": vector,
                    "checksum": f"sha256:embedding_{suffix}",
                },
            )
        await session.execute(
            text(
                """INSERT INTO corpus_snapshots
                (snapshot_id, tenant_id, as_of, embedding_policy, checksum, created_at)
                VALUES ('snapshot_pg_test', :tenant, :now, 'fixture',
                        'sha256:snapshot_pg_test', :now)"""
            ),
            {"tenant": "tenant_pg_retrieval_test", "now": now},
        )
        for suffix in ("allowed", "restricted"):
            await session.execute(
                text(
                    """INSERT INTO corpus_snapshot_versions (snapshot_id, artifact_version_id)
                    VALUES ('snapshot_pg_test', :version)"""
                ),
                {"version": f"version_pg_{suffix}"},
            )

        parameters = {
            "tenant_id": "tenant_pg_retrieval_test",
            "role": "contractor",
            "region": "ca-central",
            "policy_version": "synthetic-acl-1.0",
            "maximum_classification": 1,
            "case_time": now,
            "corpus_snapshot_id": "snapshot_pg_test",
            "query": "payments rollback",
            "query_vector": "[1,0,0]",
            "candidate_k": 10,
        }
        adapter = PostgreSQLSearchAdapter(session)
        lexical = await adapter.lexical(parameters)
        vector = await adapter.vector(parameters)
        assert [item[0] for item in lexical] == ["chunk_pg_allowed"]
        assert [item[0] for item in vector] == ["chunk_pg_allowed"]
        await transaction.rollback()
    await engine.dispose()
