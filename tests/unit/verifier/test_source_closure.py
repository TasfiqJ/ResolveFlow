from __future__ import annotations

from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import run_governed


def test_every_final_material_claim_closes_over_verified_graph() -> None:
    result = run_governed()
    claims = {item.claim_id: item for item in result.evidence_graph.claims}
    assert result.response.claim_ids
    assert all(claims[item].status is SupportStatus.SUPPORTED for item in result.response.claim_ids)
    citation_claims = {item.claim_id for item in result.response.citations}
    assert set(result.response.claim_ids).issubset(citation_claims)
    assert result.response.graph_hash == result.evidence_graph.graph_hash


def test_graph_hash_is_canonical_for_identical_inputs() -> None:
    assert run_governed().evidence_graph.graph_hash == run_governed().evidence_graph.graph_hash
