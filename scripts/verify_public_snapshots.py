from __future__ import annotations

import hashlib
import json
from pathlib import Path

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.evaluation.integrity import EvaluationIntegrityAudit
from resolveflow.evaluation.io import verify_bundle_file


def main() -> None:
    hero_path = Path("data/published/hero-foundation.json")
    hero = RunSnapshot.model_validate(json.loads(hero_path.read_text(encoding="utf-8")))
    if checksum(hero.model_dump(mode="python", exclude={"content_hash"})) != hero.content_hash:
        raise SystemExit("hero snapshot content hash mismatch")
    web_hero = Path("apps/web/public/snapshots/hero-foundation.json")
    if web_hero.read_bytes() != hero_path.read_bytes():
        raise SystemExit("web hero snapshot differs from canonical published snapshot")
    result_path = Path("data/published/replay-development-result.json")
    verify_bundle_file(result_path)
    web_result = Path("apps/web/public/snapshots/replay-development-result.json")
    if web_result.read_bytes() != result_path.read_bytes():
        raise SystemExit("web result snapshot differs from canonical published result")
    audit_path = Path("data/published/evaluation-integrity-audit.json")
    audit = EvaluationIntegrityAudit.model_validate(
        json.loads(audit_path.read_text(encoding="utf-8"))
    )
    if checksum(audit.model_dump(mode="python", exclude={"checksum"})) != audit.checksum:
        raise SystemExit("evaluation integrity audit canonical checksum mismatch")
    expected_file_hash = audit_path.with_suffix(".json.sha256").read_text().split()[0]
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != expected_file_hash:
        raise SystemExit("evaluation integrity audit file checksum mismatch")
    web_audit = Path("apps/web/public/snapshots/evaluation-integrity-audit.json")
    if web_audit.read_bytes() != audit_path.read_bytes():
        raise SystemExit("web evaluation integrity audit differs from canonical artifact")
    print(
        "Public snapshot integrity passed: hero, Replay result, and evaluation "
        "integrity checksums verified"
    )


if __name__ == "__main__":
    main()
