from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.evaluation.models import ReleaseGateDefinition, ResultBundle

ROOT = Path(__file__).resolve().parents[3]
GATE_PATH = ROOT / "eval" / "configs" / "release-gate-1.0.yaml"


def load_gate(path: Path = GATE_PATH) -> ReleaseGateDefinition:
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("release gate YAML root must be an object")
    body = {key: value for key, value in raw.items() if key != "checksum"}
    if raw.get("checksum") != checksum(body):
        raise ValueError("release gate checksum mismatch")
    return ReleaseGateDefinition.model_validate(raw)


def write_bundle(bundle: ResultBundle, output: Path) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8")
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return output, checksum_path


def verify_bundle_file(path: Path) -> ResultBundle:
    raw = json.loads(path.read_text(encoding="utf-8"))
    bundle = ResultBundle.model_validate(raw)
    body = bundle.model_dump(mode="python", exclude={"checksum"})
    if bundle.checksum != checksum(body):
        raise ValueError("result bundle canonical checksum mismatch")
    checksum_path = path.with_suffix(path.suffix + ".sha256")
    expected = checksum_path.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise ValueError("result bundle file checksum mismatch")
    return bundle


def bundle_canonical_payload(bundle: ResultBundle) -> str:
    return canonical_json(bundle.model_dump(mode="python", exclude={"checksum"}))
