"""Recovery from snapshots, and graceful stop at a repetition boundary.

Together these guarantee that a live run which hits the call cap partway through
is never wasted: the harness stops on a whole repetition, and if it still dies
mid-trial the completed snapshots can be rebuilt into a valid summary offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.eval.ab_runner import ABHarness, run_ab
from resolveflow.eval.budget import BudgetExceeded
from resolveflow.eval.publish import RESULTS_DIR
from resolveflow.eval.recover_ab import recover


def _write_three_trials(runs_dir: Path) -> None:
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=3)


def _rehash(payload: dict[str, object]) -> dict[str, object]:
    snapshot = RunSnapshot.model_validate(payload)
    payload["content_hash"] = checksum(
        snapshot.model_dump(mode="python", exclude={"content_hash"} | RunSnapshot.UNHASHED_FIELDS)
    )
    return payload


def _rebind_run_id(payload: dict[str, object], run_id: str) -> dict[str, object]:
    """Keep nested hashes valid while constructing a wrong scenario/build cell."""

    payload["run_id"] = run_id
    graph = payload["evidence_graph"]
    assert isinstance(graph, dict)
    graph["run_id"] = run_id
    graph["graph_hash"] = checksum(
        {key: value for key, value in graph.items() if key != "graph_hash"}
    )
    response = payload["response"]
    assert isinstance(response, dict)
    response["graph_hash"] = graph["graph_hash"]
    trace = payload["trace"]
    assert isinstance(trace, list)
    previous_hash: str | None = None
    for event in trace:
        assert isinstance(event, dict)
        event["correlation_id"] = run_id
        event["previous_event_hash"] = previous_hash
        event["event_hash"] = checksum(
            {key: value for key, value in event.items() if key not in {"event_id", "event_hash"}}
        )
        previous_hash = str(event["event_hash"])
    return _rehash(payload)


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


def test_recovery_rejects_a_later_full_cardinality_trial_with_wrong_cells(
    tmp_path: Path,
) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    run_ab(harness=ABHarness(provider="fixture"), output_dir=runs_dir, repetitions=2)
    files = sorted(runs_dir.glob("*_t2.json"))
    source = json.loads(files[0].read_text(encoding="utf-8"))
    victim_path = next(
        path
        for path in files[1:]
        if json.loads(path.read_text(encoding="utf-8"))["build_id"] == source["build_id"]
    )
    victim = json.loads(victim_path.read_text(encoding="utf-8"))
    victim_path.write_text(
        json.dumps(_rebind_run_id(source, str(victim["run_id"]))), encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="trial 2.*invalid scenario/build cell set"):
        recover("fixture", runs_dir)


def test_recovery_rejects_complete_trials_that_do_not_start_at_one(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    _write_three_trials(runs_dir)
    for path in runs_dir.glob("run-*.json"):
        if "_t2.json" not in path.name and "_t3.json" not in path.name:
            path.unlink()

    with pytest.raises(SystemExit, match="contiguous from trial 1"):
        recover("fixture", runs_dir)


def test_recovery_requires_exact_unique_scenario_build_cells(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=1)
    files = sorted(runs_dir.glob("run-*.json"))
    source = json.loads(files[0].read_text(encoding="utf-8"))
    victim = json.loads(files[1].read_text(encoding="utf-8"))
    files[1].write_text(json.dumps(_rebind_run_id(source, str(victim["run_id"]))), encoding="utf-8")

    with pytest.raises(SystemExit, match="invalid scenario/build cell set"):
        recover("fixture", runs_dir)


def test_recovery_round_trips_fixture_result_core_exactly(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    original = run_ab(harness=ABHarness(provider="fixture"), output_dir=runs_dir, repetitions=1)

    recovered = recover("fixture", runs_dir)

    assert recovered["runs"] == original["runs"]
    assert recovered["embedding_model"] == original["embedding_model"]
    assert recovered["results_hash"] == original["results_hash"]


@pytest.mark.parametrize("field", ["generated_at", "model_policy"])
def test_recovery_rejects_mixed_execution_identity(tmp_path: Path, field: str) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=1)
    victim = sorted(runs_dir.glob("run-*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload[field] = "2026-07-16T00:00:00Z" if field == "generated_at" else "different-policy"
    victim.write_text(json.dumps(_rehash(payload)), encoding="utf-8")

    with pytest.raises(SystemExit, match=f"mixed execution cohort.*{field}"):
        recover("fixture", runs_dir)


def test_recovery_binds_current_truth_to_frozen_case(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=1)
    victim = sorted(runs_dir.glob("run-*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["case"]["raw_text"] = "mutated historical truth"
    victim.write_text(json.dumps(_rehash(payload)), encoding="utf-8")

    with pytest.raises(SystemExit, match="case differs.*frozen scenario"):
        recover("fixture", runs_dir)


def test_recovery_rejects_resealed_snapshot_with_broken_nested_evidence(
    tmp_path: Path,
) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    run_ab(harness=ABHarness(provider="fixture"), output_dir=runs_dir, repetitions=1)
    victim = sorted(runs_dir.glob("run-*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["trace"][0]["safe_detail"]["tampered"] = True
    victim.write_text(json.dumps(_rehash(payload)), encoding="utf-8")

    with pytest.raises(SystemExit, match="nested evidence.*audit event hash"):
        recover("fixture", runs_dir)


@pytest.mark.parametrize("field", ["rerank_model", "embedding_model"])
def test_recovery_rejects_mixed_historical_model_identity(tmp_path: Path, field: str) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    harness = ABHarness(provider="fixture")
    run_ab(harness=harness, output_dir=runs_dir, repetitions=1)
    victim = sorted(runs_dir.glob("run-*.json"))[0]
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["retrieval"][field] = "different-model"
    victim.write_text(json.dumps(_rehash(payload)), encoding="utf-8")

    with pytest.raises(SystemExit, match=f"snapshots differ on {field}"):
        recover("fixture", runs_dir)


def test_recovery_rejects_empty_historical_budget_instead_of_backfilling(
    tmp_path: Path,
) -> None:
    runs_dir = tmp_path / "runs" / "fixture"
    run_ab(harness=ABHarness(provider="fixture"), output_dir=runs_dir, repetitions=1)

    with pytest.raises(SystemExit, match="historical agent_budgets missing keys"):
        recover("fixture", runs_dir, agent_budgets={})


def test_live_recovery_preserves_historical_budget_schema_and_portable_paths() -> None:
    published = json.loads((RESULTS_DIR / "ab-summary-cohere.json").read_text(encoding="utf-8"))
    result = recover(
        "cohere",
        RESULTS_DIR / "runs" / "cohere",
        agent_budgets=published["agent_budgets"],
    )

    assert "max_tool_calls_per_response" not in result["agent_budgets"]
    assert "max_tool_calls_per_run" not in result["agent_budgets"]
    recovery = result["recovered_from_snapshots"]
    assert "\\" not in recovery["runs_dir"]
    assert "hit its call cap" not in recovery["note"]
    assert recovery["complete_trials_used"] == [1]
    assert recovery["excluded_snapshot_count"] == 63
    environment = result["environment"]
    assert environment["base_corpus"]["artifact_count"] == 20
    assert environment["base_corpus"]["classification_counts"]
    assert environment["base_corpus"]["tenant_counts"]
    assert environment["base_corpus"]["roles"]
    assert environment["base_corpus"]["corpus_hash"].startswith("sha256:")
    assert environment["attack_corpus"]["artifact_count"] == 8
    assert len(environment["attack_variants"]) == 8


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
    # mid-way (8 runs). The command must fail instead of publishing trial 1 as
    # though it were the requested three-trial study. Complete trial 1 remains
    # recoverable, while partial trial 2 is explicitly quarantined.
    harness = _CappingHarness(cap_after=40)
    with pytest.raises(BudgetExceeded, match="no partial aggregate was published"):
        run_ab(harness=harness, output_dir=tmp_path, repetitions=3)

    assert len(tuple(tmp_path.glob("run-*.json"))) == 32
    assert len(tuple(tmp_path.glob("incomplete-trials/*/trial-2/run-*.json"))) == 8


def test_run_ab_reraises_if_not_even_one_repetition_fits() -> None:
    harness = _CappingHarness(cap_after=5)
    with pytest.raises(BudgetExceeded, match="no partial aggregate was published"):
        run_ab(harness=harness, output_dir=None, repetitions=2)
