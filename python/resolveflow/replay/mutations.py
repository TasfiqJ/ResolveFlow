from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from resolveflow.domain.evidence import Corpus
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import CanonicalCase
from resolveflow.replay.models import FrozenConnector, MutationType, ReplayMutation


@dataclass
class MutableWorld:
    case: CanonicalCase
    corpus: Corpus
    role: str
    region: str
    connector: FrozenConnector


MutationHandler = Callable[[MutableWorld, dict[str, Any]], tuple[str, str, object, object]]


def _require(parameters: dict[str, Any], key: str, expected: type) -> Any:
    value = parameters.get(key)
    if not isinstance(value, expected):
        raise ValueError(f"mutation parameter {key!r} must be {expected.__name__}")
    return value


def _role_override(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    role = _require(parameters, "role", str)
    if role not in {"incident_commander", "contractor"}:
        raise ValueError("role_override.role is not registered")
    before = {"role": world.role, "region": world.region}
    world.role = role
    if "region" in parameters:
        world.region = _require(parameters, "region", str)
    return "identity", "active_identity", before, {"role": world.role, "region": world.region}


def _snapshot_versions(world: MutableWorld, version_ids: tuple[str, ...]) -> None:
    chunks = {
        item.chunk_id
        for item in world.corpus.chunks
        if item.artifact_version_id in set(version_ids)
    }
    embedding_ids = tuple(
        sorted(item.embedding_id for item in world.corpus.embeddings if item.chunk_id in chunks)
    )
    old = world.corpus.snapshot
    body = {
        "snapshot_id": f"replay_{checksum(version_ids).split(':', 1)[1][:20]}",
        "tenant_id": old.tenant_id,
        "as_of": world.case.case_time,
        "artifact_version_ids": tuple(sorted(version_ids)),
        "embedding_ids": embedding_ids,
        "parser_versions": old.parser_versions,
        "chunker_versions": old.chunker_versions,
        "embedding_policy": old.embedding_policy,
        "created_at": world.case.case_time,
    }
    world.corpus = world.corpus.model_copy(
        update={"snapshot": old.__class__(**body, checksum=checksum(body))}
    )


def _add_artifact(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    version_id = _require(parameters, "artifact_version_id", str)
    known = {item.artifact_version_id for item in world.corpus.versions}
    if version_id not in known:
        raise ValueError(f"unknown artifact version: {version_id}")
    before = world.corpus.snapshot
    current = set(before.artifact_version_ids)
    if version_id in current:
        raise ValueError("add_artifact target is already in the frozen corpus")
    current.add(version_id)
    _snapshot_versions(world, tuple(current))
    return "corpus_snapshot", before.snapshot_id, before, world.corpus.snapshot


def _hide_artifact(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    artifact_id = parameters.get("artifact_id")
    version_id = parameters.get("artifact_version_id")
    if not isinstance(artifact_id, str) and not isinstance(version_id, str):
        raise ValueError("hide_artifact requires artifact_id or artifact_version_id")
    version_by_id = {item.artifact_version_id: item for item in world.corpus.versions}
    before = world.corpus.snapshot
    retained = tuple(
        item
        for item in before.artifact_version_ids
        if item != version_id
        and (artifact_id is None or version_by_id[item].artifact_id != artifact_id)
    )
    if retained == before.artifact_version_ids:
        raise ValueError("hide_artifact did not match a frozen artifact")
    _snapshot_versions(world, retained)
    return "corpus_snapshot", before.snapshot_id, before, world.corpus.snapshot


def _promote_stale(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    version_id = _require(parameters, "artifact_version_id", str)
    versions = list(world.corpus.versions)
    index = next(
        (index for index, item in enumerate(versions) if item.artifact_version_id == version_id),
        None,
    )
    if index is None:
        raise ValueError(f"unknown stale version: {version_id}")
    stale = versions[index]
    before = {"version": stale, "snapshot": world.corpus.snapshot}
    promoted_body = {
        **stale.model_dump(mode="python", exclude={"checksum"}),
        "effective_from": world.case.case_time - timedelta(days=1),
        "effective_to": None,
    }
    versions[index] = stale.__class__(**promoted_body, checksum=checksum(promoted_body))
    sibling_ids = {
        item.artifact_version_id
        for item in versions
        if item.artifact_id == stale.artifact_id and item.artifact_version_id != version_id
    }
    retained = {
        item for item in world.corpus.snapshot.artifact_version_ids if item not in sibling_ids
    }
    retained.add(version_id)
    world.corpus = world.corpus.model_copy(update={"versions": tuple(versions)})
    _snapshot_versions(world, tuple(retained))
    after = {"version": versions[index], "snapshot": world.corpus.snapshot}
    return "artifact_version", version_id, before, after


def _replace_image(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    version_id = _require(parameters, "artifact_version_id", str)
    version = next(
        (item for item in world.corpus.versions if item.artifact_version_id == version_id), None
    )
    if version is None:
        raise ValueError(f"unknown image version: {version_id}")
    artifact = next(
        item for item in world.corpus.artifacts if item.artifact_id == version.artifact_id
    )
    if artifact.modality != "image":
        raise ValueError("replace_image requires a registered image fixture")
    return _add_artifact(world, parameters)


def _connector_state(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    state = _require(parameters, "state", str)
    if state not in {"healthy", "timeout", "unavailable", "uncertain"}:
        raise ValueError("connector_state.state is not registered")
    before = world.connector
    world.connector = before.model_copy(update={"jira": state})
    return "connector", "jira", before, world.connector


def _language_variant(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    variant_id = _require(parameters, "variant_id", str)
    raise ValueError(f"language variant {variant_id!r} is unavailable pending fluent human review")


def _field_removal(
    world: MutableWorld, parameters: dict[str, Any]
) -> tuple[str, str, object, object]:
    field = _require(parameters, "field", str)
    before = world.case
    if field == "error_code":
        text = before.raw_text.replace(before.error_code, "[error code omitted]")
        body = before.model_dump(mode="python", exclude={"checksum"})
        body.update({"raw_text": text, "error_code": "UNKNOWN"})
    elif field == "cluster_id":
        if "cluster_id" in before.missing_fields:
            raise ValueError("cluster_id is already absent from this base truth")
        body = before.model_dump(mode="python", exclude={"checksum"})
        body["missing_fields"] = tuple(sorted((*before.missing_fields, "cluster_id")))
    else:
        raise ValueError("field_removal.field is not registered")
    world.case = before.__class__(**body, checksum=checksum(body))
    return "canonical_case", before.case_id, before, world.case


MUTATION_REGISTRY: dict[MutationType, MutationHandler] = {
    MutationType.ROLE_OVERRIDE: _role_override,
    MutationType.ADD_ARTIFACT: _add_artifact,
    MutationType.HIDE_ARTIFACT: _hide_artifact,
    MutationType.PROMOTE_STALE: _promote_stale,
    MutationType.REPLACE_IMAGE: _replace_image,
    MutationType.CONNECTOR_STATE: _connector_state,
    MutationType.LANGUAGE_VARIANT: _language_variant,
    MutationType.FIELD_REMOVAL: _field_removal,
}


def apply_mutation(
    world: MutableWorld, mutation: ReplayMutation
) -> tuple[str, str, object, object]:
    handler = MUTATION_REGISTRY.get(mutation.type)
    if handler is None:
        raise ValueError(f"unregistered mutation type: {mutation.type}")
    return handler(world, mutation.parameters)
