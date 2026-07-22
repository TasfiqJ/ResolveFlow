from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import stable_id
from resolveflow.domain.hashing import checksum


class AuditRecord(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    event_id: str
    run_id: str
    sequence: int = Field(ge=1)
    occurred_at: datetime
    actor_id: str
    actor_type: Literal["human", "service", "worker", "connector"]
    component: str
    event_name: str
    outcome: str
    duration_ms: int = Field(ge=0)
    correlation_ids: dict[str, str]
    versions: dict[str, str]
    safe_detail: dict[str, Any]
    trace_id: str | None = None
    span_id: str | None = None
    previous_event_hash: str | None = None
    event_hash: str


def make_audit_record(
    *,
    run_id: str,
    sequence: int,
    occurred_at: datetime,
    actor_id: str,
    actor_type: Literal["human", "service", "worker", "connector"],
    component: str,
    event_name: str,
    outcome: str,
    safe_detail: dict[str, Any],
    correlation_ids: dict[str, str] | None = None,
    versions: dict[str, str] | None = None,
    duration_ms: int = 0,
    trace_id: str | None = None,
    span_id: str | None = None,
    previous_event_hash: str | None = None,
) -> AuditRecord:
    body = {
        "schema_version": "1.0",
        "run_id": run_id,
        "sequence": sequence,
        "occurred_at": occurred_at,
        "actor_id": actor_id,
        "actor_type": actor_type,
        "component": component,
        "event_name": event_name,
        "outcome": outcome,
        "duration_ms": duration_ms,
        "correlation_ids": correlation_ids or {"run_id": run_id},
        "versions": versions or {},
        "safe_detail": safe_detail,
        "trace_id": trace_id,
        "span_id": span_id,
        "previous_event_hash": previous_event_hash,
    }
    event_hash = checksum(body)
    return AuditRecord(
        event_id=stable_id("audit", {"run_id": run_id, "sequence": sequence, "hash": event_hash}),
        **body,
        event_hash=event_hash,
    )


def verify_audit_chain(events: tuple[AuditRecord, ...]) -> bool:
    previous: str | None = None
    for expected, event in enumerate(events, 1):
        if event.sequence != expected or event.previous_event_hash != previous:
            return False
        body = event.model_dump(exclude={"event_id", "event_hash"}, mode="python")
        if checksum(body) != event.event_hash:
            return False
        previous = event.event_hash
    return True
