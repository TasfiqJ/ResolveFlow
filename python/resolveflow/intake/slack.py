from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import CanonicalCase
from resolveflow.intake.web import canonical_hero_case


class SlackVerificationError(ValueError):
    """A safe, stable rejection from the Slack authenticity boundary."""


class SlackEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    event_id: str = Field(min_length=1)
    event_time: int
    team_id: str = Field(min_length=1)
    event: dict[str, object]


@dataclass(frozen=True)
class SlackRequestVerifier:
    signing_secret: str
    replay_window_seconds: int = 300
    clock: Callable[[], float] = time.time

    def verify(self, raw_body: bytes, timestamp: str, signature: str) -> None:
        try:
            signed_at = int(timestamp)
        except ValueError as exc:
            raise SlackVerificationError("slack_timestamp_invalid") from exc
        if abs(int(self.clock()) - signed_at) > self.replay_window_seconds:
            raise SlackVerificationError("slack_timestamp_stale")
        base = b"v0:" + timestamp.encode("ascii") + b":" + raw_body
        expected = (
            "v0=" + hmac.new(self.signing_secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(expected, signature):
            raise SlackVerificationError("slack_signature_invalid")


@dataclass
class SlackIntakeStore:
    """Small fixture store; production persistence uses the same event/case keys."""

    cases_by_delivery: dict[str, CanonicalCase] = field(default_factory=dict)

    def accept(self, payload: SlackEvent) -> tuple[CanonicalCase, bool]:
        event_ts = str(payload.event.get("event_ts", ""))
        delivery_key = checksum({"event_id": payload.event_id, "event_ts": event_ts})
        existing = self.cases_by_delivery.get(delivery_key)
        if existing is not None:
            return existing, True
        base = canonical_hero_case()
        raw_text = str(payload.event.get("text", base.raw_text))
        event_time = datetime.fromtimestamp(payload.event_time, tz=timezone.utc)
        case = base.model_copy(
            update={
                "source_system": "slack_fixture",
                "channel": str(payload.event.get("channel", base.channel)),
                "reporter": f"Slack user {payload.event.get('user', 'synthetic')} (synthetic)",
                "received_at": event_time,
                "case_time": event_time,
                "raw_text": raw_text,
                "checksum": checksum(
                    {
                        "schema_version": base.schema_version,
                        "event_id": payload.event_id,
                        "event_ts": event_ts,
                        "raw_text": raw_text,
                    }
                ),
            }
        )
        self.cases_by_delivery[delivery_key] = case
        return case, False


def parse_slack_event(raw_body: bytes) -> tuple[SlackEvent | None, str | None]:
    payload = json.loads(raw_body)
    if payload.get("type") == "url_verification":
        return None, str(payload.get("challenge", ""))
    return SlackEvent.model_validate(payload), None
