from __future__ import annotations

import argparse
import re
from pathlib import Path

TOKEN_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(rb"ATATT[0-9A-Za-z_-]{20,}"),
    re.compile(rb"postgres(?:ql)?://[^\s\"']+:[^\s\"']+@"),
)
FORBIDDEN_CONFIG_NAMES = (
    b"COHERE_API_KEY",
    b"SLACK_SIGNING_SECRET",
    b"JIRA_API_TOKEN",
    b"DATABASE_URL",
)


def scan(path: Path) -> list[str]:
    errors: list[str] = []
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        data = candidate.read_bytes()
        for pattern in TOKEN_PATTERNS:
            if pattern.search(data):
                errors.append(f"secret-like value in {candidate}")
        for name in FORBIDDEN_CONFIG_NAMES:
            if name in data:
                errors.append(f"server-only configuration name {name.decode()} in {candidate}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    if not args.path.is_dir():
        raise SystemExit(f"public build path does not exist: {args.path}")
    errors = scan(args.path)
    if errors:
        raise SystemExit("Public bundle scan failed:\n- " + "\n- ".join(errors))
    print(f"Public bundle scan passed: {args.path}")


if __name__ == "__main__":
    main()
