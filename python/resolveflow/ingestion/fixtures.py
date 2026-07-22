from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from resolveflow.domain.evidence import (
    Artifact,
    ArtifactVersion,
    Chunk,
    ChunkACL,
    Classification,
    Corpus,
    CorpusSnapshot,
    EmbeddingRecord,
    SourcePosition,
    stable_id,
)
from resolveflow.domain.hashing import checksum
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data/corpus/hero-corpus-1.0.json"


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _source_content(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"))
    lines = [line.strip() for line in text.splitlines()]
    return " ".join(line for line in lines if line and not line.startswith("---"))


def load_hero_corpus(manifest_path: Path = MANIFEST) -> Corpus:
    raw: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    as_of = _at(raw["as_of"])
    artifacts: list[Artifact] = []
    versions: list[ArtifactVersion] = []
    chunks: list[Chunk] = []
    acls: list[ChunkACL] = []
    embeddings: list[EmbeddingRecord] = []
    embedder = FixtureEmbeddingAdapter()

    for source in raw["artifacts"]:
        artifact_body = {
            "artifact_id": source["artifact_id"],
            "tenant_id": raw["tenant_id"],
            "source_system": "synthetic_fixture",
            "source_key": source["source_key"],
            "title": source["title"],
            "owner": source["owner"],
            "modality": source["modality"],
            "created_at": as_of,
        }
        artifacts.append(Artifact(**artifact_body, checksum=checksum(artifact_body)))
        for version_source in source["versions"]:
            source_path = ROOT / version_source["source_path"]
            source_bytes = source_path.read_bytes()
            source_hash = "sha256:" + __import__("hashlib").sha256(source_bytes).hexdigest()
            version_id = f"{source['artifact_id']}_v{version_source['version']}"
            version_body = {
                "artifact_version_id": version_id,
                "artifact_id": source["artifact_id"],
                "version": version_source["version"],
                "source_path": version_source["source_path"],
                "source_checksum": source_hash,
                "parser_name": raw["parser"]["name"],
                "parser_version": raw["parser"]["version"],
                "chunker_name": raw["chunker"]["name"],
                "chunker_version": raw["chunker"]["version"],
                "parsing_quality": "complete",
                "language": "en",
                "classification": Classification[version_source["classification"].upper()],
                "effective_from": _at(version_source["effective_from"]),
                "effective_to": (
                    _at(version_source["effective_to"])
                    if version_source["effective_to"] is not None
                    else None
                ),
                "created_at": as_of,
            }
            version = ArtifactVersion(**version_body, checksum=checksum(version_body))
            versions.append(version)
            content = _source_content(source_path)
            position = SourcePosition(**version_source["position"])
            chunk_id = stable_id(
                "chunk", {"version": version_id, "position": position, "ordinal": 0}
            )
            chunk_body = {
                "chunk_id": chunk_id,
                "artifact_version_id": version_id,
                "ordinal": 0,
                "position": position,
                "content": content,
                "token_count": len(content.split()),
            }
            chunk = Chunk(**chunk_body, checksum=checksum(chunk_body))
            chunks.append(chunk)
            for role in source["roles"]:
                acl_body = {
                    "chunk_id": chunk_id,
                    "tenant_id": raw["tenant_id"],
                    "role": role,
                    "region": "ca-central",
                    "policy_version": "synthetic-acl-1.0",
                }
                acls.append(
                    ChunkACL(
                        **acl_body, acl_id=stable_id("acl", acl_body), checksum=checksum(acl_body)
                    )
                )
            vector = embedder.embed_documents((content,))[0]
            embedding_body = {
                "chunk_id": chunk_id,
                "model": embedder.model,
                "dimension": len(vector),
                "input_type": "search_document",
                "preprocessing_version": "nfc-tokenize-1.0",
                "content_checksum": chunk.checksum,
                "vector": vector,
            }
            embeddings.append(
                EmbeddingRecord(
                    **embedding_body,
                    embedding_id=stable_id("embedding", embedding_body),
                    checksum=checksum(embedding_body),
                )
            )

    current_versions = tuple(
        sorted(
            version.artifact_version_id
            for version in versions
            if version.effective_from <= as_of
            and (version.effective_to is None or as_of < version.effective_to)
        )
    )
    current_chunk_ids = {
        chunk.chunk_id for chunk in chunks if chunk.artifact_version_id in current_versions
    }
    current_embedding_ids = tuple(
        sorted(item.embedding_id for item in embeddings if item.chunk_id in current_chunk_ids)
    )
    snapshot_body = {
        "snapshot_id": raw["snapshot_id"],
        "tenant_id": raw["tenant_id"],
        "as_of": as_of,
        "artifact_version_ids": current_versions,
        "embedding_ids": current_embedding_ids,
        "parser_versions": (f"{raw['parser']['name']}:{raw['parser']['version']}",),
        "chunker_versions": (f"{raw['chunker']['name']}:{raw['chunker']['version']}",),
        "embedding_policy": raw["embedding_policy"],
        "created_at": as_of,
    }
    snapshot = CorpusSnapshot(**snapshot_body, checksum=checksum(snapshot_body))
    corpus = Corpus(
        artifacts=tuple(artifacts),
        versions=tuple(versions),
        chunks=tuple(chunks),
        acls=tuple(acls),
        embeddings=tuple(embeddings),
        snapshot=snapshot,
    )
    validate_corpus(corpus)
    return corpus


def validate_corpus(corpus: Corpus) -> None:
    errors: list[str] = []
    version_ids = {item.artifact_version_id for item in corpus.versions}
    chunk_ids = {item.chunk_id for item in corpus.chunks}
    identifier_groups = {
        "artifact": [item.artifact_id for item in corpus.artifacts],
        "artifact version": [item.artifact_version_id for item in corpus.versions],
        "chunk": [item.chunk_id for item in corpus.chunks],
        "ACL": [item.acl_id for item in corpus.acls],
        "embedding": [item.embedding_id for item in corpus.embeddings],
    }
    for label, identifiers in identifier_groups.items():
        if len(set(identifiers)) != len(identifiers):
            errors.append(f"duplicate {label} IDs")
    for chunk in corpus.chunks:
        if chunk.artifact_version_id not in version_ids:
            errors.append(f"orphaned chunk: {chunk.chunk_id}")
        if not chunk.content.strip():
            errors.append(f"empty chunk: {chunk.chunk_id}")
        if not any(acl.chunk_id == chunk.chunk_id for acl in corpus.acls):
            errors.append(f"missing ACL: {chunk.chunk_id}")
    for embedding in corpus.embeddings:
        if embedding.chunk_id not in chunk_ids:
            errors.append(f"orphaned embedding: {embedding.embedding_id}")
    if errors:
        raise ValueError("; ".join(errors))
