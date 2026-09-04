from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime

from resolveflow.agent.contracts import (
    EvidenceDocument,
    ToolResultEvidenceDocument,
    ToolTrace,
    UntrustedEvidenceDocument,
)
from resolveflow.agent.findings import ClaimDraft, ClaimKind, FirstPassFindings
from resolveflow.agent.security import ATTACK_PATTERNS
from resolveflow.domain.evidence import Corpus, IdentitySnapshot, stable_id
from resolveflow.domain.hashing import canonical_json, checksum
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
_NEGATIVE_POLARITY_TOKENS = {
    "denied",
    "failed",
    "failure",
    "failures",
    "incomplete",
    "never",
    "no",
    "not",
    "rejected",
}
_TOOL_CONTEXT_OPERATIONS = {
    "lookup_customer_context": "get_customer_profile",
    "query_rollout_record": "get_rollouts",
    "query_prior_incident": "get_open_incidents",
}
_TOOL_SUPPORT_FIELDS = {
    "lookup_customer_context": frozenset({"customer_id", "tier", "region"}),
    "query_rollout_record": frozenset({"rollout_id", "service", "change", "status"}),
    "query_prior_incident": frozenset({"incident_id", "matching_error"}),
}


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _TOKEN.findall(value) if token.lower() not in _STOP}


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _polarity_compatible(claim: str, excerpt: str) -> bool:
    """Reject evidence that only matches after dropping a negative qualifier.

    The verifier deliberately supports structured and CSV evidence, where a
    natural-language claim cannot always be a contiguous source substring. The
    polarity check keeps that field-aware support from accepting `complete`
    from `not complete` or `succeeded` from `failed before it succeeded`.
    """

    claim_tokens = {token.casefold() for token in _TOKEN.findall(claim)}
    excerpt_tokens = {token.casefold() for token in _TOKEN.findall(excerpt)}
    return not (
        (excerpt_tokens & _NEGATIVE_POLARITY_TOKENS) - (claim_tokens & _NEGATIVE_POLARITY_TOKENS)
    )


def _is_timezone_aware(value: object) -> bool:
    return (
        isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    )


def _valid_provenance_ids(value: object) -> bool:
    return bool(
        isinstance(value, tuple)
        and value
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(set(value)) == len(value)
    )


def _tool_support_content(tool_name: str, content_payload: object) -> str | None:
    """Project untrusted connector data onto a fixed, fact-only evidence surface."""

    if not isinstance(content_payload, dict):
        return None
    result_data = content_payload.get("data")
    if not isinstance(result_data, dict) or set(result_data) != {"status", "data"}:
        return None
    source_data = result_data.get("data")
    allowed_fields = _TOOL_SUPPORT_FIELDS.get(tool_name)
    if not isinstance(source_data, dict) or allowed_fields is None:
        return None
    projection = {key: source_data[key] for key in sorted(allowed_fields) if key in source_data}
    return canonical_json(projection) if projection else None


class EvidenceVerifier:
    """Deterministic verifier. Provider citations are mappings, never final proof."""

    def __init__(self, policy: AuthorizationPolicy | None = None) -> None:
        self.policy = policy or AuthorizationPolicy()

    def verify(
        self,
        *,
        run_id: str,
        findings: FirstPassFindings,
        documents: tuple[EvidenceDocument, ...],
        identity: IdentitySnapshot,
        corpus: Corpus,
        tool_traces: tuple[ToolTrace, ...] = (),
    ) -> EvidenceGraph:
        document_id_counts: dict[str, int] = defaultdict(int)
        for document_item in documents:
            document_id_counts[document_item.document_id] += 1
        document_by_id = {document_item.document_id: document_item for document_item in documents}
        tool_trace_counts: dict[str, int] = defaultdict(int)
        for trace_item in tool_traces:
            tool_trace_counts[trace_item.tool_call_id] += 1
        tool_trace_by_id = {trace_item.tool_call_id: trace_item for trace_item in tool_traces}
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
                exists = bool(document is not None and document_id_counts[draft.document_id] == 1)
                source_checks: dict[str, bool] = {}
                tool_support_content: str | None = None
                if isinstance(document, ToolResultEvidenceDocument):
                    trace = tool_trace_by_id.get(document.tool_call_id)
                    trace_unique = tool_trace_counts[document.tool_call_id] == 1
                    try:
                        content_payload = json.loads(document.content)
                    except (json.JSONDecodeError, TypeError):
                        content_payload = None
                    document_timestamp_valid = _is_timezone_aware(document.source_as_of)
                    identity_timestamp_valid = _is_timezone_aware(identity.case_time)
                    provenance_valid = _valid_provenance_ids(document.provenance_ids)
                    result_data = (
                        content_payload.get("data") if isinstance(content_payload, dict) else None
                    )
                    source_data = result_data.get("data") if isinstance(result_data, dict) else None
                    serialized_source_as_of = (
                        json.loads(canonical_json(document.source_as_of))
                        if document_timestamp_valid
                        else None
                    )
                    payload_provenance = (
                        content_payload.get("provenance_ids")
                        if isinstance(content_payload, dict)
                        else None
                    )
                    source_body = (
                        {
                            "operation": document.source_operation,
                            "status": document.source_status,
                            "as_of": document.source_as_of,
                            "provenance_ids": document.provenance_ids,
                            "data": source_data,
                        }
                        if document_timestamp_valid and isinstance(source_data, dict)
                        else None
                    )
                    source_checksum_recomputed = bool(
                        source_body is not None
                        and isinstance(document.source_checksum, str)
                        and document.source_checksum == checksum(source_body)
                    )
                    source_operation_valid = bool(
                        document.source_operation
                        == _TOOL_CONTEXT_OPERATIONS.get(document.tool_name)
                    )
                    instruction_safe = not any(
                        pattern.search(document.content) for _, pattern in ATTACK_PATTERNS
                    )
                    content_binding_valid = bool(
                        isinstance(content_payload, dict)
                        and canonical_json(content_payload) == document.content
                        and content_payload.get("tool_call_id") == document.tool_call_id
                        and content_payload.get("name") == document.tool_name
                        and content_payload.get("status") == "ok"
                        and content_payload.get("authority") == "read_only"
                        and content_payload.get("authorization") == "allowed"
                        and content_payload.get("source_status") == "ok"
                        and content_payload.get("freshness") == document.freshness
                        and content_payload.get("source_operation") == document.source_operation
                        and content_payload.get("source_version") == document.source_version
                        and content_payload.get("source_checksum") == document.source_checksum
                        and content_payload.get("source_as_of") == serialized_source_as_of
                        and isinstance(payload_provenance, list)
                        and tuple(payload_provenance) == document.provenance_ids
                        and isinstance(result_data, dict)
                        and set(result_data) == {"status", "data"}
                        and result_data.get("status") == document.source_status
                    )
                    identity_valid = (
                        document.document_id == f"tool-result:{document.tool_call_id}"
                        and document.content_checksum == checksum(document.content)
                        and content_binding_valid
                    )
                    trace_valid = bool(
                        trace_unique
                        and trace is not None
                        and trace.tool_call_id == document.tool_call_id
                        and trace.name == document.tool_name
                        and trace.status == "ok"
                        and trace.authorization == "allowed"
                        and trace.authority == "read_only"
                        and trace.provenance_ids == document.provenance_ids
                        and trace.source_status == document.source_status == "ok"
                        and trace.freshness == document.freshness == "run_context"
                        and trace.source_operation == document.source_operation
                        and trace.source_as_of == document.source_as_of
                        and trace.source_version == document.source_version
                        and trace.source_checksum == document.source_checksum
                        and _is_timezone_aware(trace.source_as_of)
                    )
                    source_checksum_valid = bool(
                        isinstance(document.source_checksum, str)
                        and re.fullmatch(r"sha256:[0-9a-f]{64}", document.source_checksum)
                        and source_checksum_recomputed
                    )
                    authorized = bool(exists and trace_valid and instruction_safe)
                    version_valid = bool(
                        exists
                        and identity_valid
                        and source_checksum_valid
                        and source_operation_valid
                        and provenance_valid
                        and document.source_version == "context-result/1.0"
                    )
                    source_fresh = bool(
                        document.freshness == "run_context"
                        and document_timestamp_valid
                        and identity_timestamp_valid
                        and document.source_as_of >= identity.case_time
                        and trace is not None
                        and trace.freshness == document.freshness
                        and trace.source_as_of == document.source_as_of
                    )
                    tool_support_content = _tool_support_content(
                        document.tool_name, content_payload
                    )
                    source_checks = {
                        "tool_result_identity_valid": identity_valid,
                        "tool_result_content_binding_valid": content_binding_valid,
                        "tool_execution_trace_valid": trace_valid,
                        "tool_source_checksum_valid": source_checksum_valid,
                        "tool_source_checksum_recomputed": source_checksum_recomputed,
                        "tool_source_operation_valid": source_operation_valid,
                        "tool_source_provenance_valid": provenance_valid,
                        "tool_source_timestamp_valid": document_timestamp_valid,
                        "tool_source_fresh": source_fresh,
                        "tool_result_instruction_safe": instruction_safe,
                        "tool_result_claim_kind_allowed": (
                            claim.kind is ClaimKind.FACT and not claim.action_supporting
                        ),
                        "tool_result_action_support_allowed": not claim.action_supporting,
                        "source_kind_tool_result": True,
                    }
                else:
                    authorized = bool(document and document.document_id in eligible)
                    version_valid = bool(
                        document
                        and document.artifact_version_id in version_by_id
                        and document.artifact_version_id in current_versions
                    )
                    source_fresh = version_valid
                    source_checks = {"source_kind_retrieval_chunk": document is not None}
                in_context = exists
                fresh = bool(source_fresh or not claim.current_support_required)
                span_exact = bool(
                    document and _normalized(draft.exact_quote) in _normalized(document.content)
                )
                if isinstance(document, ToolResultEvidenceDocument):
                    quote_is_allowlisted = bool(
                        tool_support_content
                        and _normalized(draft.exact_quote) in _normalized(tool_support_content)
                    )
                    span_exact = span_exact and quote_is_allowlisted
                    source_checks["tool_result_quote_allowlisted"] = quote_is_allowlisted
                claim_kind_invariant = claim.action_supporting == (claim.kind is ClaimKind.ACTION)
                semantic_support = bool(
                    draft.exact_quote
                    and (
                        self._supports_tool_fact(claim, draft.exact_quote)
                        if isinstance(document, ToolResultEvidenceDocument)
                        else self._supports(claim, draft.exact_quote)
                    )
                )
                supports = bool(
                    span_exact
                    and document
                    and semantic_support
                    and claim_kind_invariant
                    and not (
                        isinstance(document, ToolResultEvidenceDocument)
                        and (claim.kind is not ClaimKind.FACT or claim.action_supporting)
                    )
                )
                non_hostile = bool(
                    isinstance(document, UntrustedEvidenceDocument)
                    and not document.hostile
                    and supports
                )
                checks = {
                    "citation_exists": exists,
                    "citation_authorized": authorized,
                    "citation_version_valid": version_valid,
                    "citation_fresh": fresh,
                    "citation_in_context": in_context,
                    "citation_span_exact": span_exact,
                    "citation_supports_claim": supports,
                    "claim_action_kind_invariant": claim_kind_invariant,
                    **source_checks,
                }
                codes = tuple(name for name, passed in checks.items() if passed) + tuple(
                    f"{name}_failed" for name, passed in checks.items() if not passed
                )
                verified = VerifiedCitation(
                    citation_id=citation_id,
                    claim_id=claim.claim_id,
                    document_id=draft.document_id,
                    artifact_id=(
                        document.artifact_id
                        if isinstance(document, UntrustedEvidenceDocument)
                        else None
                    ),
                    artifact_version_id=(
                        document.artifact_version_id
                        if isinstance(document, UntrustedEvidenceDocument)
                        else None
                    ),
                    title=document.title if document else "Unavailable source",
                    version=(
                        document.version
                        if isinstance(document, UntrustedEvidenceDocument)
                        else document.source_version
                        if isinstance(document, ToolResultEvidenceDocument)
                        else "unknown"
                    ),
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
                isinstance(document_by_id[item.document_id], UntrustedEvidenceDocument)
                and document_by_id[item.document_id].hostile
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
            if item.kind is ClaimKind.ACTION
            and item.action_supporting
            and item.status is SupportStatus.SUPPORTED
        )
        blocked_action = any(
            (item.kind is ClaimKind.ACTION or item.action_supporting)
            and (
                item.kind is not ClaimKind.ACTION
                or not item.action_supporting
                or item.status is not SupportStatus.SUPPORTED
            )
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
            "schema_version": "1.0",
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
        normalized_excerpt = _normalized(excerpt).casefold()
        normalized_value = _normalized(claim.value).casefold()
        claim_tokens = _tokens(claim.text)
        excerpt_tokens = _tokens(excerpt)
        # Values must be contiguous, while the claim words may bind to a
        # structured/CSV excerpt in a different order. Polarity is checked
        # independently so token overlap cannot turn "not complete" into
        # "complete".
        if not claim_tokens or not normalized_value or normalized_value not in normalized_excerpt:
            return False
        overlap = len(claim_tokens & excerpt_tokens)
        required = max(1, math.ceil(len(claim_tokens) * 0.45))
        return overlap >= required and _polarity_compatible(claim.text, excerpt)

    @staticmethod
    def _supports_tool_fact(claim: ClaimDraft, exact_quote: str) -> bool:
        """Require every material claim token to occur in the exact cited tool quote."""

        quote_tokens = _tokens(exact_quote)
        value_tokens = _tokens(claim.value)
        claim_tokens = _tokens(claim.text)
        return bool(
            value_tokens
            and claim_tokens
            and value_tokens.issubset(quote_tokens)
            and claim_tokens.issubset(quote_tokens)
            and _polarity_compatible(claim.text, exact_quote)
        )

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
