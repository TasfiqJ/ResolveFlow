from __future__ import annotations

from enum import Enum
from typing import Literal

from resolveflow.agent.findings import ClaimKind, UnknownDraft
from resolveflow.domain.base import FrozenModel


class SupportStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONFLICTED = "conflicted"


class VerifiedCitation(FrozenModel):
    citation_id: str
    claim_id: str
    document_id: str
    artifact_id: str | None
    artifact_version_id: str | None
    title: str
    version: str
    locator: str
    excerpt: str
    exists: bool
    authorized: bool
    version_valid: bool
    fresh: bool
    in_context: bool
    span_exact: bool
    supports_claim: bool
    non_hostile_support: bool
    verifier_codes: tuple[str, ...]


class VerifiedClaim(FrozenModel):
    claim_id: str
    kind: ClaimKind
    text: str
    subject: str
    value: str
    material: bool
    current_support_required: bool
    action_supporting: bool
    status: SupportStatus
    citation_ids: tuple[str, ...]
    verifier_codes: tuple[str, ...]


class EvidenceConflict(FrozenModel):
    conflict_id: str
    subject: str
    claim_ids: tuple[str, ...]
    values: tuple[str, ...]
    description: str


class RouteCandidate(FrozenModel):
    claim_id: str
    route: str
    status: SupportStatus


class PermittedProposal(FrozenModel):
    proposal_type: Literal["create_jira_issue"] = "create_jira_issue"
    state: Literal["inert_only"] = "inert_only"
    supporting_claim_ids: tuple[str, ...]


class EvidenceGraph(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    graph_id: str
    run_id: str
    claims: tuple[VerifiedClaim, ...]
    citations: tuple[VerifiedCitation, ...]
    unknowns: tuple[UnknownDraft, ...]
    conflicts: tuple[EvidenceConflict, ...]
    route_candidates: tuple[RouteCandidate, ...]
    permitted_proposals: tuple[PermittedProposal, ...]
    model_context_ids: tuple[str, ...]
    graph_hash: str
