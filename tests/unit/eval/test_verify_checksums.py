from __future__ import annotations

from pathlib import Path

import pytest
from resolveflow.eval.verify_checksums import parse_manifest


def test_checksum_manifest_parser_requires_the_canonical_header_and_only_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "SHA256SUMS-test.md"
    path.write_text(
        "# Artifact checksums (test provider)\n\n"
        "| Artifact | SHA-256 | Bytes |\n"
        "| --- | --- | --- |\n"
        f"| `artifact.json` | `{'a' * 64}` | 12 |\n",
        encoding="utf-8",
    )

    assert parse_manifest(path) == [("artifact.json", "a" * 64, 12)]

    path.write_text(path.read_text(encoding="utf-8") + "unverified prose\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 6 is invalid"):
        parse_manifest(path)


def test_checksum_manifest_parser_rejects_a_mislabeled_provider(tmp_path: Path) -> None:
    path = tmp_path / "SHA256SUMS-cohere.md"
    path.write_text(
        "# Artifact checksums (fixture provider)\n\n"
        "| Artifact | SHA-256 | Bytes |\n"
        "| --- | --- | --- |\n"
        f"| `artifact.json` | `{'b' * 64}` | 12 |\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="header is invalid"):
        parse_manifest(path)
