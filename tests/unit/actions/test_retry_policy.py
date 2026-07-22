from __future__ import annotations

from resolveflow.actions.dispatcher import bounded_backoff
from resolveflow.actions.models import RetryPolicy


def test_backoff_is_deterministic_bounded_and_grows() -> None:
    policy = RetryPolicy(base_seconds=5, maximum_seconds=40, jitter_percent=0)
    observed = [bounded_backoff(policy, attempt, "sha256:key") for attempt in range(1, 7)]
    assert observed == [5, 10, 20, 40, 40, 40]

    jittered = RetryPolicy(base_seconds=10, maximum_seconds=30, jitter_percent=20)
    first = bounded_backoff(jittered, 2, "sha256:stable")
    assert first == bounded_backoff(jittered, 2, "sha256:stable")
    assert 16 <= first <= 24
