from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel


class ClaimKind(str, Enum):
    FACT = "fact"
    ROUTE = "route"
    RECOMMENDATION = "recommendation"
    ACTION = "action"


class CitationDraft(FrozenModel):
    citation_id: str
    document_id: str
    exact_quote: str = Field(min_length=1)


class ClaimDraft(FrozenModel):
    claim_id: str
    kind: ClaimKind
    text: str = Field(min_length=1, max_length=500)
    subject: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=200)
    material: bool = True
    current_support_required: bool = False
    action_supporting: bool = False
    citation_ids: tuple[str, ...]

    @model_validator(mode="after")
    def material_claim_has_citation(self) -> ClaimDraft:
        if self.material and not self.citation_ids:
            raise ValueError("material claims require at least one citation mapping")
        return self


class UnknownDraft(FrozenModel):
    unknown_id: str
    field: str
    text: str
    reason_code: str


class FirstPassFindings(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    claims: tuple[ClaimDraft, ...]
    citations: tuple[CitationDraft, ...]
    unknowns: tuple[UnknownDraft, ...]
    requested_proposal: Literal["none", "create_jira_issue"] = "none"

    @model_validator(mode="after")
    def references_are_closed(self) -> FirstPassFindings:
        citation_ids = {item.citation_id for item in self.citations}
        if len(citation_ids) != len(self.citations):
            raise ValueError("duplicate citation IDs")
        claim_ids = {item.claim_id for item in self.claims}
        if len(claim_ids) != len(self.claims):
            raise ValueError("duplicate claim IDs")
        for claim in self.claims:
            if not set(claim.citation_ids).issubset(citation_ids):
                raise ValueError("claim references an unknown citation")
        return self
