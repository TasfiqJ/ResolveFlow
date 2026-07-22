from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from resolveflow.public.live import LiveRequest, PublicLiveLimiter, PublicLiveRejected

NOW = datetime(2026, 7, 22, tzinfo=timezone.utc)


def request(session: str = "session-001", ip: str = "ip-001") -> LiveRequest:
    return LiveRequest(session, ip, "hero-payments-001", "baseline")


def test_kill_switch_and_predefined_inputs() -> None:
    with pytest.raises(PublicLiveRejected, match="kill_switch"):
        PublicLiveLimiter(enabled=False).submit(request(), NOW)
    limiter = PublicLiveLimiter(enabled=True)
    with pytest.raises(PublicLiveRejected, match="input_not_allowed"):
        limiter.submit(LiveRequest("session-001", "ip-001", "arbitrary", "baseline"), NOW)


def test_one_run_concurrency_queue_and_quota() -> None:
    limiter = PublicLiveLimiter(enabled=True, daily_global_limit=2, queue_limit=2)
    ticket = limiter.submit(request(), NOW)
    assert ticket.position == 1
    with pytest.raises(PublicLiveRejected, match="session_concurrency"):
        limiter.submit(request(), NOW)
    limiter.submit(request("session-002", "ip-002"), NOW)
    with pytest.raises(PublicLiveRejected, match="global_quota"):
        limiter.submit(request("session-003", "ip-003"), NOW)


def test_completion_releases_concurrency_but_preserves_daily_count() -> None:
    limiter = PublicLiveLimiter(enabled=True, session_daily_limit=2)
    ticket = limiter.submit(request(), NOW)
    limiter.complete("session-001", ticket.ticket_id)
    second = limiter.submit(request(), NOW)
    assert second.position == 1
    assert second.deadline_at > NOW


def test_deadline_expires_stuck_run_and_releases_session() -> None:
    limiter = PublicLiveLimiter(enabled=True, deadline_seconds=5, session_daily_limit=2)
    ticket = limiter.submit(request(), NOW)
    assert limiter.expire(NOW + timedelta(seconds=4)) == ()
    assert limiter.expire(NOW + timedelta(seconds=5)) == (ticket.ticket_id,)
    replacement = limiter.submit(request(), NOW + timedelta(seconds=6))
    assert replacement.ticket_id != ticket.ticket_id
