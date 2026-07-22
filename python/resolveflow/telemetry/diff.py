from __future__ import annotations

from typing import Any, Literal

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum


class DiffEntry(FrozenModel):
    path: str
    before: Any
    after: Any


class RunDiff(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    before_run_id: str
    after_run_id: str
    entries: tuple[DiffEntry, ...]
    checksum: str


_FOUNDATION_PATHS = (
    "identity_snapshot.active_role",
    "identity_snapshot.region",
    "corpus_version",
    "model_policy",
    "retrieval.candidates",
    "response.claim_ids",
    "action.state",
    "action.payload_digest",
    "metrics",
)


def diff_runs(before: Any, after: Any) -> RunDiff:
    left = _mapping(before)
    right = _mapping(after)
    entries = tuple(
        DiffEntry(path=path, before=old, after=new)
        for path in _FOUNDATION_PATHS
        if (old := _at(left, path)) != (new := _at(right, path))
    )
    body = {
        "before_run_id": str(left.get("run_id", "unknown")),
        "after_run_id": str(right.get("run_id", "unknown")),
        "entries": entries,
    }
    return RunDiff(**body, checksum=checksum(body))


def _mapping(value: Any) -> dict[str, Any]:
    mapped = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    if not isinstance(mapped, dict):
        raise TypeError("run diff inputs must be objects")
    return mapped


def _at(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
