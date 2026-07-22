from __future__ import annotations

from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.findings import (
    CitationDraft,
    ClaimDraft,
    ClaimKind,
    FirstPassFindings,
)
from resolveflow.verifier import EvidenceVerifier
from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import governed_inputs


def test_stale_source_cannot_support_current_action() -> None:
    _, _, corpus, identity, _ = governed_inputs()
    stale_chunk = next(
        item for item in corpus.chunks if item.artifact_version_id == "artifact_runbook_payments_v2"
    )
    document = UntrustedEvidenceDocument(
        document_id=stale_chunk.chunk_id,
        artifact_id="artifact_runbook_payments",
        artifact_version_id=stale_chunk.artifact_version_id,
        title="Payments rollback runbook",
        version="2",
        locator=stale_chunk.position.locator,
        content=stale_chunk.content,
        content_checksum=stale_chunk.checksum,
    )
    graph = EvidenceVerifier().verify(
        run_id="run_stale",
        findings=FirstPassFindings(
            claims=(
                ClaimDraft(
                    claim_id="claim_stale_action",
                    kind=ClaimKind.ACTION,
                    text="Retry the deployment before rollback.",
                    subject="action",
                    value="retry deployment",
                    current_support_required=True,
                    action_supporting=True,
                    citation_ids=("cite_stale",),
                ),
            ),
            citations=(
                CitationDraft(
                    citation_id="cite_stale",
                    document_id=stale_chunk.chunk_id,
                    exact_quote="retry the deployment before considering a rollback",
                ),
            ),
            unknowns=(),
            requested_proposal="create_jira_issue",
        ),
        documents=(document,),
        identity=identity,
        corpus=corpus,
    )
    assert graph.claims[0].status is SupportStatus.UNSUPPORTED
    assert "citation_fresh_failed" in graph.citations[0].verifier_codes
    assert graph.permitted_proposals == ()
