from __future__ import annotations

import math
import re
from collections import defaultdict

from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.findings import ClaimDraft, ClaimKind, FirstPassFindings
from resolveflow.domain.evidence import Corpus, IdentitySnapshot, stable_id
from resolveflow.domain.hashing import checksum
from resolveflow.policy.authorization import AuthorizationPolicy
from resolveflow.verifier.models import (
    EvidenceConflict,
    EvidenceGraph,
    PermittedProposal,
    RouteCandidate,
    SupportStatus,
    VerifiedCitation,
    VerifiedClaim,
)

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.I)
_STOP = {
    "a",
    "after",
    "and",
    "before",
    "for",
    "from",
    "in",
    "is",
    "of",
    "only",
    "the",
    "this",
    "to",
    "with",
}


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _TOKEN.findall(value) if token.lower() not in _STOP}


def _normalized(value: str) -> str:
    return " ".join(value.split())


class EvidenceVerifier:
    """Deterministic verifier. Provider citations are mappings, never final proof."""

    def __init__(self, policy: AuthorizationPolicy | None = None) -> None:
        self.policy = policy or AuthorizationPolicy()

    def verify(
        self,
        *,
        run_id: str,
        findings: FirstPassFindings,
        documents: tuple[UntrustedEvidenceDocument, ...],
        identity: IdentitySnapshot,
        corpus: Corpus,
    ) -> EvidenceGraph:
        document_by_id = {item.document_id: item for item in documents}
        citation_drafts = {item.citation_id: item for item in findings.citations}
        eligible = self.policy.eligible_chunk_ids(
            identity, corpus.versions, corpus.chunks, corpus.acls
        )
        current_versions = set(corpus.snapshot.artifact_version_ids)
        version_by_id = {item.artifact_version_id: item for item in corpus.versions}

        verified_citations: list[VerifiedCitation] = []
        verified_claims: list[VerifiedClaim] = []
        for claim in findings.claims:
            claim_citations: list[VerifiedCitation] = []
            for citation_id in claim.citation_ids:
                draft = citation_drafts[citation_id]
                document = document_by_id.get(draft.document_id)
                exists = document is not None
                authorized = bool(document and document.document_id in eligible)
                in_context = exists
                version_valid = bool(
                    document
                    and document.artifact_version_id in version_by_id
                    and document.artifact_version_id in current_versions
                )
                fresh = bool(version_valid or not claim.current_support_required)
                span_exact = bool(
                    document and _normalized(draft.exact_quote) in _normalized(document.content)
                )
                supports = bool(
                    span_exact and document and self._supports(claim, draft.exact_quote)
                )
                non_hostile = bool(document and not document.hostile and supports)
                checks = {
                    "citation_exists": exists,
                    "citation_authorized": authorized,
                    "citation_version_valid": version_valid,
                    "citation_fresh": fresh,
                    "citation_in_context": in_context,
                    "citation_span_exact": span_exact,
                    "citation_supports_claim": supports,
                }
                codes = tuple(name for name, passed in checks.items() if passed) + tuple(
                    f"{name}_failed" for name, passed in checks.items() if not passed
                )
                verified = VerifiedCitation(
                    citation_id=citation_id,
                    claim_id=claim.claim_id,
                    document_id=draft.document_id,
                    artifact_id=document.artifact_id if document else None,
                    artifact_version_id=document.artifact_version_id if document else None,
                    title=document.title if document else "Unavailable source",
                    version=document.version if document else "unknown",
                    locator=document.locator if document else "unknown",
                    excerpt=draft.exact_quote if document else "",
                    exists=exists,
                    authorized=authorized,
                    version_valid=version_valid,
                    fresh=fresh,
                    in_context=in_context,
                    span_exact=span_exact,
                    supports_claim=supports,
                    non_hostile_support=non_hostile,
                    verifier_codes=codes,
                )
                verified_citations.append(verified)
                claim_citations.append(verified)

            passing = [
                item
                for item in claim_citations
                if item.exists
                and item.authorized
                and item.version_valid
                and item.fresh
                and item.in_context
                and item.span_exact
                and item.supports_claim
            ]
            hostile_used = any(
                document_by_id[item.document_id].hostile
                for item in passing
                if item.document_id in document_by_id
            )
            has_independent_support = any(item.non_hostile_support for item in passing)
            if hostile_used and not has_independent_support:
                passing = []
            if len(passing) == len(claim_citations) and passing:
                status = SupportStatus.SUPPORTED
            elif passing:
                status = SupportStatus.PARTIALLY_SUPPORTED
            else:
                status = SupportStatus.UNSUPPORTED
            claim_codes = [f"claim_{status.value}"]
            if hostile_used and not has_independent_support:
                claim_codes.append("independent_non_hostile_support_required")
            verified_claims.append(
                VerifiedClaim(
                    **claim.model_dump(),
                    status=status,
                    verifier_codes=tuple(claim_codes),
                )
            )

        conflicts = self._conflicts(verified_claims)
        conflicted_ids = {claim_id for item in conflicts for claim_id in item.claim_ids}
        if conflicted_ids:
            verified_claims = [
                item.model_copy(
                    update={
                        "status": SupportStatus.CONFLICTED,
                        "verifier_codes": item.verifier_codes + ("deterministic_conflict",),
                    }
                )
                if item.claim_id in conflicted_ids
                else item
                for item in verified_claims
            ]

        routes = tuple(
            RouteCandidate(claim_id=item.claim_id, route=item.value, status=item.status)
            for item in verified_claims
            if item.kind is ClaimKind.ROUTE
            and item.status in {SupportStatus.SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
        )
        action_claims = tuple(
            item.claim_id
            for item in verified_claims
            if item.action_supporting and item.status is SupportStatus.SUPPORTED
        )
        blocked_action = any(
            item.action_supporting and item.status is not SupportStatus.SUPPORTED
            for item in verified_claims
        )
        proposals = (
            (PermittedProposal(supporting_claim_ids=action_claims),)
            if findings.requested_proposal == "create_jira_issue"
            and action_claims
            and not blocked_action
            else ()
        )
        body = {
            "graph_id": stable_id("graph", {"run_id": run_id, "findings": findings}),
            "run_id": run_id,
            "claims": tuple(verified_claims),
            "citations": tuple(verified_citations),
            "unknowns": findings.unknowns,
            "conflicts": conflicts,
            "route_candidates": routes,
            "permitted_proposals": proposals,
            "model_context_ids": tuple(sorted(document_by_id)),
        }
        return EvidenceGraph(**body, graph_hash=checksum(body))

    @staticmethod
    def _supports(claim: ClaimDraft, excerpt: str) -> bool:
        excerpt_tokens = _tokens(excerpt)
        value_tokens = _tokens(claim.value)
        if value_tokens and not value_tokens.issubset(excerpt_tokens):
            return False
        claim_tokens = _tokens(claim.text)
        if not claim_tokens:
            return False
        overlap = len(claim_tokens & excerpt_tokens)
        required = max(1, math.ceil(len(claim_tokens) * 0.45))
        return overlap >= required

    @staticmethod
    def _conflicts(claims: list[VerifiedClaim]) -> tuple[EvidenceConflict, ...]:
        grouped: dict[str, list[VerifiedClaim]] = defaultdict(list)
        for claim in claims:
            if claim.status in {SupportStatus.SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}:
                grouped[claim.subject].append(claim)
        conflicts: list[EvidenceConflict] = []
        for subject, items in grouped.items():
            values = tuple(sorted({item.value for item in items}))
            if len(values) < 2:
                continue
            body = {
                "subject": subject,
                "claims": tuple(item.claim_id for item in items),
                "values": values,
            }
            conflicts.append(
                EvidenceConflict(
                    conflict_id=stable_id("conflict", body),
                    subject=subject,
                    claim_ids=tuple(item.claim_id for item in items),
                    values=values,
                    description=f"Verified evidence disagrees about {subject}.",
                )
            )
        return tuple(conflicts)
