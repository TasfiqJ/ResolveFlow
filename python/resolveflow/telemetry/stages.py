from __future__ import annotations

import platform
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


def clock_resolution_ns() -> int:
    """Advertised resolution of the stage clock, in nanoseconds.

    Reported alongside every run so a reader can tell a genuine sub-millisecond
    stage from a stage the clock was too coarse to see. On Windows
    ``time.monotonic`` advertises ~15.6 ms, which is why the previous run
    reported 0.0 ms for eleven stages.
    """
    return int(time.get_clock_info("perf_counter").resolution * 1_000_000_000)


class StageTiming(FrozenModel):
    """One measured stage. Durations are wall time on a high-resolution clock."""

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

    schema_version: Literal["1.1"] = "1.1"
    # 1.0 snapshots recorded "time.monotonic", whose ~15.6 ms Windows granularity
    # rendered every sub-millisecond stage as 0.0 ms -- unmeasured, not free. The
    # clock is named in the artifact so no reader has to guess which it was.
    clock: Literal["time.monotonic", "time.perf_counter_ns"] = "time.perf_counter_ns"
    clock_resolution_ns: int = Field(default_factory=clock_resolution_ns, ge=0)
    platform: str = Field(default_factory=lambda: f"{platform.system()} {platform.release()}")
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
    """High-resolution stage recorder.

    Repeated entries for the same stage accumulate rather than overwrite, so a
    stage entered once per tool round reports total time and an invocation count.

    The clock is ``time.perf_counter_ns`` and all arithmetic is done in integer
    nanoseconds, converted to milliseconds only at the boundary. ``time.monotonic``
    was previously used and on Windows advertises a ~15.6 ms tick, so every stage
    faster than one tick recorded as exactly 0.0 ms. 0.0 ms meant "the clock could
    not see this", not "this was free".
    """

    def __init__(self, clock: Callable[[], int] = time.perf_counter_ns) -> None:
        self._clock = clock
        self._origin = clock()
        self._durations_ns: dict[str, int] = {}
        self._offsets_ns: dict[str, int] = {}
        self._invocations: dict[str, int] = {}

    def _now_ms(self) -> float:
        return (self._clock() - self._origin) / 1_000_000.0

    def record(self, stage: str, duration_ms: float, started_offset_ms: float) -> None:
        """Record a stage from millisecond values (kept for external callers)."""
        self.record_ns(
            stage,
            int(max(0.0, duration_ms) * 1_000_000),
            int(max(0.0, started_offset_ms) * 1_000_000),
        )

    def record_ns(self, stage: str, duration_ns: int, started_offset_ns: int) -> None:
        duration_ns = max(0, duration_ns)
        started_offset_ns = max(0, started_offset_ns)
        if stage in self._durations_ns:
            self._durations_ns[stage] += duration_ns
            self._invocations[stage] += 1
            self._offsets_ns[stage] = min(self._offsets_ns[stage], started_offset_ns)
        else:
            self._durations_ns[stage] = duration_ns
            self._offsets_ns[stage] = started_offset_ns
            self._invocations[stage] = 1

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        started = self._clock()
        offset_ns = started - self._origin
        try:
            yield
        finally:
            self.record_ns(name, self._clock() - started, offset_ns)

    def elapsed_ms(self) -> float:
        return self._now_ms()

    def snapshot(
        self,
        *,
        provider_call_ms: float,
        provider_call_count: int,
        measured: bool = True,
    ) -> RunTiming:
        known = [name for name in STAGE_ORDER if name in self._durations_ns]
        extra = sorted(name for name in self._durations_ns if name not in set(STAGE_ORDER))
        # Six decimal places: nanosecond fidelity is preserved in a millisecond
        # field. Rounding to 3 would re-create the 0.0 ms problem for fast stages.
        stages = tuple(
            StageTiming(
                stage=name,
                duration_ms=round(self._durations_ns[name] / 1_000_000.0, 6),
                started_offset_ms=round(self._offsets_ns[name] / 1_000_000.0, 6),
                invocations=self._invocations[name],
            )
            for name in known + extra
        )
        return RunTiming(
            measured=measured,
            wall_clock_ms=round(self._now_ms(), 6),
            provider_call_ms=round(max(0.0, provider_call_ms), 6),
            provider_call_count=max(0, provider_call_count),
            stages=stages,
        )


class NullStageRecorder(StageRecorder):
    """Recorder that measures nothing; used where a caller opts out explicitly."""

    def record_ns(self, stage: str, duration_ns: int, started_offset_ns: int) -> None:
        del stage, duration_ns, started_offset_ns
