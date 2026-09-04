from __future__ import annotations

import pytest
from resolveflow.agent.renderer import DeterministicRenderer, StructureSelection

from tests.agent_helpers import run_governed


def test_identical_verified_selection_renders_identically() -> None:
    result = run_governed()
    graph = result.evidence_graph
    renderer = DeterministicRenderer()
    route = next(item.claim_id for item in graph.claims if item.kind.value == "route")
    fact = next(item.claim_id for item in graph.claims if item.kind.value == "fact")
    step = next(item.claim_id for item in graph.claims if item.kind.value == "recommendation")
    selection = StructureSelection(
        disposition="resolved",
        route_claim_id=route,
        summary_claim_ids=(fact,),
        recommended_step_claim_ids=(step,),
        unknown_ids=tuple(item.unknown_id for item in graph.unknowns),
        conflict_ids=(),
        graph_hash=graph.graph_hash,
        needs_review=False,
    )
    first = renderer.render(graph, selection, provider="recorded_fixture")
    second = renderer.render(graph, selection, provider="recorded_fixture")
    assert first == second


def test_renderer_rejects_unknown_or_unverified_claim_ids() -> None:
    graph = run_governed().evidence_graph
    selection = StructureSelection(
        disposition="resolved",
        route_claim_id="unsupported_new_fact",
        summary_claim_ids=(),
        recommended_step_claim_ids=(),
        unknown_ids=(),
        conflict_ids=(),
        graph_hash=graph.graph_hash,
        needs_review=False,
    )
    with pytest.raises(ValueError, match="unknown claim"):
        DeterministicRenderer().render(graph, selection, provider="recorded_fixture")


@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("summary_claim_ids", "summary field"),
        ("recommended_step_claim_ids", "recommended-step field"),
    ],
)
def test_renderer_rejects_verified_ids_in_the_wrong_field(field: str, error: str) -> None:
    graph = run_governed().evidence_graph
    route = next(item.claim_id for item in graph.claims if item.kind.value == "route")
    fact = next(item.claim_id for item in graph.claims if item.kind.value == "fact")
    step = next(item.claim_id for item in graph.claims if item.kind.value == "recommendation")
    selection = StructureSelection(
        disposition="resolved",
        route_claim_id=route,
        summary_claim_ids=(route,) if field == "summary_claim_ids" else (fact,),
        recommended_step_claim_ids=((fact,) if field == "recommended_step_claim_ids" else (step,)),
        unknown_ids=tuple(item.unknown_id for item in graph.unknowns),
        conflict_ids=(),
        graph_hash=graph.graph_hash,
        needs_review=False,
    )

    with pytest.raises(ValueError, match=error):
        DeterministicRenderer().render(graph, selection, provider="recorded_fixture")


def test_renderer_rejects_resolved_output_without_a_route() -> None:
    graph = run_governed().evidence_graph
    selection = StructureSelection(
        disposition="resolved",
        route_claim_id=None,
        summary_claim_ids=(),
        recommended_step_claim_ids=(),
        unknown_ids=tuple(item.unknown_id for item in graph.unknowns),
        conflict_ids=tuple(item.conflict_id for item in graph.conflicts),
        graph_hash=graph.graph_hash,
        needs_review=False,
    )

    with pytest.raises(ValueError, match="requires a verified route"):
        DeterministicRenderer().render(graph, selection, provider="recorded_fixture")


def test_renderer_cannot_suppress_verified_unknowns() -> None:
    graph = run_governed().evidence_graph
    route = next(item.claim_id for item in graph.claims if item.kind.value == "route")
    assert graph.unknowns
    selection = StructureSelection(
        disposition="resolved",
        route_claim_id=route,
        summary_claim_ids=(),
        recommended_step_claim_ids=(),
        unknown_ids=(),
        conflict_ids=tuple(item.conflict_id for item in graph.conflicts),
        graph_hash=graph.graph_hash,
        needs_review=False,
    )

    with pytest.raises(ValueError, match="preserve every verified unknown"):
        DeterministicRenderer().render(graph, selection, provider="recorded_fixture")
