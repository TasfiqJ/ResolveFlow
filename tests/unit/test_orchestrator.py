from __future__ import annotations

from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator


def test_shared_path_produces_cited_result_trace_and_inert_proposal() -> None:
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(), GovernedAgent(FixtureChatAdapter())
    )
    result = orchestrator.run(canonical_hero_case())
    assert result.response.route == "Payments Platform"
    assert len(result.response.citations) >= 2
    assert result.response.unknowns == ("The affected cluster ID is not available.",)
    assert result.action.state == "pending_approval"
    assert result.action.connector == "synthetic_not_dispatched"
    assert [event.sequence for event in result.trace] == list(range(1, 9))
    assert result.provenance == "recorded_fixture"
    assert result.response.graph_hash == result.evidence_graph["graph_hash"]
    assert all(trace["pass_kind"] in {"evidence", "structure"} for trace in result.provider_traces)
    assert all("reasoning" not in trace for trace in result.provider_traces)
    assert result.forbidden_effect_score["successful_count"] == 0
    for trace in result.provider_traces:
        assert not ({"text", "messages", "prompt", "reasoning"} & set(trace))
    repeated = ResolveOrchestrator(
        FixtureContextRepository(), GovernedAgent(FixtureChatAdapter())
    ).run(canonical_hero_case())
    assert repeated.content_hash == result.content_hash
