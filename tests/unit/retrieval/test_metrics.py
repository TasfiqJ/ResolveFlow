from __future__ import annotations

from resolveflow.retrieval.metrics import ndcg_at_k, recall_at_k


def test_retrieval_metrics_use_declared_relevance_ids() -> None:
    ranked = ("decisive", "noise", "support")
    relevant = frozenset({"decisive", "support"})
    assert recall_at_k(ranked, relevant, 1) == 0.5
    assert recall_at_k(ranked, relevant, 3) == 1.0
    assert 0.9 < ndcg_at_k(ranked, relevant, 3) < 1.0
