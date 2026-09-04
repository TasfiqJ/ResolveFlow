"""Verify a published SHA256SUMS manifest against the files on disk.

A checksum manifest is only evidence if something re-computes it. This module
re-reads every row of `eval/results/SHA256SUMS-<provider>.md`, hashes the file
the row names, and reports any row whose digest, size, or file no longer
matches. It exits non-zero on the first category of mismatch so it can be used
as a gate.

It also checks the reverse direction: an artifact that exists on disk for this
provider but appears in no row. A manifest that silently omits a file is a
manifest that can vouch for a subset while a reader assumes it covers the whole
run -- which is the failure that let a previous manifest list one provider's
files under another provider's heading.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from resolveflow.eval.publish import RESULTS_DIR, artifact_paths, sha256_file
from resolveflow.ingestion.fixtures import ROOT

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*(\d+)\s*\|\s*$")


def parse_manifest(path: Path) -> list[tuple[str, str, int]]:
    provider = path.stem.removeprefix("SHA256SUMS-")
    expected_header = [
        f"# Artifact checksums ({provider} provider)",
        "",
        "| Artifact | SHA-256 | Bytes |",
        "| --- | --- | --- |",
    ]
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines[:4] != expected_header:
        raise ValueError("checksum manifest header is invalid")
    if len(lines) == 4:
        raise ValueError("checksum manifest contains no artifact rows")
    rows: list[tuple[str, str, int]] = []
    for line_number, line in enumerate(lines[4:], start=5):
        match = ROW.match(line.strip())
        if not match:
            raise ValueError(f"checksum manifest line {line_number} is invalid")
        rows.append((match.group(1), match.group(2), int(match.group(3))))
    return rows


def verify(provider: str) -> dict[str, Any]:
    manifest_path = RESULTS_DIR / f"SHA256SUMS-{provider}.md"
    if not manifest_path.exists():
        return {"provider": provider, "error": f"missing manifest {manifest_path}"}

    manifest_format_errors: list[str] = []
    try:
        rows = parse_manifest(manifest_path)
    except ValueError as exc:
        rows = []
        manifest_format_errors.append(str(exc))
    missing: list[str] = []
    digest_mismatch: list[dict[str, str]] = []
    size_mismatch: list[dict[str, Any]] = []
    invalid_paths: list[str] = []
    verified: list[str] = []

    for relative, expected_digest, expected_size in rows:
        portable_relative = PurePosixPath(relative.replace("\\", "/"))
        if portable_relative.is_absolute() or ".." in portable_relative.parts:
            invalid_paths.append(relative)
            continue
        path = ROOT.joinpath(*portable_relative.parts)
        if not path.exists():
            missing.append(relative)
            continue
        actual_digest = sha256_file(path)
        actual_size = path.stat().st_size
        if actual_digest != expected_digest:
            digest_mismatch.append(
                {"artifact": relative, "expected": expected_digest, "actual": actual_digest}
            )
        elif actual_size != expected_size:
            # Size disagreeing while the digest matches means the manifest row
            # was hand-edited; report it rather than trusting the digest alone.
            size_mismatch.append(
                {"artifact": relative, "expected": expected_size, "actual": actual_size}
            )
        else:
            verified.append(relative)

    listed = {relative for relative, _, _ in rows}
    normalized_listed = [name.replace("\\", "/") for name, _, _ in rows]
    duplicate_rows = sorted(name for name, count in Counter(normalized_listed).items() if count > 1)
    artifact_set_errors: list[str] = []
    try:
        expected_paths = artifact_paths(provider)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        expected_paths = []
        artifact_set_errors.append(str(exc))
    on_disk = {str(path.relative_to(ROOT)).replace("\\", "/") for path in expected_paths}
    normalized_listed_set = {name.replace("\\", "/") for name in listed}
    unlisted = sorted(on_disk - normalized_listed_set)
    unexpected = sorted(normalized_listed_set - on_disk)

    return {
        "provider": provider,
        "manifest": str(manifest_path.relative_to(ROOT)),
        "rows": len(rows),
        "verified": len(verified),
        "missing_files": missing,
        "digest_mismatches": digest_mismatch,
        "size_mismatches": size_mismatch,
        "invalid_paths": invalid_paths,
        "duplicate_manifest_rows": duplicate_rows,
        "manifest_format_errors": manifest_format_errors,
        "artifacts_on_disk_not_in_manifest": unlisted,
        "manifest_artifacts_not_in_provider_set": unexpected,
        "artifact_set_errors": artifact_set_errors,
        "ok": not (
            missing
            or digest_mismatch
            or size_mismatch
            or invalid_paths
            or duplicate_rows
            or manifest_format_errors
            or unlisted
            or unexpected
            or artifact_set_errors
        ),
    }


def main(provider: str = "fixture") -> int:
    report = verify(provider)
    if "error" in report:
        print(f"[fail] {report['error']}", file=sys.stderr)
        return 2

    print(f"manifest: {report['manifest']}")
    print(f"rows: {report['rows']}  verified: {report['verified']}")
    for label, key in (
        ("missing file", "missing_files"),
        ("digest mismatch", "digest_mismatches"),
        ("size mismatch", "size_mismatches"),
        ("invalid manifest path", "invalid_paths"),
        ("duplicate manifest row", "duplicate_manifest_rows"),
        ("manifest format", "manifest_format_errors"),
        ("on disk but unlisted", "artifacts_on_disk_not_in_manifest"),
        ("listed outside provider set", "manifest_artifacts_not_in_provider_set"),
        ("artifact set", "artifact_set_errors"),
    ):
        for item in report[key]:
            print(f"  [{label}] {item}")
    print("OK" if report["ok"] else "MISMATCHES FOUND")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "fixture"))
