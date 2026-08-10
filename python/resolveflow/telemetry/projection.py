from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from resolveflow.domain.hashing import checksum

# Matched against the WHOLE key, not as a substring. A substring match silently
# redacted the audit signal this artifact exists to publish: "authorization" hit
# `authorization_mode` and the ToolTrace `authorization` verdict, and "token" hit
# `input_tokens`/`output_tokens`. Those are non-secret and must stay legible; the
# credential-shaped variants below are still redacted, and _SECRET_VALUE continues
# to scrub secret-shaped values wherever they appear.
_SENSITIVE_KEY = re.compile(
    r"\A(?:"
    r"[a-z0-9]*[_-]?(?:cookie|credentials?|secret|password|passphrase)(?:[_-][a-z0-9]+)*"
    r"|[a-z0-9]*[_-]?api[_-]?keys?"
    r"|authorization[_-]?(?:header|value)"
    r"|(?:access|refresh|bearer|auth|session|signing|id|api)[_-]?tokens?"
    r"|token"
    r"|hidden[_-]?prompt|system[_-]?prompt"
    r"|reasoning|chain[_-]?of[_-]?thought"
    r"|stack|stack[_-]?trace|traceback"
    r"|private[_-]?path|source[_-]?path"
    r"|raw[_-]?payload|provider[_-]?payload"
    r")\Z",
    re.I,
)
# Keys that the whole-key pattern would otherwise catch but which carry no secret
# and are load-bearing for public auditability.
_PUBLIC_SAFE_KEYS = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "reasoning_tokens",
        "billed_tokens",
        "max_total_tokens",
    }
)
_PRIVATE_PATH = re.compile(r"(?:[A-Za-z]:\\Users\\|/(?:home|Users|mnt/c/Users)/)[^\s]+")
_SECRET_VALUE = re.compile(
    r"(?:Bearer\s+[A-Za-z0-9._~-]{12,}|sk-[A-Za-z0-9_-]{12,}|"
    r"xox[baprs]-[A-Za-z0-9-]{12,}|ATATT[A-Za-z0-9_-]{12,})",
    re.I,
)


def _project(value: Any, key: str | None = None) -> Any:
    if key and key.lower() not in _PUBLIC_SAFE_KEYS and _SENSITIVE_KEY.match(key):
        return "[REDACTED]"
    if isinstance(value, BaseModel):
        return _project(value.model_dump(mode="python"), key)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, dict):
        if value.get("classification") == "restricted" or value.get("restricted") is True:
            return {
                "redacted": True,
                "reason_code": "restricted_content_removed",
                "checksum": checksum(value),
            }
        return {
            str(item_key): _project(value[item_key], str(item_key)) for item_key in sorted(value)
        }
    if isinstance(value, list | tuple):
        return [_project(item) for item in value]
    if isinstance(value, str):
        redacted = _PRIVATE_PATH.sub("[PRIVATE_PATH]", value)
        redacted = _SECRET_VALUE.sub("[SECRET]", redacted)
        return redacted
    return value


def public_projection(value: Any) -> dict[str, Any]:
    projected = _project(value)
    if not isinstance(projected, dict):
        raise TypeError("public projection root must be an object")
    return projected


def public_projection_checksum(value: Any) -> str:
    return checksum(public_projection(value))
