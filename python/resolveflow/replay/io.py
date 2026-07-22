from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel

from resolveflow.domain.hashing import checksum
from resolveflow.replay.models import (
    BaseTruth,
    BaseTruthCatalog,
    BuildConfiguration,
    ReplayManifest,
)

ROOT = Path(__file__).resolve().parents[3]
TRUTH_CATALOG = ROOT / "data" / "truths" / "replay-base-truths-1.0.yaml"
MANIFEST_DIR = ROOT / "data" / "manifests"
BUILD_CONFIG = ROOT / "eval" / "configs" / "replay-builds-1.0.yaml"

ModelT = TypeVar("ModelT", bound=BaseModel)


def _yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return raw


def _validate_checksum(raw: dict[str, Any], *, path: Path) -> None:
    declared = raw.get("checksum")
    body = {key: value for key, value in raw.items() if key != "checksum"}
    actual = checksum(body)
    if declared != actual:
        raise ValueError(f"checksum mismatch for {path}: expected {declared}, computed {actual}")


def load_truth_catalog(path: Path = TRUTH_CATALOG) -> BaseTruthCatalog:
    raw = _yaml(path)
    _validate_checksum(raw, path=path)
    truths: list[BaseTruth] = []
    for item in raw.get("truths", []):
        if not isinstance(item, dict):
            raise ValueError("truth entries must be objects")
        body = {key: value for key, value in item.items() if key != "content_checksum"}
        computed = checksum(body)
        if item.get("content_checksum") not in {None, computed}:
            raise ValueError(f"truth checksum mismatch: {item.get('truth_id', 'unknown')}")
        truths.append(BaseTruth.model_validate({**body, "content_checksum": computed}))
    return BaseTruthCatalog.model_validate({**raw, "truths": truths})


def load_truth(truth_id: str, path: Path = TRUTH_CATALOG) -> BaseTruth:
    catalog = load_truth_catalog(path)
    match = next((item for item in catalog.truths if item.truth_id == truth_id), None)
    if match is None:
        raise ValueError(f"unknown truth_id: {truth_id}")
    return match


def load_manifest(path: Path) -> ReplayManifest:
    raw = _yaml(path)
    _validate_checksum(raw, path=path)
    manifest = ReplayManifest.model_validate(raw)
    truth = load_truth(manifest.truth_id)
    if manifest.truth_checksum != truth.content_checksum:
        raise ValueError("manifest truth checksum does not match the referenced base truth")
    return manifest


def manifest_path(manifest_id: str) -> Path:
    candidates = tuple(MANIFEST_DIR.glob("*.yaml"))
    for path in candidates:
        raw = _yaml(path)
        if raw.get("manifest_id") == manifest_id:
            return path
    raise ValueError(f"unknown predefined manifest: {manifest_id}")


def load_build_config(build_id: str, path: Path = BUILD_CONFIG) -> BuildConfiguration:
    raw = _yaml(path)
    _validate_checksum(raw, path=path)
    for item in raw.get("builds", []):
        if item.get("build_id") != build_id:
            continue
        body = {key: value for key, value in item.items() if key != "checksum"}
        if item.get("checksum") != checksum(body):
            raise ValueError(f"build configuration checksum mismatch: {build_id}")
        return BuildConfiguration.model_validate(item)
    raise ValueError(f"unknown Replay build configuration: {build_id}")
