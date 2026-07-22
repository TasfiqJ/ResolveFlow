from __future__ import annotations

import pytest
from pydantic import ValidationError
from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.findings import (
    CitationDraft,
    ClaimDraft,
    ClaimKind,
    FirstPassFindings,
)
from resolveflow.verifier import EvidenceVerifier
from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import governed_inputs, run_governed


def test_material_claim_schema_requires_a_citation_mapping() -> None:
    with pytest.raises(ValidationError, match="material claims require"):
        ClaimDraft(
            claim_id="unsupported",
            kind=ClaimKind.ACTION,
            text="Create an issue now.",
            subject="action",
            value="create",
            material=True,
            action_supporting=True,
            citation_ids=(),
        )


def test_action_proposal_exists_only_when_action_support_is_verified() -> None:
    graph = run_governed().evidence_graph
    action = next(item for item in graph.claims if item.action_supporting)
    assert action.status is SupportStatus.SUPPORTED
    assert graph.permitted_proposals


def test_absent_from_context_citation_is_rejected() -> None:
    _, _, corpus, identity, _ = governed_inputs()
    graph = EvidenceVerifier().verify(
        run_id="run_absent_context",
        findings=FirstPassFindings(
            claims=(
                ClaimDraft(
                    claim_id="claim_absent",
                    kind=ClaimKind.FACT,
                    text="The rollout completed.",
                    subject="rollout_status",
                    value="completed",
                    citation_ids=("cite_absent",),
                ),
            ),
            citations=(
                CitationDraft(
                    citation_id="cite_absent",
                    document_id="chunk_never_sent_to_model",
                    exact_quote="completed",
                ),
            ),
            unknowns=(),
        ),
        documents=(),
        identity=identity,
        corpus=corpus,
    )
    assert graph.citations[0].in_context is False
    assert graph.claims[0].status is SupportStatus.UNSUPPORTED


def test_exact_structured_conflict_is_preserved_in_graph() -> None:
    _, _, corpus, identity, retrieval = governed_inputs()
    candidates = {
        item.artifact_id: item
        for item in retrieval.candidates
        if item.artifact_id in {"artifact_runbook_payments", "artifact_prior_incident_1042"}
    }
    documents = tuple(
        UntrustedEvidenceDocument(
            document_id=item.chunk_id,
            artifact_id=item.artifact_id,
            artifact_version_id=item.artifact_version_id,
            title=item.title,
            version="3" if item.artifact_id == "artifact_runbook_payments" else "1",
            locator=item.position.locator,
            content=item.content,
            content_checksum=item.content_checksum,
        )
        for item in candidates.values()
    )
    runbook = candidates["artifact_runbook_payments"]
    prior = candidates["artifact_prior_incident_1042"]
    graph = EvidenceVerifier().verify(
        run_id="run_conflict",
        findings=FirstPassFindings(
            claims=(
                ClaimDraft(
                    claim_id="route_payments",
                    kind=ClaimKind.ROUTE,
                    text="Route issuer-routing failures to Payments Platform.",
                    subject="route",
                    value="Payments Platform",
                    citation_ids=("cite_payments",),
                ),
                ClaimDraft(
                    claim_id="route_incident_operations",
                    kind=ClaimKind.ROUTE,
                    text="prior-incident-1042.",
                    subject="route",
                    value="prior-incident-1042",
                    citation_ids=("cite_other",),
                ),
            ),
            citations=(
                CitationDraft(
                    citation_id="cite_payments",
                    document_id=runbook.chunk_id,
                    exact_quote="Route issuer-routing failures to Payments Platform.",
                ),
                CitationDraft(
                    citation_id="cite_other",
                    document_id=prior.chunk_id,
                    exact_quote='"artifact_id":"prior-incident-1042"',
                ),
            ),
            unknowns=(),
        ),
        documents=documents,
        identity=identity,
        corpus=corpus,
    )
    assert len(graph.conflicts) == 1
    assert all(item.status is SupportStatus.CONFLICTED for item in graph.claims)
