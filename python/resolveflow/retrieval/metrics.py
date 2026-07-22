from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

from resolveflow.domain.evidence import RetrievalMetricObservation, stable_id
from resolveflow.domain.hashing import checksum
from resolveflow.ingestion.fixtures import ROOT, load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy, make_identity_snapshot
from resolveflow.retrieval.engine import HybridRetriever
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def recall_at_k(ranked_ids: tuple[str, ...], relevant_ids: frozenset[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    return len(set(ranked_ids[:k]) & relevant_ids) / len(relevant_ids)


def ndcg_at_k(ranked_ids: tuple[str, ...], relevant_ids: frozenset[str], k: int) -> float:
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, item in enumerate(ranked_ids[:k], 1)
        if item in relevant_ids
    )
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant_ids)) + 1))
    return dcg / ideal if ideal else 0.0


def evaluate_fixture_split(path: Path) -> tuple[RetrievalMetricObservation, ...]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    corpus = load_hero_corpus()
    retriever = HybridRetriever(
        corpus, AuthorizationPolicy(), FixtureEmbeddingAdapter(), FixtureRerankAdapter()
    )
    values: dict[str, list[float]] = {
        "recall_at_5": [],
        "recall_at_10": [],
        "ndcg_at_10": [],
    }
    for case in fixture["cases"]:
        identity = make_identity_snapshot(
            tenant_id=corpus.snapshot.tenant_id,
            actor_id=f"eval_{case['query_id']}",
            role=case["role"],
            region="ca-central",
            case_time=corpus.snapshot.as_of,
        )
        trace = retriever.retrieve(case["query"], identity)
        ranked = tuple(item.artifact_id for item in trace.candidates)
        relevant = frozenset(case["relevant_artifact_ids"])
        values["recall_at_5"].append(recall_at_k(ranked, relevant, 5))
        values["recall_at_10"].append(recall_at_k(ranked, relevant, 10))
        values["ndcg_at_10"].append(ndcg_at_k(ranked, relevant, 10))
    observations: list[RetrievalMetricObservation] = []
    for metric_name, samples in values.items():
        body = {
            "metric_name": metric_name,
            "split": fixture["split"],
            "build_id": "evidence-fixture-v1",
            "fixture_version": path.stem,
            "numerator": sum(samples),
            "denominator": len(samples),
            "value": sum(samples) / len(samples),
            "created_at": datetime.fromisoformat("2026-07-15T14:22:00+00:00"),
        }
        observations.append(
            RetrievalMetricObservation(
                **body, metric_id=stable_id("metric", body), checksum=checksum(body)
            )
        )
    return tuple(observations)


def fixture_metric_paths() -> tuple[Path, ...]:
    return (
        ROOT / "data/truths/retrieval-development-1.0.json",
        ROOT / "data/truths/retrieval-calibration-1.0.json",
    )
