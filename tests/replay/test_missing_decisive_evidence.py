from __future__ import annotations

from tests.agent_helpers import governed_inputs, run_governed


def test_missing_decisive_evidence_yields_review_without_route_or_proposal() -> None:
    _, _, _, _, retrieval = governed_inputs()
    filtered = retrieval.model_copy(
        update={
            "candidates": tuple(
                item
                for item in retrieval.candidates
                if item.artifact_id not in {"artifact_runbook_payments", "artifact_rollout_records"}
            )
        }
    )
    result = run_governed(retrieval=filtered)
    assert result.response.needs_review is True
    assert result.response.route is None
    assert result.evidence_graph.permitted_proposals == ()
