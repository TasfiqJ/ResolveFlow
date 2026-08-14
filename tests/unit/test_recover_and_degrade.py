"""Recovery from snapshots, and graceful stop at a repetition boundary.

Together these guarantee that a live run which hits the call cap partway through
is never wasted: the harness stops on a whole repetition, and if it still dies
mid-trial the completed snapshots can be rebuilt into a valid summary offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from resolveflow.eval.ab_runner import ABHarness, run_ab
from resolveflow.eval.budget import BudgetExceeded
from resolveflow.eval.recover_ab import recover


def _write_three_trials(runs_dir: Path) -> None:
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=3)


def test_recovery_keeps_only_whole_repetitions(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    _write_three_trials(runs_dir)
    assert len(list(runs_dir.glob("run-*.json"))) == 96  # 3 x 16 x 2

    # Simulate a crash: delete one trial-3 snapshot so trial 3 is incomplete.
    victim = next(iter(sorted(runs_dir.glob("*_t3.json"))))
    victim.unlink()
    assert len(list(runs_dir.glob("run-*.json"))) == 95

    result = recover("fixture", runs_dir)
    assert result["repetitions"] == 2
    assert result["run_count"] == 64
    assert result["recovered_from_snapshots"]["complete_trials_used"] == [1, 2]
    assert result["recovered_from_snapshots"]["incomplete_trials_dropped"] == {3: 31}
    # The rebuilt summary carries the same interval machinery a live run would.
    assert "intervals" in result["by_build"]["guarded-v1"]


def test_recovery_refuses_when_no_trial_is_complete(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=1)
    # Break trial 1 so nothing is whole.
    next(iter(sorted(runs_dir.glob("run-*.json")))).unlink()
    with pytest.raises(SystemExit, match="no complete repetition"):
        recover("fixture", runs_dir)


class _CappingHarness:
    """Wraps the fixture harness and raises BudgetExceeded after N runs."""

    def __init__(self, cap_after: int) -> None:
        self._inner = ABHarness(provider="fixture")
        self._cap_after = cap_after
        self._n = 0
        # surfaced attributes build_result reads through the harness
        self.provider = self._inner.provider
        self.command_model = self._inner.command_model
        self.rerank_model = self._inner.rerank_model
        self.embedder = self._inner.embedder
        self.budgets = self._inner.budgets

    def run_one(self, scenario, build_id, generated_at, trial=1):  # type: ignore[no-untyped-def]
        self._n += 1
        if self._n > self._cap_after:
            raise BudgetExceeded(f"cap hit after {self._cap_after}")
        return self._inner.run_one(scenario, build_id, generated_at, trial)


def test_run_ab_stops_on_a_whole_repetition_when_the_cap_is_hit(tmp_path: Path) -> None:
    # 32 runs per trial. Cap after 40 -> trial 1 completes (32), trial 2 dies
    # mid-way (8 runs). The result must be trial 1 only, not 40 runs.
    harness = _CappingHarness(cap_after=40)
    result = run_ab(harness=harness, output_dir=tmp_path, repetitions=3)
    assert result["repetitions"] == 1
    assert result["run_count"] == 32
    # Every published trial is whole.
    assert {row["trial"] for row in result["runs"]} == {1}


def test_run_ab_reraises_if_not_even_one_repetition_fits() -> None:
    harness = _CappingHarness(cap_after=5)
    with pytest.raises(BudgetExceeded, match="single repetition"):
        run_ab(harness=harness, output_dir=None, repetitions=2)
