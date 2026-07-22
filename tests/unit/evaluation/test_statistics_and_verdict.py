from resolveflow.domain.hashing import checksum
from resolveflow.evaluation.gate import evaluate_release_gate
from resolveflow.evaluation.io import load_gate
from resolveflow.evaluation.models import MetricObservation
from resolveflow.evaluation.statistics import paired_cluster_bootstrap, wilson_interval


def test_wilson_interval_uses_exact_counts() -> None:
    interval = wilson_interval(0, 200)
    assert interval.lower == 0.0
    assert 0.018 < interval.upper < 0.019


def test_cluster_bootstrap_is_seeded_and_cluster_aware() -> None:
    values = {"truth-a": (0.0, 1.0), "truth-b": (1.0, 1.0)}
    first = paired_cluster_bootstrap(values, resamples=500, seed=19)
    second = paired_cluster_bootstrap(values, resamples=500, seed=19)
    assert first == second
    assert first.cluster_count == 2
    assert first.estimate == 0.5


def _with_metric(
    metrics: tuple[MetricObservation, ...], metric_id: str, numerator: int, denominator: int
) -> tuple[MetricObservation, ...]:
    changed = []
    for item in metrics:
        if item.metric_id != metric_id:
            changed.append(item)
            continue
        body = item.model_dump(mode="python", exclude={"checksum"})
        body.update(
            {
                "numerator": numerator,
                "denominator": denominator,
                "value": numerator / denominator,
                "interval": wilson_interval(numerator, denominator),
            }
        )
        changed.append(item.__class__(**body, checksum=checksum(body)))
    return tuple(changed)


def test_ship_ship_with_limits_and_no_ship_logic(candidate_bundle) -> None:  # type: ignore[no-untyped-def]
    gate = load_gate()
    base = candidate_bundle.candidate.metrics
    limited = evaluate_release_gate(
        gate=gate,
        metrics=base,
        candidate_build="guarded-v1",
        baseline_build="unsafe-v0",
        dataset_id="draft",
    )
    assert limited.verdict == "SHIP_WITH_LIMITS"

    enough_citations = _with_metric(base, "citation_precision", 10, 10)
    shipped = evaluate_release_gate(
        gate=gate,
        metrics=enough_citations,
        candidate_build="guarded-v1",
        baseline_build="unsafe-v0",
        dataset_id="draft",
    )
    assert shipped.verdict == "SHIP"

    forbidden = _with_metric(enough_citations, "forbidden_candidate", 1, 1)
    blocked = evaluate_release_gate(
        gate=gate,
        metrics=forbidden,
        candidate_build="guarded-v1",
        baseline_build="unsafe-v0",
        dataset_id="draft",
    )
    assert blocked.verdict == "NO_SHIP"
