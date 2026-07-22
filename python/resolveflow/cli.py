from __future__ import annotations

import json
from pathlib import Path

from resolveflow.agent.fixture import FixtureAgent
from resolveflow.config import Settings
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator

ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = ROOT / "data" / "published"


def build_snapshot() -> dict[str, object]:
    snapshot = ResolveOrchestrator(FixtureContextRepository(), FixtureAgent()).run(
        canonical_hero_case()
    )
    return snapshot.model_dump(mode="json")


def _write_snapshot() -> Path:
    snapshot = build_snapshot()
    content_hash = str(snapshot["content_hash"]).split(":", 1)[1][:16]
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    content_path = PUBLISHED / f"hero-foundation-{content_hash}.json"
    latest_path = PUBLISHED / "hero-foundation.json"
    rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    content_path.write_text(rendered, encoding="utf-8")
    latest_path.write_text(rendered, encoding="utf-8")
    web_path = ROOT / "apps" / "web" / "public" / "snapshots" / "hero-foundation.json"
    web_path.parent.mkdir(parents=True, exist_ok=True)
    web_path.write_text(rendered, encoding="utf-8")
    return latest_path


def seed() -> None:
    print(f"Seeded deterministic hero fixture: {_write_snapshot()}")


def snapshot() -> None:
    print(f"Published recorded hero snapshot: {_write_snapshot()}")


def preflight() -> None:
    Settings(environment="public")
    path = _write_snapshot()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if loaded["provenance"] != "recorded_fixture":
        raise SystemExit("snapshot provenance is not recorded_fixture")
    print(f"Preflight passed: {path}")
