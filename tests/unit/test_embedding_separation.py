"""Guard the Embed v4 separation finding and its provenance checks.

The claim this protects is a Cohere-specific one: real Embed v4 vectors separate
hostile from benign evidence and recover attacks the signature layer missed. The
tests pin the shape of the result and, critically, the guards that stop the
module computing that number off anything other than real Embed v4 output.
"""

from __future__ import annotations

import math

from resolveflow.eval.embedding_separation import _auc, _bootstrap_auc_ci, evaluate


def test_auc_is_monotone_and_bounded() -> None:
    assert _auc([1.0, 2.0], [0.0, 0.5]) == 1.0
    assert _auc([0.0], [1.0]) == 0.0
    assert _auc([1.0, 0.0], [1.0, 0.0]) == 0.5


def test_bootstrap_interval_is_seeded_and_brackets_the_point() -> None:
    positive = [0.3, 0.5, 0.9, 0.1, 0.7]
    negative = [0.0, 0.2, 0.4, -0.1]
    first = _bootstrap_auc_ci(positive, negative)
    second = _bootstrap_auc_ci(positive, negative)
    assert first == second, "bootstrap must be seeded and reproducible"
    point = _auc(positive, negative)
    assert first["low"] <= point <= first["high"]


def test_report_has_the_cohere_provenance_and_the_headline_fields() -> None:
    report = evaluate()
    assert report["provider"] == "cohere"
    assert report["embedding_model"] == "embed-v4.0"
    # The number must be free: no calls spent computing it.
    assert report["provider_calls_spent_here"] == 0
    # ...but backed by real ones behind the cache.
    assert report["cache"]["embed_calls_behind_cache"] >= 1
    assert report["n_attack"] == 8
    assert 0.0 <= report["auc"] <= 1.0
    assert not math.isnan(report["auc"])


def test_zero_false_positive_operating_point_is_honest() -> None:
    report = evaluate()
    op = report["zero_false_positive_operating_point"]
    assert op["false_positives_on_benign"] == 0
    assert 0.0 <= op["embed_v4_recall"]["point"] <= 1.0


def test_the_recovered_count_is_a_subset_of_regex_misses() -> None:
    report = evaluate()
    vs = report["vs_regex_detector"]
    assert vs["embed_recovered_from_regex_misses"] <= vs["regex_missed"]
    # union caught is at least as large as either layer alone
    assert vs["union_caught"] >= sum(1 for r in report["per_attack"] if r["regex_fired"])


def test_attacks_evading_both_are_reported_not_hidden() -> None:
    """A clean sweep would be suspicious; the honest finding names what got through."""
    report = evaluate()
    evaded = report["vs_regex_detector"]["attacks_evading_both"]
    for artifact in evaded:
        row = next(r for r in report["per_attack"] if r["artifact"] == artifact)
        assert not row["regex_fired"] and not row["embed_v4_flag"]
