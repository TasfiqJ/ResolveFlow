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

from resolveflow.eval.budget import SDK_MAX_RETRIES, BudgetedCohereClient
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

    client = BudgetedCohereClient(
        cohere.ClientV2(api_key=api_key, max_retries=SDK_MAX_RETRIES, timeout=60)
    )
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

    # Provenance must survive a warm-cache re-run. When the cache is already
    # complete this invocation makes 0 calls, but the vectors on disk were still
    # produced by real Embed v4 calls in an earlier run. Writing budget_total_calls
    # = 0 here would erase that and make downstream provenance checks reject real
    # vectors. Carry forward the highest call count ever recorded for this cache
    # hash, so the manifest states how many real calls stand behind these vectors,
    # not merely how many the most recent invocation happened to make.
    prior_calls = 0
    prior_input = 0
    prior_output = 0
    manifest_path = Path(MANIFEST_PATH)
    if manifest_path.exists():
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
            if prior.get("cache_hash") == adapter.cache_hash():
                prior_calls = int(prior.get("budget_total_calls", 0) or 0)
                prior_input = int(prior.get("input_tokens", 0) or 0)
                prior_output = int(prior.get("output_tokens", 0) or 0)
        except (json.JSONDecodeError, ValueError):
            pass

    manifest = {
        "schema_version": "1.0",
        "model": adapter.model,
        "dimension": adapter.dimension,
        "vector_count": adapter.cached_vector_count(),
        "cache_hash": adapter.cache_hash(),
        "provider_embed_calls_this_run": calls,
        # Real calls behind the current cache contents, carried across warm re-runs.
        "budget_total_calls": max(ledger.total_calls, prior_calls),
        "input_tokens": max(ledger.input_tokens, prior_input),
        "output_tokens": max(ledger.output_tokens, prior_output),
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
