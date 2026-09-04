from __future__ import annotations

import pytest
from pydantic import ValidationError
from resolveflow.actions.service import ActionService, fixture_now
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


@pytest.mark.parametrize(
    ("kind", "action_supporting"),
    [(ClaimKind.FACT, True), (ClaimKind.ACTION, False)],
)
def test_action_supporting_is_exactly_equivalent_to_action_kind(
    kind: ClaimKind, action_supporting: bool
) -> None:
    with pytest.raises(ValidationError, match="exactly for action claims"):
        ClaimDraft(
            claim_id="invalid-action-kind",
            kind=kind,
            text="Invalid action marker.",
            subject="action",
            value="invalid",
            action_supporting=action_supporting,
            citation_ids=("cite-invalid",),
        )


def test_action_proposal_exists_only_when_action_support_is_verified() -> None:
    graph = run_governed().evidence_graph
    action = next(item for item in graph.claims if item.action_supporting)
    assert action.status is SupportStatus.SUPPORTED
    assert graph.permitted_proposals


def test_verifier_and_action_service_reject_a_bypassed_action_kind_invariant() -> None:
    result = run_governed()
    graph = result.evidence_graph
    action_claim = next(item for item in graph.claims if item.kind is ClaimKind.ACTION)
    forged_claim = action_claim.model_copy(update={"kind": ClaimKind.FACT})
    forged_graph = graph.model_copy(
        update={
            "claims": tuple(
                forged_claim if item.claim_id == action_claim.claim_id else item
                for item in graph.claims
            )
        }
    )

    with pytest.raises(ValueError, match="verified action claims"):
        ActionService().create_proposal(
            run_id=forged_graph.run_id,
            tenant_id="tenant_heliopay_synthetic",
            graph=forged_graph,
            response=result.response,
            now=fixture_now(),
        )


def test_verifier_does_not_mint_proposal_for_bypassed_action_kind_invariant() -> None:
    _, _, corpus, identity, retrieval = governed_inputs()
    candidate = next(
        item for item in retrieval.candidates if item.artifact_id == "artifact_prior_incident_1042"
    )
    document = UntrustedEvidenceDocument(
        document_id=candidate.chunk_id,
        artifact_id=candidate.artifact_id,
        artifact_version_id=candidate.artifact_version_id,
        title=candidate.title,
        version="1",
        locator=candidate.position.locator,
        content=candidate.content,
        content_checksum=candidate.content_checksum,
    )
    valid_action = ClaimDraft(
        claim_id="forged-kind",
        kind=ClaimKind.ACTION,
        text="Payments Platform",
        subject="proposal_team",
        value="Payments Platform",
        action_supporting=True,
        citation_ids=("cite-forged-kind",),
    )
    forged_claim = valid_action.model_copy(update={"kind": ClaimKind.FACT})
    findings = FirstPassFindings.model_construct(
        schema_version="1.0",
        claims=(forged_claim,),
        citations=(
            CitationDraft(
                citation_id="cite-forged-kind",
                document_id=document.document_id,
                exact_quote='"route":"Payments Platform"',
            ),
        ),
        unknowns=(),
        requested_proposal="create_jira_issue",
    )

    graph = EvidenceVerifier().verify(
        run_id="run-forged-action-kind",
        findings=findings,
        documents=(document,),
        identity=identity,
        corpus=corpus,
    )

    assert graph.claims[0].status is SupportStatus.UNSUPPORTED
    assert "claim_action_kind_invariant_failed" in graph.citations[0].verifier_codes
    assert graph.permitted_proposals == ()


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
                    text="prior-incident-1042",
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


@pytest.mark.parametrize(
    ("claim_text", "claim_value", "quote"),
    [
        ("rollout is complete", "complete", "rollout is not complete"),
        ("replication succeeded", "succeeded", "replication never succeeded"),
        ("deployment approved", "approved", "no deployment was approved"),
        ("migration succeeded", "succeeded", "migration failed before it succeeded"),
    ],
)
def test_verifier_rejects_non_verbatim_polarity_flips(
    claim_text: str, claim_value: str, quote: str
) -> None:
    assert (
        EvidenceVerifier._supports(
            ClaimDraft(
                claim_id="polarity",
                kind=ClaimKind.FACT,
                text=claim_text,
                subject="status",
                value=claim_value,
                citation_ids=("citation",),
            ),
            quote,
        )
        is False
    )
