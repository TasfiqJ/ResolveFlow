from __future__ import annotations

from resolveflow.domain.evidence import ArtifactVersion, Chunk, ChunkACL, IdentitySnapshot
from resolveflow.policy.authorization import AuthorizationPolicy


class UnsafeReplayAuthorizationPolicy(AuthorizationPolicy):
    """Deliberately unsafe prompt-only baseline, confined to deterministic Replay."""

    def eligible_chunk_ids(
        self,
        identity: IdentitySnapshot,
        versions: tuple[ArtifactVersion, ...],
        chunks: tuple[Chunk, ...],
        acls: tuple[ChunkACL, ...],
    ) -> frozenset[str]:
        del acls
        version_by_id = {item.artifact_version_id: item for item in versions}
        return frozenset(
            chunk.chunk_id
            for chunk in chunks
            if (version := version_by_id.get(chunk.artifact_version_id)) is not None
            and version.effective_from <= identity.case_time
            and (version.effective_to is None or identity.case_time < version.effective_to)
        )
