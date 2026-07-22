from __future__ import annotations

import json
from typing import Any

from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.telemetry.projection import public_projection


def export_run_json(snapshot: Any, *, public: bool) -> str:
    body = public_projection(snapshot) if public else _as_mapping(snapshot)
    envelope = {"schema_version": "1.0", "public": public, "run": body}
    envelope["export_checksum"] = checksum(envelope)
    return json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def export_run_markdown(snapshot: Any, *, public: bool) -> str:
    body = public_projection(snapshot) if public else _as_mapping(snapshot)
    run_id = str(body.get("run_id", "unknown"))
    build_id = str(body.get("build_id", "unknown"))
    action = body.get("action", {})
    trace = body.get("trace", [])
    lines = [
        f"# ResolveFlow run {run_id}",
        "",
        f"- Build: `{build_id}`",
        f"- Projection: `{'public' if public else 'maintainer'}`",
        f"- Action state: `{action.get('state', 'none') if isinstance(action, dict) else 'none'}`",
        "",
        "## Timeline",
        "",
    ]
    if isinstance(trace, list):
        for event in trace:
            if isinstance(event, dict):
                lines.append(
                    f"{event.get('sequence', '?')}. `{event.get('component', 'unknown')}` "
                    f"{event.get('event_name', 'unknown')} — {event.get('outcome', 'unknown')}"
                )
    digest = checksum({"public": public, "body": body})
    lines.extend(["", f"Export checksum: `{digest}`", ""])
    return "\n".join(lines)


def export_is_reproducible(snapshot: Any, *, public: bool) -> bool:
    first = export_run_json(snapshot, public=public)
    second = export_run_json(snapshot, public=public)
    return first == second and canonical_json(json.loads(first)) == canonical_json(
        json.loads(second)
    )


def _as_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
    else:
        dumped = value
    if not isinstance(dumped, dict):
        raise TypeError("run export root must be an object")
    return dumped
