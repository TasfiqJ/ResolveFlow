from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus


def test_reingestion_checksums_are_idempotent() -> None:
    first = load_hero_corpus()
    second = load_hero_corpus()
    assert first == second
    assert [item.checksum for item in first.chunks] == [item.checksum for item in second.chunks]
    assert len({item.chunk_id for item in first.chunks}) == len(first.chunks)


def test_manifest_freezes_current_versions_and_embedding_ids() -> None:
    corpus = load_hero_corpus()
    assert "artifact_runbook_payments_v2" not in corpus.snapshot.artifact_version_ids
    assert "artifact_runbook_payments_v3" in corpus.snapshot.artifact_version_ids
    assert corpus.snapshot.embedding_ids
    assert corpus.snapshot.parser_versions == ("resolveflow_fixture:1.0.0",)
