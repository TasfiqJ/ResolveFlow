from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from resolveflow.actions.postgres import JobLease, PostgreSQLJobRepository

JobHandler = Callable[[JobLease], Awaitable[None]]


@dataclass
class DurableWorker:
    """One transactional claim per tick; an expired lease is safely reclaimable."""

    repository: PostgreSQLJobRepository
    worker_id: str
    handler: JobHandler
    lease_seconds: int = 30
    retry_seconds: int = 5

    async def run_once(self, *, now: datetime) -> bool:
        lease = await self.repository.claim(
            worker_id=self.worker_id,
            now=now,
            lease_seconds=self.lease_seconds,
            kind="action_dispatch",
        )
        if lease is None:
            return False
        if not await self.repository.mark_running(lease, now=now):
            return False
        try:
            await self.handler(lease)
        except Exception:
            await self.repository.retry(
                lease,
                available_at=now + timedelta(seconds=self.retry_seconds),
                safe_error_code="action_worker_handler_failed",
            )
            return True
        await self.repository.complete(lease, now=now)
        return True
