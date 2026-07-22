from __future__ import annotations

from typing import Any, Literal

from resolveflow.domain.base import FrozenModel


class RunReconstruction(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    route: str | None
    action_state: str | None
    payload_digest: str | None
    event_count: int
    complete: bool


def reconstruct_from_events(events: list[dict[str, Any]] | tuple[Any, ...]) -> RunReconstruction:
    normalized = [
        event.model_dump(mode="json") if hasattr(event, "model_dump") else event for event in events
    ]
    ordered = sorted(normalized, key=lambda item: int(item["sequence"]))
    if [int(item["sequence"]) for item in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("audit event sequence has a gap")
    route: str | None = None
    action_state: str | None = None
    payload_digest: str | None = None
    for event in ordered:
        detail = event.get("safe_detail", {})
        if event.get("event_name") == "evidence_graph.verified":
            route = detail.get("route")
        if event.get("event_name") in {"proposal.created", "proposal.blocked"}:
            action_state = detail.get("state")
            payload_digest = detail.get("payload_digest")
    return RunReconstruction(
        route=route,
        action_state=action_state,
        payload_digest=payload_digest,
        event_count=len(ordered),
        complete=route is not None and action_state is not None,
    )
