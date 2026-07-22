from __future__ import annotations

from resolveflow.retrieval.postgres import ELIGIBLE_CTE, LEXICAL_SQL, VECTOR_SQL


def test_both_postgresql_plans_rank_only_materialized_eligible_chunks() -> None:
    assert "eligible_chunks AS MATERIALIZED" in ELIGIBLE_CTE
    for sql in (LEXICAL_SQL, VECTOR_SQL):
        assert sql.startswith(ELIGIBLE_CTE)
        assert "acl.tenant_id = :tenant_id" in sql
        assert "acl.role = :role" in sql
        assert "acl.region = :region" in sql
        assert "csv.snapshot_id = :corpus_snapshot_id" in sql
    assert "websearch_to_tsquery" in LEXICAL_SQL
    assert "<=>" in VECTOR_SQL
