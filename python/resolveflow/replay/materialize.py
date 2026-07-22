from __future__ import annotations

from pathlib import Path

from resolveflow.domain.evidence import Corpus
from resolveflow.domain.hashing import checksum
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.replay.io import load_manifest, load_truth
from resolveflow.replay.models import ChangedObject, MaterializedScenario, ReplayManifest
from resolveflow.replay.mutations import MutableWorld, apply_mutation


def _freeze_corpus(manifest: ReplayManifest) -> Corpus:
    corpus = load_hero_corpus()
    if manifest.frozen.corpus.corpus_checksum != corpus.snapshot.checksum:
        raise ValueError("frozen corpus checksum does not match the repository fixture")
    known = {item.artifact_version_id for item in corpus.versions}
    requested = set(manifest.frozen.corpus.artifact_version_ids)
    if not requested <= known:
        raise ValueError(f"frozen corpus references unknown versions: {sorted(requested - known)}")
    chunks = {item.chunk_id for item in corpus.chunks if item.artifact_version_id in requested}
    embedding_ids = tuple(
        sorted(item.embedding_id for item in corpus.embeddings if item.chunk_id in chunks)
    )
    old = corpus.snapshot
    body = {
        "snapshot_id": manifest.frozen.corpus.snapshot_id,
        "tenant_id": old.tenant_id,
        "as_of": manifest.frozen.clock,
        "artifact_version_ids": tuple(sorted(requested)),
        "embedding_ids": embedding_ids,
        "parser_versions": old.parser_versions,
        "chunker_versions": old.chunker_versions,
        "embedding_policy": old.embedding_policy,
        "created_at": manifest.frozen.clock,
    }
    return corpus.model_copy(update={"snapshot": old.__class__(**body, checksum=checksum(body))})


def materialize_scenario(manifest_or_path: ReplayManifest | Path) -> MaterializedScenario:
    manifest = (
        load_manifest(manifest_or_path) if isinstance(manifest_or_path, Path) else manifest_or_path
    )
    truth = load_truth(manifest.truth_id)
    case = canonical_hero_case().model_copy(
        update={
            "case_time": manifest.frozen.clock,
            "received_at": manifest.frozen.clock,
            "error_code": truth.error_code,
            "region": truth.region,
        }
    )
    case_body = case.model_dump(mode="python", exclude={"checksum"})
    case = case.model_copy(update={"checksum": checksum(case_body)})
    world = MutableWorld(
        case=case,
        corpus=_freeze_corpus(manifest),
        role=manifest.frozen.identity.role,
        region=manifest.frozen.identity.region,
        connector=manifest.frozen.connector,
    )
    changes: list[ChangedObject] = []
    for mutation in manifest.mutations:
        object_type, object_id, before, after = apply_mutation(world, mutation)
        changes.append(
            ChangedObject(
                object_type=object_type,
                object_id=object_id,
                before_hash=checksum(before),
                after_hash=checksum(after),
            )
        )
    identity = make_identity_snapshot(
        tenant_id=world.case.tenant_id,
        actor_id=manifest.frozen.identity.actor_id,
        role=world.role,
        region=world.region,
        case_time=manifest.frozen.clock,
    )
    if identity.policy_version != manifest.frozen.acl_policy_version:
        raise ValueError("frozen ACL policy does not match the materialized identity")
    if identity.policy_version != manifest.frozen.identity.policy_version:
        raise ValueError("frozen identity policy does not match the ACL policy")
    eligible = AuthorizationPolicy().eligible_chunk_ids(
        identity, world.corpus.versions, world.corpus.chunks, world.corpus.acls
    )
    acl = AuthorizationPolicy.snapshot(identity, world.corpus.snapshot.snapshot_id, eligible)
    rendered = {
        "case": checksum(world.case),
        "identity": checksum(identity),
        "acl": checksum(acl),
        "corpus": checksum(world.corpus.snapshot),
        "policy": checksum(manifest.frozen.model_policy),
        "connector": checksum(world.connector),
        "feature_flags": checksum(manifest.frozen.feature_flags),
    }
    body = {
        "manifest_checksum": manifest.checksum,
        "truth_checksum": truth.content_checksum,
        "rendered_input_hashes": rendered,
        "changed_objects": changes,
    }
    return MaterializedScenario(
        manifest=manifest,
        truth=truth,
        case=world.case,
        identity=identity,
        acl=acl,
        corpus=world.corpus,
        connector=world.connector,
        feature_flags=dict(sorted(manifest.frozen.feature_flags.items())),
        changed_objects=tuple(changes),
        rendered_input_hashes=rendered,
        materialization_checksum=checksum(body),
    )
