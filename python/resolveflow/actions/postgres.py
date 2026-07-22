from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from resolveflow.actions.models import (
    ActionDecision,
    ActionPayload,
    ActionProposal,
    ActionState,
    ApprovalCommand,
    DispatchResult,
)
from resolveflow.actions.service import ActionService
from resolveflow.domain.base import FrozenModel
from resolveflow.telemetry.audit import make_audit_record


class JobLease(FrozenModel):
    job_id: str
    kind: str
    status: Literal["leased"] = "leased"
    payload: dict[str, Any]
    attempt_count: int = Field(ge=1)
    max_attempts: int = Field(ge=1)
    lease_owner: str
    lease_expires_at: datetime
    run_id: str | None = None


class PostgreSQLJobRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def enqueue(
        self,
        *,
        job_id: str,
        kind: str,
        payload: dict[str, Any],
        logical_key: str,
        available_at: datetime,
        run_id: str | None = None,
        max_attempts: int = 5,
    ) -> None:
        async with self.sessions() as session, session.begin():
            await session.execute(
                text(
                    """INSERT INTO jobs
                    (job_id, kind, status, payload, run_id, logical_key, available_at,
                     attempt_count, max_attempts, cancellation_requested, updated_at)
                    VALUES (:job_id, :kind, 'queued', CAST(:payload AS json), :run_id,
                            :logical_key, :available_at, 0, :max_attempts, false, :available_at)
                    ON CONFLICT (logical_key) DO NOTHING"""
                ),
                {
                    "job_id": job_id,
                    "kind": kind,
                    "payload": _json(payload),
                    "run_id": run_id,
                    "logical_key": logical_key,
                    "available_at": available_at,
                    "max_attempts": max_attempts,
                },
            )

    async def claim(
        self,
        *,
        worker_id: str,
        now: datetime,
        lease_seconds: int,
        kind: str | None = None,
    ) -> JobLease | None:
        if not worker_id.startswith("worker_"):
            raise PermissionError("job_claim_requires_worker_identity")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        lease_expires = now + timedelta(seconds=lease_seconds)
        async with self.sessions() as session, session.begin():
            result = await session.execute(
                text(
                    """WITH candidate AS (
                      SELECT job_id FROM jobs
                      WHERE cancellation_requested = false
                        AND (CAST(:kind AS text) IS NULL OR kind = CAST(:kind AS text))
                        AND attempt_count < max_attempts
                        AND (
                          (status IN ('queued', 'retry_wait') AND available_at <= :now)
                          OR (status IN ('leased', 'running') AND lease_expires_at <= :now)
                        )
                      ORDER BY available_at, created_at, job_id
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    UPDATE jobs AS job
                    SET status = 'leased', lease_owner = :worker_id,
                        lease_expires_at = :lease_expires,
                        attempt_count = job.attempt_count + 1, updated_at = :now
                    FROM candidate
                    WHERE job.job_id = candidate.job_id
                    RETURNING job.job_id, job.kind, job.payload, job.attempt_count,
                              job.max_attempts, job.lease_owner, job.lease_expires_at,
                              job.run_id"""
                ),
                {
                    "now": now,
                    "worker_id": worker_id,
                    "lease_expires": lease_expires,
                    "kind": kind,
                },
            )
            row = result.mappings().one_or_none()
            return JobLease(**row) if row else None

    async def mark_running(self, lease: JobLease, *, now: datetime) -> bool:
        return await self._owned_transition(lease, "running", now=now)

    async def retry(self, lease: JobLease, *, available_at: datetime, safe_error_code: str) -> bool:
        async with self.sessions() as session, session.begin():
            result = await session.execute(
                text(
                    """UPDATE jobs SET status = CASE
                           WHEN attempt_count >= max_attempts THEN 'dead_letter'
                           ELSE 'retry_wait' END,
                         available_at = :available_at, lease_owner = NULL,
                         lease_expires_at = NULL, last_error_code = :error,
                         updated_at = :available_at
                       WHERE job_id = :job_id AND lease_owner = :owner
                         AND status IN ('leased', 'running')"""
                ),
                {
                    "job_id": lease.job_id,
                    "owner": lease.lease_owner,
                    "available_at": available_at,
                    "error": safe_error_code,
                },
            )
            return _affected(result)

    async def complete(self, lease: JobLease, *, now: datetime) -> bool:
        return await self._owned_transition(lease, "complete", now=now, terminal=True)

    async def cancel(self, job_id: str, *, now: datetime) -> bool:
        async with self.sessions() as session, session.begin():
            result = await session.execute(
                text(
                    """UPDATE jobs SET status = 'cancelled', cancellation_requested = true,
                         lease_owner = NULL, lease_expires_at = NULL, completed_at = :now,
                         updated_at = :now
                       WHERE job_id = :job_id AND status IN ('queued', 'retry_wait')"""
                ),
                {"job_id": job_id, "now": now},
            )
            return _affected(result)

    async def _owned_transition(
        self, lease: JobLease, state: str, *, now: datetime, terminal: bool = False
    ) -> bool:
        async with self.sessions() as session, session.begin():
            result = await session.execute(
                text(
                    """UPDATE jobs SET status = :state, updated_at = :now,
                         completed_at = CASE WHEN :terminal THEN :now ELSE completed_at END,
                         lease_owner = CASE WHEN :terminal THEN NULL ELSE lease_owner END,
                         lease_expires_at = CASE WHEN :terminal THEN NULL ELSE lease_expires_at END
                       WHERE job_id = :job_id AND lease_owner = :owner
                         AND status IN ('leased', 'running')"""
                ),
                {
                    "state": state,
                    "now": now,
                    "terminal": terminal,
                    "job_id": lease.job_id,
                    "owner": lease.lease_owner,
                },
            )
            return _affected(result)


class PostgreSQLActionRepository:
    """Critical action transitions and their audit rows share one transaction."""

    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], service: ActionService | None = None
    ) -> None:
        self.sessions = sessions
        self.service = service or ActionService()

    async def insert_proposal(self, proposal: ActionProposal) -> None:
        async with self.sessions() as session, session.begin():
            await session.execute(
                text(
                    """INSERT INTO action_proposals
                    (proposal_id, logical_action_id, run_id, tenant_id, graph_hash,
                     supporting_claim_ids, payload, payload_digest, idempotency_key,
                     state, revision, expires_at, invalidated_by_proposal_id,
                     created_at, updated_at)
                    VALUES (:proposal_id, :logical_action_id, :run_id, :tenant_id, :graph_hash,
                            CAST(:supporting AS json), CAST(:payload AS json), :digest, :key,
                            :state, :revision, :expires_at, :invalidated_by,
                            :created_at, :created_at)"""
                ),
                {
                    "proposal_id": proposal.proposal_id,
                    "logical_action_id": proposal.logical_action_id,
                    "run_id": proposal.run_id,
                    "tenant_id": proposal.tenant_id,
                    "graph_hash": proposal.graph_hash,
                    "supporting": _json(list(proposal.supporting_claim_ids)),
                    "payload": proposal.payload.model_dump_json(),
                    "digest": proposal.payload_digest,
                    "key": proposal.idempotency_key,
                    "state": proposal.state.value,
                    "revision": proposal.revision,
                    "expires_at": proposal.expires_at,
                    "invalidated_by": proposal.invalidated_by_proposal_id,
                    "created_at": proposal.created_at,
                },
            )
            await self._append_audit(
                session,
                proposal.run_id,
                proposal.created_at,
                "resolveflow-service",
                "service",
                "proposal.created",
                "ok",
                {"proposal_id": proposal.proposal_id, "payload_digest": proposal.payload_digest},
            )

    async def approve(self, command: ApprovalCommand, *, now: datetime) -> ActionDecision:
        async with self.sessions() as session, session.begin():
            result = await session.execute(
                text("SELECT * FROM action_proposals WHERE proposal_id = :id FOR UPDATE"),
                {"id": command.proposal_id},
            )
            row = result.mappings().one_or_none()
            if row is None:
                raise LookupError("proposal_not_found")
            proposal = _proposal_from_row(row)
            decision = self.service.approve(proposal, command, now)
            event_name = "approval.granted" if decision.accepted else "approval.denied"
            await self._append_audit(
                session,
                proposal.run_id,
                now,
                command.actor_id,
                "human" if command.human else "service",
                event_name,
                "ok" if decision.accepted else "rejected",
                {"proposal_id": proposal.proposal_id, "reason_code": decision.code},
            )
            if not decision.accepted or decision.approval is None:
                if decision.proposal.state is ActionState.EXPIRED:
                    await session.execute(
                        text(
                            """UPDATE action_proposals SET state = 'expired',
                               updated_at = :now WHERE proposal_id = :id"""
                        ),
                        {"now": now, "id": proposal.proposal_id},
                    )
                return decision
            approval = decision.approval
            await session.execute(
                text(
                    """UPDATE action_proposals SET state = 'approved',
                       updated_at = :now WHERE proposal_id = :id"""
                ),
                {"now": now, "id": proposal.proposal_id},
            )
            await session.execute(
                text(
                    """INSERT INTO approvals
                    (approval_id, proposal_id, payload_digest, approver_id,
                     permission_result, approved_at, expires_at)
                    VALUES (:approval_id, :proposal_id, :digest, :approver,
                            'allowed', :approved_at, :expires_at)"""
                ),
                {
                    "approval_id": approval.approval_id,
                    "proposal_id": approval.proposal_id,
                    "digest": approval.payload_digest,
                    "approver": approval.approver_id,
                    "approved_at": approval.approved_at,
                    "expires_at": approval.expires_at,
                },
            )
            await session.execute(
                text(
                    """INSERT INTO action_idempotency
                    (logical_action_id, idempotency_key, proposal_id, status,
                     created_at, updated_at)
                    VALUES (:logical, :key, :proposal, 'unused', :now, :now)"""
                ),
                {
                    "logical": proposal.logical_action_id,
                    "key": proposal.idempotency_key,
                    "proposal": proposal.proposal_id,
                    "now": now,
                },
            )
            await session.execute(
                text(
                    """INSERT INTO jobs
                    (job_id, kind, status, payload, run_id, logical_key, available_at,
                     attempt_count, max_attempts, cancellation_requested, updated_at)
                    VALUES (:job, 'action_dispatch', 'queued', CAST(:payload AS json), :run,
                            :logical, :now, 0, 5, false, :now)"""
                ),
                {
                    "job": f"job_{proposal.proposal_id}",
                    "payload": _json({"proposal_id": proposal.proposal_id}),
                    "run": proposal.run_id,
                    "logical": f"dispatch:{proposal.logical_action_id}",
                    "now": now,
                },
            )
            return decision

    async def record_dispatch_result(self, result: DispatchResult, *, now: datetime) -> None:
        attempt = result.attempt
        if attempt is None:
            raise ValueError("dispatch result has no attempt")
        proposal = result.proposal
        async with self.sessions() as session, session.begin():
            current = await session.execute(
                text(
                    """SELECT state, payload_digest FROM action_proposals
                       WHERE proposal_id = :id FOR UPDATE"""
                ),
                {"id": proposal.proposal_id},
            )
            row = current.mappings().one_or_none()
            if row is None:
                raise LookupError("proposal_not_found")
            if row["payload_digest"] != attempt.payload_digest:
                raise ValueError("attempt_payload_digest_mismatch")
            await session.execute(
                text(
                    """INSERT INTO action_attempts
                    (attempt_id, proposal_id, logical_action_id, idempotency_key,
                     payload_digest, attempt_number, started_at, finished_at,
                     request_fingerprint, disposition, safe_error_code,
                     retry_decision, reconciliation, remote_issue_key)
                    VALUES (:attempt_id, :proposal_id, :logical_action_id, :key,
                            :digest, :number, :started_at, :finished_at,
                            :fingerprint, :disposition, :error, :retry,
                            CAST(:reconciliation AS json), :remote_issue_key)"""
                ),
                {
                    "attempt_id": attempt.attempt_id,
                    "proposal_id": attempt.proposal_id,
                    "logical_action_id": attempt.logical_action_id,
                    "key": attempt.idempotency_key,
                    "digest": attempt.payload_digest,
                    "number": attempt.attempt_number,
                    "started_at": attempt.started_at,
                    "finished_at": attempt.finished_at,
                    "fingerprint": attempt.request_fingerprint,
                    "disposition": attempt.disposition.value,
                    "error": attempt.safe_error_code,
                    "retry": attempt.retry_decision,
                    "reconciliation": _json(
                        attempt.reconciliation.model_dump(mode="json")
                        if attempt.reconciliation
                        else None
                    ),
                    "remote_issue_key": attempt.remote_issue_key,
                },
            )
            await session.execute(
                text(
                    """UPDATE action_proposals SET state = :state, updated_at = :now
                       WHERE proposal_id = :id"""
                ),
                {"state": proposal.state.value, "now": now, "id": proposal.proposal_id},
            )
            ledger_state = (
                "complete" if proposal.state is ActionState.COMPLETE else proposal.state.value
            )
            await session.execute(
                text(
                    """UPDATE action_idempotency
                       SET status = :status, remote_issue_key = :remote, updated_at = :now
                       WHERE logical_action_id = :logical AND idempotency_key = :key"""
                ),
                {
                    "status": ledger_state,
                    "remote": attempt.remote_issue_key,
                    "now": now,
                    "logical": proposal.logical_action_id,
                    "key": proposal.idempotency_key,
                },
            )
            await self._append_audit(
                session,
                proposal.run_id,
                now,
                "worker_action_dispatch",
                "worker",
                "connector.attempt.completed",
                proposal.state.value,
                {
                    "proposal_id": proposal.proposal_id,
                    "attempt_number": attempt.attempt_number,
                    "disposition": attempt.disposition.value,
                    "retry_decision": attempt.retry_decision,
                    "remote_issue_key": attempt.remote_issue_key,
                },
            )

    async def _append_audit(
        self,
        session: AsyncSession,
        run_id: str,
        occurred_at: datetime,
        actor_id: str,
        actor_type: str,
        event_name: str,
        outcome: str,
        detail: dict[str, Any],
    ) -> None:
        result = await session.execute(
            text(
                """SELECT sequence, event_hash FROM audit_events
                   WHERE run_id = :run_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE"""
            ),
            {"run_id": run_id},
        )
        previous = result.mappings().one_or_none()
        sequence = int(previous["sequence"]) + 1 if previous else 1
        previous_hash = str(previous["event_hash"]) if previous else None
        record = make_audit_record(
            run_id=run_id,
            sequence=sequence,
            occurred_at=occurred_at,
            actor_id=actor_id,
            actor_type=actor_type,  # type: ignore[arg-type]
            component="actions",
            event_name=event_name,
            outcome=outcome,
            safe_detail=detail,
            previous_event_hash=previous_hash,
        )
        await session.execute(
            text(
                """INSERT INTO audit_events
                (event_id, run_id, sequence, event_name, safe_detail, event_hash, created_at,
                 actor_id, actor_type, component, outcome, duration_ms, correlation_ids,
                 versions, trace_id, span_id, previous_event_hash)
                VALUES (:event_id, :run_id, :sequence, :event_name, CAST(:detail AS json),
                        :event_hash, :occurred_at, :actor_id, :actor_type, 'actions', :outcome,
                        :duration_ms, CAST(:correlations AS json), CAST(:versions AS json),
                        :trace_id, :span_id, :previous_hash)"""
            ),
            {
                "event_id": record.event_id,
                "run_id": record.run_id,
                "sequence": record.sequence,
                "event_name": record.event_name,
                "detail": _json(record.safe_detail),
                "event_hash": record.event_hash,
                "occurred_at": record.occurred_at,
                "actor_id": record.actor_id,
                "actor_type": record.actor_type,
                "outcome": record.outcome,
                "duration_ms": record.duration_ms,
                "correlations": _json(record.correlation_ids),
                "versions": _json(record.versions),
                "trace_id": record.trace_id,
                "span_id": record.span_id,
                "previous_hash": record.previous_event_hash,
            },
        )


def _proposal_from_row(row: Any) -> ActionProposal:
    return ActionProposal(
        proposal_id=row["proposal_id"],
        logical_action_id=row["logical_action_id"],
        run_id=row["run_id"],
        tenant_id=row["tenant_id"],
        graph_hash=row["graph_hash"],
        supporting_claim_ids=tuple(row["supporting_claim_ids"]),
        payload=ActionPayload.model_validate(row["payload"]),
        payload_digest=row["payload_digest"],
        idempotency_key=row["idempotency_key"],
        state=ActionState(row["state"]),
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        revision=row["revision"],
        invalidated_by_proposal_id=row["invalidated_by_proposal_id"],
    )


def _json(value: Any) -> str:
    import json

    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _affected(result: Any) -> bool:
    return int(result.rowcount) == 1
