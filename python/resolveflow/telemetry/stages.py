from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Literal

from pydantic import Field

from resolveflow.domain.base import FrozenModel

# Canonical stage names. Every stage a run can spend time in appears here so a
# missing stage in a snapshot is legible as "not reached", never as "zero cost".
STAGE_INTAKE = "intake"
STAGE_CONTEXT = "context_enrichment"
STAGE_ACL = "acl_application"
STAGE_LEXICAL = "lexical_retrieval"
STAGE_QUERY_EMBEDDING = "query_embedding"
STAGE_VECTOR = "vector_retrieval"
STAGE_FUSION = "fusion"
STAGE_RERANK = "rerank"
STAGE_HOSTILE_SCAN = "hostile_evidence_scan"
STAGE_EVIDENCE_PASS = "model_evidence_pass"
STAGE_TOOLS = "tool_execution"
STAGE_VERIFICATION = "verification"
STAGE_RENDERING = "rendering"
STAGE_ACTION = "action_proposal"

STAGE_ORDER: tuple[str, ...] = (
    STAGE_INTAKE,
    STAGE_CONTEXT,
    STAGE_ACL,
    STAGE_LEXICAL,
    STAGE_QUERY_EMBEDDING,
    STAGE_VECTOR,
    STAGE_FUSION,
    STAGE_RERANK,
    STAGE_HOSTILE_SCAN,
    STAGE_EVIDENCE_PASS,
    STAGE_TOOLS,
    STAGE_VERIFICATION,
    STAGE_RENDERING,
    STAGE_ACTION,
)


class StageTiming(FrozenModel):
    """One measured stage. Durations are wall time on a monotonic clock."""

    stage: str
    duration_ms: float = Field(ge=0.0)
    started_offset_ms: float = Field(ge=0.0)
    invocations: int = Field(default=1, ge=1)


class RunTiming(FrozenModel):
    """Measured timing for one run.

    ``wall_clock_ms`` and ``provider_call_ms`` are deliberately separate numbers.
    Wall clock is everything the orchestrator did. Provider-call time is only the
    time spent inside Cohere HTTP calls, as reported by the provider traces. They
    support different claims and must never be presented as interchangeable.
    """

    schema_version: Literal["1.0"] = "1.0"
    clock: Literal["time.monotonic"] = "time.monotonic"
    unit: Literal["milliseconds"] = "milliseconds"
    measured: bool
    wall_clock_ms: float = Field(ge=0.0)
    provider_call_ms: float = Field(ge=0.0)
    provider_call_count: int = Field(ge=0)
    stages: tuple[StageTiming, ...]

    @property
    def local_compute_ms(self) -> float:
        """Wall time not attributable to a provider HTTP call."""
        return max(0.0, self.wall_clock_ms - self.provider_call_ms)

    def by_stage(self) -> dict[str, float]:
        return {item.stage: item.duration_ms for item in self.stages}


class StageRecorder:
    """Monotonic-clock stage recorder.

    Repeated entries for the same stage accumulate rather than overwrite, so a
    stage entered once per tool round reports total time and an invocation count.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._origin = clock()
        self._durations: dict[str, float] = {}
        self._offsets: dict[str, float] = {}
        self._invocations: dict[str, int] = {}

    def _now_ms(self) -> float:
        return (self._clock() - self._origin) * 1000.0

    def record(self, stage: str, duration_ms: float, started_offset_ms: float) -> None:
        duration_ms = max(0.0, duration_ms)
        started_offset_ms = max(0.0, started_offset_ms)
        if stage in self._durations:
            self._durations[stage] += duration_ms
            self._invocations[stage] += 1
            self._offsets[stage] = min(self._offsets[stage], started_offset_ms)
        else:
            self._durations[stage] = duration_ms
            self._offsets[stage] = started_offset_ms
            self._invocations[stage] = 1

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        started = self._clock()
        offset = (started - self._origin) * 1000.0
        try:
            yield
        finally:
            self.record(name, (self._clock() - started) * 1000.0, offset)

    def elapsed_ms(self) -> float:
        return self._now_ms()

    def snapshot(
        self,
        *,
        provider_call_ms: float,
        provider_call_count: int,
        measured: bool = True,
    ) -> RunTiming:
        known = [name for name in STAGE_ORDER if name in self._durations]
        extra = sorted(name for name in self._durations if name not in set(STAGE_ORDER))
        stages = tuple(
            StageTiming(
                stage=name,
                duration_ms=round(self._durations[name], 3),
                started_offset_ms=round(self._offsets[name], 3),
                invocations=self._invocations[name],
            )
            for name in known + extra
        )
        return RunTiming(
            measured=measured,
            wall_clock_ms=round(self._now_ms(), 3),
            provider_call_ms=round(max(0.0, provider_call_ms), 3),
            provider_call_count=max(0, provider_call_count),
            stages=stages,
        )


class NullStageRecorder(StageRecorder):
    """Recorder that measures nothing; used where a caller opts out explicitly."""

    def record(self, stage: str, duration_ms: float, started_offset_ms: float) -> None:
        del stage, duration_ms, started_offset_ms
