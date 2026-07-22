from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from resolveflow.actions.connectors import SyntheticJiraConnector
from resolveflow.actions.dispatcher import ActionDispatcher
from resolveflow.actions.models import ApprovalCommand
from resolveflow.actions.postgres import PostgreSQLActionRepository, PostgreSQLJobRepository
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.action_helpers import fixture_proposal

DATABASE_URL = "postgresql+asyncpg://resolveflow:resolveflow@localhost:5432/resolveflow"


@pytest.mark.asyncio
async def test_skip_locked_concurrent_claim_and_safe_reclaim_after_crash() -> None:
    engine = create_async_engine(DATABASE_URL)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = PostgreSQLJobRepository(sessions)
    suffix = uuid4().hex
    kind = f"test_{suffix}"
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    await repository.enqueue(
        job_id=f"job_concurrency_{suffix}",
        kind=kind,
        payload={"proposal_id": f"proposal_{suffix}"},
        logical_key=f"logical_{suffix}",
        available_at=now,
    )
    first, second = await asyncio.gather(
        repository.claim(worker_id="worker_one", now=now, lease_seconds=30, kind=kind),
        repository.claim(worker_id="worker_two", now=now, lease_seconds=30, kind=kind),
    )
    leases = [
        lease for lease in (first, second) if lease and lease.job_id == f"job_concurrency_{suffix}"
    ]
    assert len(leases) == 1
    lease = leases[0]
    reclaimed = await repository.claim(
        worker_id="worker_recovery",
        now=now + timedelta(seconds=31),
        lease_seconds=30,
        kind=kind,
    )
    assert reclaimed is not None
    assert reclaimed.job_id == lease.job_id
    assert reclaimed.lease_owner == "worker_recovery"
    assert reclaimed.attempt_count == 2
    assert not await repository.complete(lease, now=now + timedelta(seconds=32))
    assert await repository.complete(reclaimed, now=now + timedelta(seconds=32))
    await engine.dispose()


@pytest.mark.asyncio
async def test_approval_state_audit_job_and_idempotency_commit_together() -> None:
    engine = create_async_engine(DATABASE_URL)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = PostgreSQLActionRepository(sessions)
    original = fixture_proposal()
    suffix = uuid4().hex
    now = datetime(2026, 7, 21, 0, 1, tzinfo=timezone.utc)
    proposal = original.model_copy(
        update={
            "proposal_id": f"proposal_pg_{suffix}",
            "logical_action_id": f"action_pg_{suffix}",
            "run_id": f"run_pg_{suffix}",
            "tenant_id": f"tenant_pg_{suffix}",
            "idempotency_key": "sha256:" + suffix.ljust(64, "0")[:64],
        }
    )
    async with sessions() as session, session.begin():
        await session.execute(
            text("INSERT INTO tenants (tenant_id, display_name) VALUES (:id, 'Action test')"),
            {"id": proposal.tenant_id},
        )
        await session.execute(
            text(
                """INSERT INTO cases (case_id, tenant_id, source_system, raw_text, checksum)
                   VALUES (:case, :tenant, 'test', 'synthetic', :checksum)"""
            ),
            {
                "case": f"case_pg_{suffix}",
                "tenant": proposal.tenant_id,
                "checksum": "sha256:" + ("c" + suffix).ljust(64, "0")[:64],
            },
        )
        await session.execute(
            text(
                """INSERT INTO agent_runs (run_id, case_id, status, build_id)
                   VALUES (:run, :case, 'completed', 'test')"""
            ),
            {"run": proposal.run_id, "case": f"case_pg_{suffix}"},
        )
    await repository.insert_proposal(proposal)
    command = ApprovalCommand(
        proposal_id=proposal.proposal_id,
        payload_digest=proposal.payload_digest,
        actor_id="human_pg_approver",
        permissions=frozenset({"approve_jira"}),
    )
    first, second = await asyncio.gather(
        repository.approve(command, now=now),
        repository.approve(command, now=now),
    )
    assert sum(decision.accepted for decision in (first, second)) == 1
    accepted = next(decision for decision in (first, second) if decision.accepted)
    assert accepted.approval is not None
    dispatch = ActionDispatcher(SyntheticJiraConnector()).dispatch(
        proposal=accepted.proposal,
        approval=accepted.approval,
        worker_id="worker_pg_action",
        attempt_number=1,
        now=now,
    )
    await repository.record_dispatch_result(dispatch, now=now)
    async with sessions() as session:
        state = await session.scalar(
            text("SELECT state FROM action_proposals WHERE proposal_id = :id"),
            {"id": proposal.proposal_id},
        )
        approval_count = await session.scalar(
            text("SELECT count(*) FROM approvals WHERE proposal_id = :id"),
            {"id": proposal.proposal_id},
        )
        job_count = await session.scalar(
            text("SELECT count(*) FROM jobs WHERE logical_key = :key"),
            {"key": f"dispatch:{proposal.logical_action_id}"},
        )
        ledger_count = await session.scalar(
            text("SELECT count(*) FROM action_idempotency WHERE logical_action_id = :id"),
            {"id": proposal.logical_action_id},
        )
        attempt_count = await session.scalar(
            text("SELECT count(*) FROM action_attempts WHERE proposal_id = :id"),
            {"id": proposal.proposal_id},
        )
        audit_names = (
            (
                await session.execute(
                    text(
                        "SELECT event_name FROM audit_events WHERE run_id = :run ORDER BY sequence"
                    ),
                    {"run": proposal.run_id},
                )
            )
            .scalars()
            .all()
        )
    assert state == "complete"
    assert approval_count == job_count == ledger_count == attempt_count == 1
    assert audit_names == [
        "proposal.created",
        "approval.granted",
        "approval.denied",
        "connector.attempt.completed",
    ]
    await engine.dispose()


@pytest.mark.asyncio
async def test_audit_rows_are_database_append_only() -> None:
    engine = create_async_engine(DATABASE_URL)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        event_id = await session.scalar(text("SELECT event_id FROM audit_events LIMIT 1"))
        assert event_id is not None
        await session.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            async with session.begin():
                await session.execute(
                    text("UPDATE audit_events SET outcome = 'changed' WHERE event_id = :id"),
                    {"id": event_id},
                )
        await session.rollback()
    await engine.dispose()
