from __future__ import annotations

import json

import pytest
from pydantic import ValidationError
from resolveflow.intake.slack import SlackEvent, SlackIntakeStore, parse_slack_event


def _body(event_time: int) -> bytes:
    return json.dumps(
        {
            "event_id": "e1",
            "event_time": event_time,
            "team_id": "T",
            "event": {"text": "hi", "event_ts": "1"},
        }
    ).encode("utf-8")


@pytest.mark.parametrize("event_time", [10**18, -(10**18), 253402300800])
def test_out_of_range_event_time_is_a_safe_rejection_not_a_crash(event_time: int) -> None:
    """`event_time` was an unbounded int fed straight to datetime.fromtimestamp().

    That raises OSError/OverflowError — neither a ValueError — from `slack_store.accept`,
    which sits outside the handler's try/except, so a correctly signed request with an
    absurd timestamp produced an unhandled 500 and a stack trace instead of a 401.
    Bounding the field turns it into a ValidationError, which IS a ValueError and is
    mapped to the safe rejection path.
    """
    with pytest.raises(ValidationError) as caught:
        parse_slack_event(_body(event_time))

    assert isinstance(caught.value, ValueError)


def test_in_range_event_time_still_produces_a_case() -> None:
    event, challenge = parse_slack_event(_body(1_767_225_600))

    assert challenge is None
    assert isinstance(event, SlackEvent)
    case, duplicate = SlackIntakeStore().accept(event)
    assert duplicate is False
    assert case.received_at.year == 2026
