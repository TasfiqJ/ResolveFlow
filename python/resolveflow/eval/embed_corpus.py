"""One-time Embed v4 pass over the evaluation corpus and scenario queries.

Run this once. It batches every text into as few provider calls as the API
allows, writes the vectors to disk, and prints exactly what it spent. The A/B
runner then reads the cache in strict mode and cannot spend an embed call at all.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from resolveflow.eval.budget import BudgetedCohereClient
from resolveflow.eval.corpus import ATTACK_MANIFEST, BASE_MANIFEST
from resolveflow.eval.embedding_cache import CACHE_DIR, CachedEmbeddingAdapter
from resolveflow.eval.scenarios import scenario_queries
from resolveflow.ingestion.fixtures import corpus_profile, load_hero_corpus
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter

CACHE_PATH = CACHE_DIR / "embed-v4.0-eval-corpus.json"
MANIFEST_PATH = CACHE_DIR / "embed-v4.0-eval-corpus.manifest.json"


def chunk_texts() -> tuple[str, ...]:
    """Exact chunk content the retriever will embed, base corpus plus all attacks.

    The fixture embedder is used only to satisfy the loader's signature; the text
    it returns is what matters, and it costs nothing.
    """
    texts: list[str] = []
    for manifest in (BASE_MANIFEST, ATTACK_MANIFEST):
        corpus = load_hero_corpus(manifest, embedder=FixtureEmbeddingAdapter())
        texts.extend(chunk.content for chunk in corpus.chunks)
    return tuple(dict.fromkeys(texts))


def main() -> int:
    api_key = os.environ.get("RESOLVEFLOW_COHERE_API_KEY")
    if not api_key:
        print("RESOLVEFLOW_COHERE_API_KEY is not set; refusing to run", file=sys.stderr)
        return 2

    import cohere

    client = BudgetedCohereClient(cohere.ClientV2(api_key=api_key))
    adapter = CachedEmbeddingAdapter(CACHE_PATH, client=client, allow_provider=True)

    documents = chunk_texts()
    queries = scenario_queries()
    print(f"documents to embed: {len(documents)}   queries to embed: {len(queries)}")
    print(f"already cached: {adapter.cached_vector_count()}")

    calls = adapter.prewarm(documents=documents, queries=queries)
    if adapter.dirty:
        path = adapter.save()
        print(f"wrote {adapter.cached_vector_count()} vectors -> {path}")
    else:
        print("cache already complete; no provider call made")

    ledger = client.ledger()
    manifest = {
        "schema_version": "1.0",
        "model": adapter.model,
        "dimension": adapter.dimension,
        "vector_count": adapter.cached_vector_count(),
        "cache_hash": adapter.cache_hash(),
        "provider_embed_calls": calls,
        "budget_total_calls": ledger.total_calls,
        "input_tokens": ledger.input_tokens,
        "output_tokens": ledger.output_tokens,
        "base_corpus": corpus_profile(BASE_MANIFEST),
        "attack_corpus": corpus_profile(ATTACK_MANIFEST),
    }
    Path(MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(MANIFEST_PATH).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    print(client.summary_line())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
