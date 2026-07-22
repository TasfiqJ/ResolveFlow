from __future__ import annotations

import pytest
from pydantic import ValidationError
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot


def test_corpus_and_policy_snapshot_models_are_immutable() -> None:
    corpus = load_hero_corpus()
    identity = make_identity_snapshot(
        tenant_id=corpus.snapshot.tenant_id,
        actor_id="immutable-test",
        role="contractor",
        region="ca-central",
        case_time=corpus.snapshot.as_of,
    )
    eligible = AuthorizationPolicy().eligible_chunk_ids(
        identity, corpus.versions, corpus.chunks, corpus.acls
    )
    acl_snapshot = AuthorizationPolicy.snapshot(identity, corpus.snapshot.snapshot_id, eligible)
    with pytest.raises(ValidationError):
        identity.active_role = "incident_commander"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        acl_snapshot.eligible_chunk_ids = ()  # type: ignore[misc]
