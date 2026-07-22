from __future__ import annotations

from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.findings import CitationDraft, ClaimDraft, ClaimKind, FirstPassFindings
from resolveflow.verifier import EvidenceVerifier
from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import governed_inputs
from tests.security.test_forbidden_candidate import _retrieve


def test_candidate_projection_cannot_supply_forbidden_citation() -> None:
    trace = _retrieve("contractor")
    assert all(item.artifact_id != "artifact_restricted_legal" for item in trace.candidates)


def test_injected_unauthorized_citation_is_rejected_by_verifier() -> None:
    _, _, corpus, identity, _ = governed_inputs(role="contractor")
    chunk = next(
        item for item in corpus.chunks if item.artifact_version_id == "artifact_restricted_legal_v1"
    )
    document = UntrustedEvidenceDocument(
        document_id=chunk.chunk_id,
        artifact_id="artifact_restricted_legal",
        artifact_version_id=chunk.artifact_version_id,
        title="Restricted payments legal memo",
        version="1",
        locator=chunk.position.locator,
        content=chunk.content,
        content_checksum=chunk.checksum,
    )
    graph = EvidenceVerifier().verify(
        run_id="run_forbidden_citation",
        findings=FirstPassFindings(
            claims=(
                ClaimDraft(
                    claim_id="claim_forbidden",
                    kind=ClaimKind.FACT,
                    text="Legal review material exists.",
                    subject="legal_review",
                    value="legal review",
                    citation_ids=("cite_forbidden",),
                ),
            ),
            citations=(
                CitationDraft(
                    citation_id="cite_forbidden",
                    document_id=chunk.chunk_id,
                    exact_quote="Legal review material",
                ),
            ),
            unknowns=(),
        ),
        documents=(document,),
        identity=identity,
        corpus=corpus,
    )
    assert graph.citations[0].authorized is False
    assert graph.claims[0].status is SupportStatus.UNSUPPORTED
