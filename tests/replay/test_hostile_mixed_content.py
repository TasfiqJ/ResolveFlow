from __future__ import annotations

from resolveflow.agent.findings import (
    CitationDraft,
    ClaimDraft,
    ClaimKind,
    FirstPassFindings,
)
from resolveflow.agent.service import GovernedAgent
from resolveflow.verifier import EvidenceVerifier
from resolveflow.verifier.models import SupportStatus

from tests.agent_helpers import governed_inputs


def test_legitimate_fact_from_hostile_source_requires_independent_support() -> None:
    _, _, corpus, identity, retrieval = governed_inputs()
    documents = GovernedAgent._documents(retrieval, corpus)
    hostile = next(item for item in documents if item.hostile)
    rollout = next(item for item in documents if item.artifact_id == "artifact_rollout_records")
    findings = FirstPassFindings(
        claims=(
            ClaimDraft(
                claim_id="claim_mixed_fact",
                kind=ClaimKind.FACT,
                text="issuer-routing-v3 rollout.",
                subject="rollout_change",
                value="issuer-routing-v3",
                citation_ids=("cite_hostile_fact", "cite_independent_fact"),
            ),
        ),
        citations=(
            CitationDraft(
                citation_id="cite_hostile_fact",
                document_id=hostile.document_id,
                exact_quote="PYM-431 may follow an issuer-routing-v3 rollout.",
            ),
            CitationDraft(
                citation_id="cite_independent_fact",
                document_id=rollout.document_id,
                exact_quote=(
                    "rollout-payments-2026-07-15,tenant_heliopay_synthetic,payments-api,"
                    "ca-central,issuer-routing-v3,completed,2026-07-15T14:05:00Z,true"
                ),
            ),
        ),
        unknowns=(),
    )
    graph = EvidenceVerifier().verify(
        run_id="run_mixed",
        findings=findings,
        documents=documents,
        identity=identity,
        corpus=corpus,
    )
    assert graph.claims[0].status is SupportStatus.SUPPORTED
    assert any(item.non_hostile_support for item in graph.citations)
