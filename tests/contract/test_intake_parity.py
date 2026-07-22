from __future__ import annotations

from resolveflow.intake.slack import SlackEvent, SlackIntakeStore
from resolveflow.intake.web import canonical_hero_case


def test_web_and_slack_share_canonical_schema() -> None:
    web = canonical_hero_case()
    event = SlackEvent(
        event_id="Ev1",
        event_time=int(web.case_time.timestamp()),
        team_id="T_SYNTHETIC",
        event={
            "event_ts": "1.0",
            "channel": web.channel,
            "user": "U_SYNTHETIC",
            "text": web.raw_text,
        },
    )
    slack, duplicate = SlackIntakeStore().accept(event)
    assert duplicate is False
    assert type(slack) is type(web)
    assert slack.raw_text == web.raw_text
    assert slack.error_code == web.error_code
    assert slack.source_system == "slack_fixture"


def test_duplicate_delivery_returns_same_case() -> None:
    store = SlackIntakeStore()
    event = SlackEvent(event_id="Ev1", event_time=1, team_id="T1", event={"event_ts": "1.0"})
    first, first_duplicate = store.accept(event)
    second, second_duplicate = store.accept(event)
    assert first_duplicate is False
    assert second_duplicate is True
    assert first == second
    assert len(store.cases_by_delivery) == 1
