from __future__ import annotations

from resolveflow.agent.security import score_forbidden_effects

from tests.agent_helpers import run_governed


def test_hostile_scenario_records_attempted_effects_not_verbal_refusal() -> None:
    result = run_governed()
    score = score_forbidden_effects(result.security_events)
    assert score.attempted_count >= 1
    assert score.successful_count == 0
    assert all(
        item.observable_source == "untrusted_evidence_scan" for item in result.security_events
    )
    assert all("refus" not in item.safe_detail.lower() for item in result.security_events)
