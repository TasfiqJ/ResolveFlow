from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ELIGIBLE_CTE = """
WITH eligible_chunks AS MATERIALIZED (
  SELECT c.chunk_id, c.artifact_version_id, c.content, c.content_tsv, e.embedding
  FROM chunks c
  JOIN artifact_versions av ON av.artifact_version_id = c.artifact_version_id
  JOIN artifacts a ON a.artifact_id = av.artifact_id
  JOIN chunk_acls acl ON acl.chunk_id = c.chunk_id
  JOIN embeddings e ON e.chunk_id = c.chunk_id
  JOIN corpus_snapshot_versions csv ON csv.artifact_version_id = av.artifact_version_id
  WHERE a.tenant_id = :tenant_id
    AND acl.tenant_id = :tenant_id
    AND acl.role = :role
    AND acl.region = :region
    AND acl.policy_version = :policy_version
    AND av.classification <= :maximum_classification
    AND av.effective_from <= :case_time
    AND (av.effective_to IS NULL OR :case_time < av.effective_to)
    AND csv.snapshot_id = :corpus_snapshot_id
)
"""

LEXICAL_SQL = (
    ELIGIBLE_CTE
    + """
SELECT chunk_id, ts_rank_cd(content_tsv, websearch_to_tsquery('simple', :query)) AS score
FROM eligible_chunks
WHERE content_tsv @@ websearch_to_tsquery('simple', :query)
ORDER BY score DESC, chunk_id
LIMIT :candidate_k
"""
)

VECTOR_SQL = (
    ELIGIBLE_CTE
    + """
SELECT chunk_id, 1 - (embedding <=> CAST(:query_vector AS vector)) AS score
FROM eligible_chunks
ORDER BY embedding <=> CAST(:query_vector AS vector), chunk_id
LIMIT :candidate_k
"""
)


class PostgreSQLSearchAdapter:
    """Runs both ranking methods only over the materialized eligible relation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lexical(self, parameters: dict[str, Any]) -> tuple[tuple[str, float], ...]:
        result = await self._session.execute(text(LEXICAL_SQL), parameters)
        return tuple((str(row.chunk_id), float(row.score)) for row in result)

    async def vector(self, parameters: dict[str, Any]) -> tuple[tuple[str, float], ...]:
        result = await self._session.execute(text(VECTOR_SQL), parameters)
        return tuple((str(row.chunk_id), float(row.score)) for row in result)
