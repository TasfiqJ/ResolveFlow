from __future__ import annotations

from resolveflow.retrieval.metrics import evaluate_fixture_split, fixture_metric_paths


def test_fixture_metrics_have_exact_counts_and_synthetic_provenance() -> None:
    observations = tuple(
        observation
        for path in fixture_metric_paths()
        for observation in evaluate_fixture_split(path)
    )
    assert len(observations) == 6
    assert {item.denominator for item in observations} == {2, 3}
    assert all(0 <= item.value <= 1 for item in observations)
    assert all(item.checksum.startswith("sha256:") for item in observations)
