from __future__ import annotations

from datetime import datetime

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot


def test_t0_sees_only_effective_artifact_versions() -> None:
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=corpus.snapshot.tenant_id,
        actor_id="operator",
        role="incident_commander",
        region="ca-central",
        case_time=datetime.fromisoformat("2026-07-15T14:22:00+00:00"),
    )
    eligible = AuthorizationPolicy().eligible_chunk_ids(
        identity, corpus.versions, corpus.chunks, corpus.acls
    )
    versions = {chunk.artifact_version_id for chunk in corpus.chunks if chunk.chunk_id in eligible}
    assert "artifact_runbook_payments_v3" in versions
    assert "artifact_runbook_payments_v2" not in versions
