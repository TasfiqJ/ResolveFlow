from __future__ import annotations

import json
from pathlib import Path

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
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
    print("Public snapshot integrity passed: hero and Replay result checksums verified")


if __name__ == "__main__":
    main()
