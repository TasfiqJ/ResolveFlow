from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel


class WilsonInterval(FrozenModel):
    confidence: float = 0.95
    lower: float = Field(ge=0.0, le=1.0)
    upper: float = Field(ge=0.0, le=1.0)


class MetricObservation(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    metric_id: str
    metric_version: str
    family: Literal["hard_invariant", "quality", "operations"]
    build_id: str
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    value: float = Field(ge=0.0, le=1.0)
    interval: WilsonInterval
    unit: Literal["proportion"] = "proportion"
    base_truth_clusters: tuple[str, ...]
    source_run_ids: tuple[str, ...]
    failing_replay_links: tuple[str, ...] = ()
    checksum: str

    @model_validator(mode="after")
    def exact_ratio(self) -> MetricObservation:
        if abs(self.value - (self.numerator / self.denominator)) > 1e-12:
            raise ValueError("metric value must equal the exact numerator/denominator")
        return self


class PairedBootstrapInterval(FrozenModel):
    confidence: float = 0.95
    estimate: float
    lower: float
    upper: float
    cluster_count: int = Field(gt=0)
    resamples: int = Field(gt=0)
    seed: int
    caveat: str


class ExperimentComparison(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    comparison_id: str
    baseline_build: str
    candidate_build: str
    paired_scenario_ids: tuple[str, ...]
    metric_id: str
    baseline_value: float
    candidate_value: float
    delta: float
    uncertainty: PairedBootstrapInterval
    checksum: str


class GateMetricRule(FrozenModel):
    metric_id: str
    direction: Literal["at_most", "at_least"]
    threshold: float
    minimum_denominator: int = Field(gt=0)
    severity: Literal["hard", "required", "secondary"]


class ReleaseGateDefinition(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    gate_id: str
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"]
    registration_status: Literal["DRAFT_PRE_REGISTERED_NO_HELD_OUT_RESULTS"]
    declared_at: str
    declared_commit: str
    rules: tuple[GateMetricRule, ...]
    checksum: str


class GateOutcome(FrozenModel):
    metric_id: str
    phase: Literal["hard_invariant", "quality_operations"]
    status: Literal["pass", "fail", "insufficient_sample"]
    reason_code: str
    numerator: int
    denominator: int
    value: float
    threshold: float
    failing_replay_links: tuple[str, ...] = ()


class ReleaseVerdict(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    verdict_id: str
    decision_scope: Literal["deterministic_development_fixture"]
    publishable_as_final_release: Literal[False] = False
    candidate_build: str
    baseline_build: str
    dataset_id: str
    dataset_lock_status: Literal["DRAFT_NOT_LOCKED"] = "DRAFT_NOT_LOCKED"
    gate_id: str
    evaluation_order: tuple[Literal["hard_invariants", "quality_operations"], ...]
    hard_outcomes: tuple[GateOutcome, ...]
    quality_outcomes: tuple[GateOutcome, ...]
    limitations: tuple[str, ...]
    verdict: Literal["SHIP", "SHIP_WITH_LIMITS", "NO_SHIP"]
    reason_codes: tuple[str, ...]
    failing_replay_links: tuple[str, ...]
    checksum: str


class BuildEvaluation(FrozenModel):
    build_id: str
    metrics: tuple[MetricObservation, ...]
    verdict: ReleaseVerdict


class ResultBundle(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    bundle_id: str
    provenance: Literal["deterministic_recorded_fixture"] = "deterministic_recorded_fixture"
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"]
    dataset_id: str
    dataset_lock_status: Literal["DRAFT_NOT_LOCKED"] = "DRAFT_NOT_LOCKED"
    manifest_id: str
    manifest_checksum: str
    materialization_checksum: str
    commit: str
    baseline: BuildEvaluation
    candidate: BuildEvaluation
    comparison: ExperimentComparison
    paired_run_checksum: str
    checksum: str
