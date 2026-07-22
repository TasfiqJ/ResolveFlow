from __future__ import annotations

from datetime import datetime

from resolveflow.domain.evidence import (
    ACLSnapshot,
    ArtifactVersion,
    Chunk,
    ChunkACL,
    Classification,
    IdentitySnapshot,
    stable_id,
)
from resolveflow.domain.hashing import checksum


def make_identity_snapshot(
    *, tenant_id: str, actor_id: str, role: str, region: str, case_time: datetime
) -> IdentitySnapshot:
    maximum = Classification.RESTRICTED if role == "incident_commander" else Classification.INTERNAL
    body = {
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "active_role": role,
        "region": region,
        "maximum_classification": maximum,
        "policy_version": "synthetic-acl-1.0",
        "case_time": case_time,
        "created_at": case_time,
    }
    return IdentitySnapshot(
        **body,
        snapshot_id=stable_id("identity", body),
        checksum=checksum(body),
    )


class AuthorizationPolicy:
    """Model-external pre-retrieval eligibility policy with deny-by-default behavior."""

    def eligible_chunk_ids(
        self,
        identity: IdentitySnapshot,
        versions: tuple[ArtifactVersion, ...],
        chunks: tuple[Chunk, ...],
        acls: tuple[ChunkACL, ...],
    ) -> frozenset[str]:
        version_by_id = {item.artifact_version_id: item for item in versions}
        acl_chunk_ids = {
            acl.chunk_id
            for acl in acls
            if acl.tenant_id == identity.tenant_id
            and acl.role == identity.active_role
            and acl.region == identity.region
            and acl.policy_version == identity.policy_version
        }
        eligible: set[str] = set()
        for chunk in chunks:
            version = version_by_id.get(chunk.artifact_version_id)
            if version is None or chunk.chunk_id not in acl_chunk_ids:
                continue
            effective = version.effective_from <= identity.case_time and (
                version.effective_to is None or identity.case_time < version.effective_to
            )
            if effective and version.classification <= identity.maximum_classification:
                eligible.add(chunk.chunk_id)
        return frozenset(eligible)

    @staticmethod
    def cache_key(identity: IdentitySnapshot, corpus_snapshot_id: str, query: str) -> str:
        return checksum(
            {
                "tenant_id": identity.tenant_id,
                "role": identity.active_role,
                "region": identity.region,
                "policy_version": identity.policy_version,
                "identity_snapshot_id": identity.snapshot_id,
                "corpus_snapshot_id": corpus_snapshot_id,
                "query": query,
            }
        )

    @staticmethod
    def snapshot(
        identity: IdentitySnapshot,
        corpus_snapshot_id: str,
        eligible_chunk_ids: frozenset[str],
    ) -> ACLSnapshot:
        body = {
            "identity_snapshot_id": identity.snapshot_id,
            "corpus_snapshot_id": corpus_snapshot_id,
            "eligible_chunk_ids": tuple(sorted(eligible_chunk_ids)),
            "policy_version": identity.policy_version,
            "created_at": identity.created_at,
        }
        return ACLSnapshot(
            **body, snapshot_id=stable_id("acl_snapshot", body), checksum=checksum(body)
        )
