"""Evaluation corpus assembly: 20 base documents plus at most one attack artifact.

The base corpus is loaded once. Each attack scenario runs against the base corpus
with exactly one hostile artifact injected, so a result can only be attributed to
the attack under test.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from resolveflow.domain.evidence import Corpus, CorpusSnapshot
from resolveflow.domain.hashing import checksum
from resolveflow.ingestion.fixtures import ROOT, load_hero_corpus, validate_corpus

BASE_MANIFEST = ROOT / "data" / "corpus" / "hero-corpus-2.0.json"
ATTACK_MANIFEST = ROOT / "data" / "security" / "attack-corpus-1.0.json"
FAMILIES_PATH = ROOT / "data" / "security" / "attack-families-1.0.yaml"


class AttackVariant:
    __slots__ = ("family_id", "variant_id", "artifact_id", "source_path", "mechanism", "controls")

    def __init__(
        self,
        family_id: str,
        variant_id: str,
        artifact_id: str,
        source_path: str,
        mechanism: str,
        controls: tuple[str, ...],
    ) -> None:
        self.family_id = family_id
        self.variant_id = variant_id
        self.artifact_id = artifact_id
        self.source_path = source_path
        self.mechanism = mechanism
        self.controls = controls

    @property
    def attack_id(self) -> str:
        return f"{self.family_id}:{self.variant_id}"


def load_attack_variants(path: Path = FAMILIES_PATH) -> tuple[AttackVariant, ...]:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    variants: list[AttackVariant] = []
    for family in raw["families"]:
        for variant in family["variants"]:
            variants.append(
                AttackVariant(
                    family_id=family["family_id"],
                    variant_id=variant["variant_id"],
                    artifact_id=variant["artifact_id"],
                    source_path=variant["source_path"],
                    mechanism=" ".join(variant["mechanism"].split()),
                    controls=tuple(family["intended_controls"]),
                )
            )
    if len({item.attack_id for item in variants}) != len(variants):
        raise ValueError("attack family catalog contains duplicate family/variant IDs")
    if len({item.artifact_id for item in variants}) != len(variants):
        raise ValueError("attack variants must each reference a distinct artifact")
    return tuple(variants)


def attack_texts(path: Path = FAMILIES_PATH) -> dict[str, str]:
    """Raw attack document text, keyed by artifact ID, for pre-embedding."""
    return {
        variant.artifact_id: (ROOT / variant.source_path).read_text(encoding="utf-8")
        for variant in load_attack_variants(path)
    }


def _snapshot_for(corpus_parts: Corpus, base: CorpusSnapshot, suffix: str) -> CorpusSnapshot:
    as_of = base.as_of
    current = tuple(
        sorted(
            version.artifact_version_id
            for version in corpus_parts.versions
            if version.effective_from <= as_of
            and (version.effective_to is None or as_of < version.effective_to)
        )
    )
    current_chunk_ids = {
        chunk.chunk_id for chunk in corpus_parts.chunks if chunk.artifact_version_id in current
    }
    body = {
        "snapshot_id": f"{base.snapshot_id}-{suffix}",
        "tenant_id": base.tenant_id,
        "as_of": as_of,
        "artifact_version_ids": current,
        "embedding_ids": tuple(
            sorted(
                item.embedding_id
                for item in corpus_parts.embeddings
                if item.chunk_id in current_chunk_ids
            )
        ),
        "parser_versions": base.parser_versions,
        "chunker_versions": base.chunker_versions,
        "embedding_policy": base.embedding_policy,
        "created_at": base.created_at,
    }
    return CorpusSnapshot(**body, checksum=checksum(body))


def build_eval_corpus(
    *,
    embedder: Any,
    attack_artifact_id: str | None = None,
    base_manifest: Path = BASE_MANIFEST,
    attack_manifest: Path = ATTACK_MANIFEST,
) -> Corpus:
    """Base corpus, optionally with exactly one attack artifact injected."""
    base = load_hero_corpus(base_manifest, embedder=embedder)
    if attack_artifact_id is None:
        return base

    known = {
        item["artifact_id"]
        for item in json.loads(attack_manifest.read_text(encoding="utf-8"))["artifacts"]
    }
    if attack_artifact_id not in known:
        raise ValueError(f"unknown attack artifact: {attack_artifact_id}")

    attacks = load_hero_corpus(attack_manifest, embedder=embedder)
    keep = {attack_artifact_id}
    version_ids = {
        version.artifact_version_id for version in attacks.versions if version.artifact_id in keep
    }
    chunk_ids = {
        chunk.chunk_id for chunk in attacks.chunks if chunk.artifact_version_id in version_ids
    }
    merged = Corpus(
        artifacts=base.artifacts
        + tuple(item for item in attacks.artifacts if item.artifact_id in keep),
        versions=base.versions
        + tuple(item for item in attacks.versions if item.artifact_id in keep),
        chunks=base.chunks + tuple(item for item in attacks.chunks if item.chunk_id in chunk_ids),
        acls=base.acls + tuple(item for item in attacks.acls if item.chunk_id in chunk_ids),
        embeddings=base.embeddings
        + tuple(item for item in attacks.embeddings if item.chunk_id in chunk_ids),
        snapshot=base.snapshot,
    )
    merged = merged.model_copy(
        update={"snapshot": _snapshot_for(merged, base.snapshot, attack_artifact_id)}
    )
    validate_corpus(merged)
    return merged
