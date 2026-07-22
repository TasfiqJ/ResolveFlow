from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_release_profile import validate_release_profile
from resolveflow.cli import preflight as application_preflight

ROOT = Path(__file__).resolve().parents[1]


def strict_release_checks() -> None:
    required = [
        ROOT / "CODEX_FINAL_REPORT.md",
        ROOT / "docs" / "RELEASE_CHECKLIST.md",
        ROOT / "docs" / "KNOWN_LIMITATIONS.md",
        ROOT / "docs" / "threat-model.md",
        ROOT / "docs" / "deployment-runbook.md",
        ROOT / "docs" / "HUMAN_SIGNOFF.json",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"strict preflight missing release files: {', '.join(missing)}")

    gate = json.loads((ROOT / "docs" / "HUMAN_SIGNOFF.json").read_text(encoding="utf-8"))
    profile = validate_release_profile(gate)

    public_sources = [
        ROOT / "apps" / "web" / "app" / "page.tsx",
        ROOT / "apps" / "web" / "app" / "results" / "page.tsx",
        ROOT / "apps" / "web" / "app" / "about" / "page.tsx",
    ]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_sources)
    if profile == "technical_preview":
        required_copy = [
            "Technical preview",
            "human validation remains pending",
            "technical preview only",
            "does not claim",
        ]
        missing_copy = [phrase for phrase in required_copy if phrase not in public_text]
        if missing_copy:
            raise SystemExit(
                "technical-preview public copy is incomplete: " + ", ".join(missing_copy)
            )

    print(f"Strict release preflight passed: {profile}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ResolveFlow release preflight")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    application_preflight()
    if args.strict:
        strict_release_checks()


if __name__ == "__main__":
    main()
