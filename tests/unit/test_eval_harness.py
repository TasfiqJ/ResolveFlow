from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from resolveflow.eval.ab_runner import ABHarness
from resolveflow.eval.budget import BudgetedCohereClient, BudgetExceeded
from resolveflow.eval.corpus import (
    ATTACK_MANIFEST,
    BASE_MANIFEST,
    build_eval_corpus,
    load_attack_variants,
)
from resolveflow.eval.embedding_cache import CachedEmbeddingAdapter, EmbeddingCacheMiss
from resolveflow.eval.scenarios import all_scenarios
from resolveflow.ingestion.fixtures import ROOT, corpus_profile
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter
from resolveflow.telemetry.stages import StageRecorder

# --------------------------------------------------------------------------
# Budget accounting
# --------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self) -> None:
        self.id = "resp_1"
        self.usage = {"tokens": {"input_tokens": 11, "output_tokens": 7}}


class _RateLimited(Exception):
    status_code = 429


class _FakeClient:
    def __init__(self, fail_times: int = 0) -> None:
        self.calls = 0
        self._fail_times = fail_times

    def chat(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise _RateLimited("429 rate limit")
        return _FakeResponse()

    def embed(self, **_: object) -> _FakeResponse:
        self.calls += 1
        return _FakeResponse()

    def rerank(self, **_: object) -> _FakeResponse:
        self.calls += 1
        return _FakeResponse()


def _clock() -> object:
    state = {"t": 0.0}

    def now() -> float:
        state["t"] += 0.001
        return state["t"]

    return now


def test_budget_counts_every_call_and_tokens() -> None:
    client = BudgetedCohereClient(_FakeClient(), sleep=lambda _: None, clock=_clock())
    for _ in range(3):
        client.chat(model="m", messages=[])
    ledger = client.ledger()
    assert ledger.total_calls == 3
    assert ledger.calls_by_endpoint == {"chat": 3}
    assert ledger.input_tokens == 33
    assert ledger.output_tokens == 21
    assert ledger.retry_calls == 0


def test_budget_raises_before_exceeding_the_cap() -> None:
    client = BudgetedCohereClient(_FakeClient(), max_calls=2, sleep=lambda _: None, clock=_clock())
    client.chat(model="m", messages=[])
    client.chat(model="m", messages=[])
    with pytest.raises(BudgetExceeded):
        client.chat(model="m", messages=[])
    # The refused call must not be recorded as consumed.
    assert client.total_calls == 2


def test_rate_limit_retries_are_counted_against_the_budget() -> None:
    inner = _FakeClient(fail_times=2)
    client = BudgetedCohereClient(inner, sleep=lambda _: None, clock=_clock())
    client.chat(model="m", messages=[])
    ledger = client.ledger()
    # Two 429s plus the success: three calls against the trial key, not one.
    assert ledger.total_calls == 3
    assert ledger.retry_calls == 2
    assert [item.status for item in ledger.records] == ["rate_limited", "rate_limited", "ok"]


def test_throttle_sleeps_rather_than_exceeding_the_per_minute_limit() -> None:
    # A sleep that actually advances the clock, as time.sleep does. The window
    # must then drain and the call must proceed.
    state = {"t": 0.0}
    slept: list[float] = []

    def clock() -> float:
        state["t"] += 0.001
        return state["t"]

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        state["t"] += seconds

    client = BudgetedCohereClient(
        _FakeClient(),
        rate_limits={"embed": 2},  # type: ignore[arg-type]
        sleep=sleep,
        clock=clock,
    )
    for _ in range(3):
        client.embed(model="embed-v4.0", texts=[])
    assert slept, "third embed call inside the window must have waited"
    assert client.total_calls == 3
    assert client.ledger().throttle_sleep_ms > 0


def test_throttle_refuses_to_spin_when_the_clock_does_not_advance() -> None:
    # A no-op sleep would otherwise loop forever, hanging a run instead of
    # failing it. Bounded waits turn that into a loud error.
    client = BudgetedCohereClient(
        _FakeClient(),
        rate_limits={"embed": 1},  # type: ignore[arg-type]
        sleep=lambda _: None,
        clock=_clock(),
    )
    client.embed(model="embed-v4.0", texts=[])
    with pytest.raises(RuntimeError, match="clock is not advancing"):
        client.embed(model="embed-v4.0", texts=[])


def test_call_records_carry_no_request_or_response_body() -> None:
    client = BudgetedCohereClient(_FakeClient(), sleep=lambda _: None, clock=_clock())
    client.chat(model="m", messages=[{"role": "user", "content": "secret text"}])
    dumped = json.dumps(client.ledger().model_dump(mode="json"))
    assert "secret text" not in dumped
    record = client.ledger().records[0]
    assert record.request_hash.startswith("sha256:")
    assert record.response_hash is not None


# --------------------------------------------------------------------------
# Embedding cache
# --------------------------------------------------------------------------


def test_strict_cache_refuses_to_spend_a_provider_call(tmp_path: Path) -> None:
    adapter = CachedEmbeddingAdapter(tmp_path / "cache.json", client=None, allow_provider=False)
    with pytest.raises(EmbeddingCacheMiss):
        adapter.embed_query("anything")


def test_cache_roundtrip_normalizes_and_reloads(tmp_path: Path) -> None:
    class _Embed:
        def embed(self, **kwargs: object) -> object:
            texts = kwargs["texts"]
            assert isinstance(texts, list)

            class _Vectors:
                float = [[3.0, 4.0] for _ in texts]

            class _Response:
                embeddings = _Vectors()
                usage = None

            return _Response()

    path = tmp_path / "cache.json"
    adapter = CachedEmbeddingAdapter(path, client=_Embed(), dimension=2, allow_provider=True)
    calls = adapter.prewarm(documents=("a", "b"), queries=("q",))
    assert calls == 2  # one document batch, one query batch
    vector = adapter.embed_documents(("a",))[0]
    assert vector == pytest.approx((0.6, 0.8))  # unit-normalized
    adapter.save()

    reloaded = CachedEmbeddingAdapter(path, client=None, allow_provider=False)
    assert reloaded.cached_vector_count() == 3
    assert reloaded.embed_query("q") == pytest.approx((0.6, 0.8))


# --------------------------------------------------------------------------
# Corpus and attack catalog
# --------------------------------------------------------------------------


def test_base_corpus_shape_is_what_the_results_claim() -> None:
    profile = corpus_profile(BASE_MANIFEST)
    assert profile["artifact_count"] == 20
    assert profile["restricted_artifact_count"] == 6
    assert set(profile["tenant_counts"]) == {
        "tenant_heliopay_synthetic",
        "tenant_northwind_synthetic",
    }
    assert len(profile["roles"]) >= 4
    assert profile["corpus_hash"].startswith("sha256:")


def test_corpus_hash_tracks_document_text_not_just_the_manifest(tmp_path: Path) -> None:
    before = corpus_profile(BASE_MANIFEST)["corpus_hash"]
    target = ROOT / "data" / "artifacts" / "oncall-rotation.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\nappended line\n")
        after = corpus_profile(BASE_MANIFEST)["corpus_hash"]
    finally:
        target.write_bytes(original)
    assert before != after


def test_attack_families_are_four_by_two_and_textually_distinct() -> None:
    variants = load_attack_variants()
    assert len(variants) == 8
    assert len({item.family_id for item in variants}) == 4
    for family in {item.family_id for item in variants}:
        assert sum(1 for item in variants if item.family_id == family) == 2
    bodies = [(ROOT / item.source_path).read_text(encoding="utf-8") for item in variants]
    assert len(set(bodies)) == 8, "every attack variant must be a distinct payload"
    assert len({item.mechanism for item in variants}) == 8


def test_exactly_one_attack_artifact_is_injected() -> None:
    embedder = FixtureEmbeddingAdapter()
    base = build_eval_corpus(embedder=embedder)
    injected = build_eval_corpus(embedder=embedder, attack_artifact_id="attack_b2_exfil_locator")
    assert len(injected.artifacts) == len(base.artifacts) + 1
    attack_ids = [
        item.artifact_id for item in injected.artifacts if item.artifact_id.startswith("attack_")
    ]
    assert attack_ids == ["attack_b2_exfil_locator"]


def test_unknown_attack_artifact_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_eval_corpus(embedder=FixtureEmbeddingAdapter(), attack_artifact_id="attack_nope")


def test_attack_corpus_declares_eight_artifacts() -> None:
    assert corpus_profile(ATTACK_MANIFEST)["artifact_count"] == 8


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------


def test_scenario_set_is_eight_benign_and_eight_attack() -> None:
    scenarios = all_scenarios()
    assert len(scenarios) == 16
    assert sum(1 for item in scenarios if item.kind == "benign") == 8
    attacks = [item for item in scenarios if item.kind == "attack"]
    assert len(attacks) == 8
    assert len({item.attack_artifact_id for item in attacks}) == 8


def test_non_clearance_roles_forbid_restricted_material() -> None:
    for scenario in all_scenarios():
        if scenario.role != "incident_commander":
            assert "artifact_restricted_legal" in scenario.forbidden_artifact_ids
        # No HelioPay identity may ever surface Northwind material.
        assert "artifact_northwind_pricing" in scenario.forbidden_artifact_ids


# --------------------------------------------------------------------------
# Stage timing
# --------------------------------------------------------------------------


def test_recorder_accumulates_repeated_stages() -> None:
    # Nanosecond readings: 10 ms then 20 ms, accumulating to 30 ms.
    recorder = StageRecorder(
        clock=iter([0, 0, 10_000_000, 10_000_000, 30_000_000, 30_000_000]).__next__
    )
    with recorder.stage("tool_execution"):
        pass
    with recorder.stage("tool_execution"):
        pass
    timing = recorder.snapshot(provider_call_ms=0.0, provider_call_count=0)
    stage = timing.by_stage()["tool_execution"]
    assert stage == pytest.approx(30.0)
    assert timing.stages[0].invocations == 2


def test_wall_time_and_provider_time_stay_separate() -> None:
    recorder = StageRecorder()
    with recorder.stage("rerank"):
        pass
    timing = recorder.snapshot(provider_call_ms=250.0, provider_call_count=2)
    assert timing.provider_call_ms == 250.0
    assert timing.provider_call_count == 2
    # Local compute never absorbs provider time, and never goes negative.
    assert timing.local_compute_ms >= 0.0


# --------------------------------------------------------------------------
# The core A/B claim, guarded as a regression
# --------------------------------------------------------------------------


def test_guarded_build_blocks_what_the_unsafe_baseline_admits() -> None:
    from resolveflow.eval.ab_runner import run_ab

    scenarios = tuple(
        item
        for item in all_scenarios()
        if item.scenario_id
        in {"benign-02-database-failover", "attack-c1-role_escalation_cross_tenant"}
    )
    assert len(scenarios) == 2
    result = run_ab(harness=ABHarness(provider="fixture"), scenarios=scenarios)

    guarded = result["by_build"]["guarded-v1"]
    unsafe = result["by_build"]["unsafe-v0"]

    # The whole point of pre-retrieval authorization: unauthorized chunks never
    # reach the candidate set at all under guarded-v1.
    assert guarded["forbidden_evidence_retrieved_count"] == 0
    assert unsafe["forbidden_evidence_retrieved_count"] > 0
    assert guarded["forbidden_evidence_exposure_count"] == 0

    # Neither build may ever perform an external write.
    assert guarded["external_write_total"] == 0
    assert unsafe["external_write_total"] == 0


def test_fixture_run_records_provider_call_stages_and_tokens() -> None:
    scenario = all_scenarios()[0]
    _, metrics = ABHarness(provider="fixture").run_one(
        scenario,
        "guarded-v1",
        datetime.now(timezone.utc),
    )
    row = metrics.as_dict()

    assert row["provider_calls_consumed"] == 3
    assert row["tool_rounds_used"] == 1
    assert row["calls_to_render"] == 3
    assert [call["stage"] for call in row["provider_call_profile"]] == [
        "evidence_pass",
        "tool_round_1",
        "render",
    ]
    assert [call["total_tokens"] for call in row["provider_call_profile"]] == [
        104,
        340,
        184,
    ]


def test_every_attack_scenario_records_whether_it_was_delivered() -> None:
    from resolveflow.eval.ab_runner import ABHarness, run_ab

    scenarios = tuple(item for item in all_scenarios() if item.kind == "attack")
    result = run_ab(harness=ABHarness(provider="fixture"), scenarios=scenarios)
    for row in result["runs"]:
        # None would mean the harness silently lost track of delivery, which
        # would make every "got through: none" result unfalsifiable.
        assert row["attack_delivered"] is not None


class _GatewayTimeout(Exception):
    status_code = 504


class _GatewayThenOk:
    """Fails with a 504 the first `fail_times` calls, then succeeds."""

    def __init__(self, fail_times: int) -> None:
        self.calls = 0
        self._fail_times = fail_times

    def rerank(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise _GatewayTimeout("504 gateway timeout")
        return _FakeResponse()


def test_transient_gateway_504_is_retried_and_counted() -> None:
    """A 504 on Cohere's side must not abort the run; it retries, counted.

    This is the exact failure that killed a live run after 33 good calls: a
    single Rerank v4 504 propagated because only 429s were retried.
    """
    from resolveflow.eval.budget import _is_transient_gateway

    inner = _GatewayThenOk(fail_times=2)
    client = BudgetedCohereClient(inner, sleep=lambda _: None, clock=_clock())
    client.rerank(model="rerank-v4.0-fast", query="q", documents=["a"])
    ledger = client.ledger()
    assert ledger.total_calls == 3
    assert ledger.retry_calls == 2
    assert [item.status for item in ledger.records] == [
        "gateway_error",
        "gateway_error",
        "ok",
    ]
    assert _is_transient_gateway(_GatewayTimeout("504"))


def test_persistent_gateway_error_still_eventually_raises() -> None:
    """Retries are bounded; a provider that never recovers must not loop forever."""
    inner = _GatewayThenOk(fail_times=99)
    client = BudgetedCohereClient(inner, max_attempts=3, sleep=lambda _: None, clock=_clock())
    with pytest.raises(_GatewayTimeout):
        client.rerank(model="rerank-v4.0-fast", query="q", documents=["a"])
    # Exactly max_attempts calls were made and all are on the ledger.
    assert client.total_calls == 3
    assert all(item.status == "gateway_error" for item in client.ledger().records)
