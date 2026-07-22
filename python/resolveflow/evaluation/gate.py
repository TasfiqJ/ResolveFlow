from __future__ import annotations

from resolveflow.domain.hashing import checksum
from resolveflow.evaluation.models import (
    GateOutcome,
    MetricObservation,
    ReleaseGateDefinition,
    ReleaseVerdict,
)


def _passes(value: float, direction: str, threshold: float) -> bool:
    return value <= threshold if direction == "at_most" else value >= threshold


def evaluate_release_gate(
    *,
    gate: ReleaseGateDefinition,
    metrics: tuple[MetricObservation, ...],
    candidate_build: str,
    baseline_build: str,
    dataset_id: str,
) -> ReleaseVerdict:
    by_id = {item.metric_id: item for item in metrics}
    hard: list[GateOutcome] = []
    quality: list[GateOutcome] = []
    reason_codes: list[str] = []
    limitations: list[str] = [
        "Candidate truths and scenarios are synthetic-agent-authored drafts pending human review.",
        "This is a deterministic development-fixture decision, not a held-out or "
        "live-provider release.",
    ]
    ordered_rules = tuple(rule for rule in gate.rules if rule.severity == "hard") + tuple(
        rule for rule in gate.rules if rule.severity != "hard"
    )
    for rule in ordered_rules:
        metric = by_id.get(rule.metric_id)
        if metric is None:
            raise ValueError(f"gate metric is missing from aggregation: {rule.metric_id}")
        phase = "hard_invariant" if rule.severity == "hard" else "quality_operations"
        if metric.denominator < rule.minimum_denominator:
            status = "insufficient_sample"
            reason = f"{rule.metric_id}_minimum_sample_not_met"
            limitations.append(
                f"{rule.metric_id} has N={metric.denominator}; gate requires "
                f"N={rule.minimum_denominator}."
            )
        elif _passes(metric.value, rule.direction, rule.threshold):
            status = "pass"
            reason = f"{rule.metric_id}_passed"
        else:
            status = "fail"
            reason = f"{rule.metric_id}_failed"
        outcome = GateOutcome(
            metric_id=rule.metric_id,
            phase=phase,
            status=status,
            reason_code=reason,
            numerator=metric.numerator,
            denominator=metric.denominator,
            value=metric.value,
            threshold=rule.threshold,
            failing_replay_links=metric.failing_replay_links,
        )
        (hard if rule.severity == "hard" else quality).append(outcome)
        if status != "pass":
            reason_codes.append(reason)

    hard_failure = any(item.status != "pass" for item in hard)
    required_failure = any(
        outcome.status != "pass"
        for outcome in quality
        for rule in gate.rules
        if rule.metric_id == outcome.metric_id and rule.severity == "required"
    )
    secondary_failure = any(
        outcome.status != "pass"
        for outcome in quality
        for rule in gate.rules
        if rule.metric_id == outcome.metric_id and rule.severity == "secondary"
    )
    if hard_failure or required_failure:
        verdict = "NO_SHIP"
    elif secondary_failure:
        verdict = "SHIP_WITH_LIMITS"
    else:
        verdict = "SHIP"
    failing_links = tuple(
        sorted(
            {
                link
                for outcome in (*hard, *quality)
                if outcome.status == "fail"
                for link in outcome.failing_replay_links
            }
        )
    )
    body = {
        "verdict_id": f"verdict_{candidate_build}_{dataset_id}",
        "decision_scope": "deterministic_development_fixture",
        "publishable_as_final_release": False,
        "candidate_build": candidate_build,
        "baseline_build": baseline_build,
        "dataset_id": dataset_id,
        "dataset_lock_status": "DRAFT_NOT_LOCKED",
        "gate_id": gate.gate_id,
        "evaluation_order": ("hard_invariants", "quality_operations"),
        "hard_outcomes": tuple(hard),
        "quality_outcomes": tuple(quality),
        "limitations": tuple(dict.fromkeys(limitations)),
        "verdict": verdict,
        "reason_codes": tuple(reason_codes),
        "failing_replay_links": failing_links,
    }
    return ReleaseVerdict(**body, checksum=checksum(body))
