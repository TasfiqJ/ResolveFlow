from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock

ALLOWED_CASES = frozenset({"hero-payments-001"})
ALLOWED_MUTATIONS = frozenset(
    {"baseline", "role_downgrade", "malicious_runbook", "missing_decisive_evidence", "jira_outage"}
)


class PublicLiveRejected(ValueError):
    pass


@dataclass(frozen=True)
class LiveRequest:
    session_id: str
    ip_hash: str
    case_id: str
    mutation: str


@dataclass(frozen=True)
class LiveTicket:
    ticket_id: str
    position: int
    deadline_at: datetime


@dataclass
class PublicLiveLimiter:
    enabled: bool = False
    daily_global_limit: int = 12
    session_daily_limit: int = 2
    ip_daily_limit: int = 4
    queue_limit: int = 4
    deadline_seconds: int = 45
    _day: str = ""
    _global_count: int = 0
    _session_counts: dict[str, int] = field(default_factory=dict)
    _ip_counts: dict[str, int] = field(default_factory=dict)
    _active_sessions: set[str] = field(default_factory=set)
    _queue: list[str] = field(default_factory=list)
    _tickets: dict[str, tuple[str, datetime]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def submit(self, request: LiveRequest, now: datetime | None = None) -> LiveTicket:
        if request.case_id not in ALLOWED_CASES or request.mutation not in ALLOWED_MUTATIONS:
            raise PublicLiveRejected("public_live_input_not_allowed")
        if not self.enabled:
            raise PublicLiveRejected("public_live_kill_switch_active")
        current = now or datetime.now(timezone.utc)
        with self._lock:
            self._roll_day(current)
            self._expire_locked(current)
            if request.session_id in self._active_sessions:
                raise PublicLiveRejected("public_live_session_concurrency")
            if self._global_count >= self.daily_global_limit:
                raise PublicLiveRejected("public_live_global_quota")
            if self._session_counts.get(request.session_id, 0) >= self.session_daily_limit:
                raise PublicLiveRejected("public_live_session_quota")
            if self._ip_counts.get(request.ip_hash, 0) >= self.ip_daily_limit:
                raise PublicLiveRejected("public_live_ip_quota")
            if len(self._queue) >= self.queue_limit:
                raise PublicLiveRejected("public_live_queue_full")
            ticket_id = f"live-{current.strftime('%Y%m%d')}-{self._global_count + 1:04d}"
            self._queue.append(ticket_id)
            self._active_sessions.add(request.session_id)
            deadline = current + timedelta(seconds=self.deadline_seconds)
            self._tickets[ticket_id] = (request.session_id, deadline)
            self._global_count += 1
            self._session_counts[request.session_id] = (
                self._session_counts.get(request.session_id, 0) + 1
            )
            self._ip_counts[request.ip_hash] = self._ip_counts.get(request.ip_hash, 0) + 1
            return LiveTicket(ticket_id, len(self._queue), deadline)

    def complete(self, session_id: str, ticket_id: str) -> None:
        with self._lock:
            self._active_sessions.discard(session_id)
            if ticket_id in self._queue:
                self._queue.remove(ticket_id)
            self._tickets.pop(ticket_id, None)

    def expire(self, now: datetime | None = None) -> tuple[str, ...]:
        with self._lock:
            return self._expire_locked(now or datetime.now(timezone.utc))

    def _expire_locked(self, now: datetime) -> tuple[str, ...]:
        expired = tuple(
            ticket_id for ticket_id, (_, deadline) in self._tickets.items() if deadline <= now
        )
        for ticket_id in expired:
            session_id, _ = self._tickets.pop(ticket_id)
            self._active_sessions.discard(session_id)
            if ticket_id in self._queue:
                self._queue.remove(ticket_id)
        return expired

    def _roll_day(self, now: datetime) -> None:
        day = now.date().isoformat()
        if self._day != day:
            self._day = day
            self._global_count = 0
            self._session_counts.clear()
            self._ip_counts.clear()
            self._active_sessions.clear()
            self._queue.clear()
            self._tickets.clear()
