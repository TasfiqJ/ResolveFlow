from __future__ import annotations

from resolveflow.agent.fixture import FixtureAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator


def test_shared_path_produces_cited_result_trace_and_inert_proposal() -> None:
    result = ResolveOrchestrator(FixtureContextRepository(), FixtureAgent()).run(
        canonical_hero_case()
    )
    assert result.response.route == "Payments Platform"
    assert len(result.response.citations) == 2
    assert result.response.unknowns == ("The affected cluster ID is not available.",)
    assert result.action.state == "pending_approval"
    assert result.action.connector == "synthetic_not_dispatched"
    assert [event.sequence for event in result.trace] == list(range(1, 7))
    assert result.provenance == "recorded_fixture"
