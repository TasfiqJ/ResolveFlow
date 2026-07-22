from __future__ import annotations

import pytest
from resolveflow.ingestion.fixtures import load_hero_corpus, validate_corpus


def test_every_chunk_has_version_position_acl_and_embedding() -> None:
    corpus = load_hero_corpus()
    validate_corpus(corpus)
    version_ids = {item.artifact_version_id for item in corpus.versions}
    for chunk in corpus.chunks:
        assert chunk.artifact_version_id in version_ids
        assert chunk.position.locator
        assert any(item.chunk_id == chunk.chunk_id for item in corpus.acls)
        assert any(item.chunk_id == chunk.chunk_id for item in corpus.embeddings)


def test_data_quality_rejects_missing_acl_and_duplicate_embedding_id() -> None:
    corpus = load_hero_corpus()
    broken = corpus.model_copy(
        update={
            "acls": (),
            "embeddings": corpus.embeddings + (corpus.embeddings[0],),
        }
    )
    with pytest.raises(ValueError) as error:
        validate_corpus(broken)
    assert "missing ACL" in str(error.value)
    assert "duplicate embedding IDs" in str(error.value)
