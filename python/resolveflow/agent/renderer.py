from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.models import Citation, FinalResponse
from resolveflow.verifier.models import EvidenceGraph, SupportStatus


class StructureSelection(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    disposition: Literal["resolved", "needs_review", "abstained"]
    route_claim_id: str | None
    summary_claim_ids: tuple[str, ...]
    recommended_step_claim_ids: tuple[str, ...]
    unknown_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    graph_hash: str
    needs_review: bool

    @model_validator(mode="after")
    def disposition_matches_review_flag(self) -> StructureSelection:
        if self.disposition == "resolved" and self.needs_review:
            raise ValueError("resolved responses cannot require review")
        if self.disposition != "resolved" and not self.needs_review:
            raise ValueError("non-resolved responses require review")
        return self


class DeterministicRenderer:
    def render(
        self,
        graph: EvidenceGraph,
        selection: StructureSelection,
        *,
        provider: Literal["recorded_fixture", "cohere"],
    ) -> FinalResponse:
        self.validate_selection(graph, selection)
        claim_by_id = {item.claim_id: item for item in graph.claims}
        unknown_by_id = {item.unknown_id: item for item in graph.unknowns}
        conflict_by_id = {item.conflict_id: item for item in graph.conflicts}
        selected_ids = tuple(
            dict.fromkeys(
                ([selection.route_claim_id] if selection.route_claim_id else [])
                + list(selection.summary_claim_ids)
                + list(selection.recommended_step_claim_ids)
            )
        )
        selected_claims = tuple(claim_by_id[item] for item in selected_ids)
        selected_citation_ids = {
            citation_id for item in selected_claims for citation_id in item.citation_ids
        }
        citations = tuple(
            Citation(
                citation_id=item.citation_id,
                source_id=item.document_id,
                title=item.title,
                version=item.version,
                locator=item.locator,
                excerpt=item.excerpt,
                claim_id=item.claim_id,
                verifier_codes=item.verifier_codes,
            )
            for item in graph.citations
            if item.citation_id in selected_citation_ids and item.supports_claim
        )
        facts = tuple(claim_by_id[item].text for item in selection.summary_claim_ids)
        summary = (
            " ".join(facts) if facts else "Verified evidence is insufficient for a resolution."
        )
        return FinalResponse(
            status="verified" if selection.disposition == "resolved" else selection.disposition,
            disposition=selection.disposition,
            route=(
                claim_by_id[selection.route_claim_id].value if selection.route_claim_id else None
            ),
            summary=summary,
            recommended_steps=tuple(
                claim_by_id[item].text for item in selection.recommended_step_claim_ids
            ),
            verified_facts=facts,
            unknowns=tuple(unknown_by_id[item].text for item in selection.unknown_ids),
            conflicts=tuple(conflict_by_id[item].description for item in selection.conflict_ids),
            citations=citations,
            claim_ids=selected_ids,
            graph_hash=graph.graph_hash,
            provider=provider,
            verifier_status="verified" if selection.disposition == "resolved" else "needs_review",
            needs_review=selection.needs_review,
        )

    @staticmethod
    def validate_selection(graph: EvidenceGraph, selection: StructureSelection) -> None:
        if selection.graph_hash != graph.graph_hash:
            raise ValueError("structure graph hash mismatch")
        claims = {item.claim_id: item for item in graph.claims}
        requested_claims = set(selection.summary_claim_ids) | set(
            selection.recommended_step_claim_ids
        )
        if selection.route_claim_id:
            requested_claims.add(selection.route_claim_id)
        if not requested_claims.issubset(claims):
            raise ValueError("structure selected an unknown claim")
        if any(claims[item].status is not SupportStatus.SUPPORTED for item in requested_claims):
            raise ValueError("structure selected a claim that is not fully verified")
        if selection.route_claim_id and claims[selection.route_claim_id].kind.value != "route":
            raise ValueError("route field must select a route claim")
        if not set(selection.unknown_ids).issubset({item.unknown_id for item in graph.unknowns}):
            raise ValueError("structure selected an unknown unknown")
        if not set(selection.conflict_ids).issubset({item.conflict_id for item in graph.conflicts}):
            raise ValueError("structure selected an unknown conflict")

    def fallback(
        self,
        graph: EvidenceGraph,
        *,
        provider: Literal["recorded_fixture", "cohere"],
    ) -> FinalResponse:
        supported_facts = tuple(
            item
            for item in graph.claims
            if item.status is SupportStatus.SUPPORTED and item.kind.value == "fact"
        )
        selection = StructureSelection(
            disposition="needs_review",
            route_claim_id=None,
            summary_claim_ids=tuple(item.claim_id for item in supported_facts),
            recommended_step_claim_ids=(),
            unknown_ids=tuple(item.unknown_id for item in graph.unknowns),
            conflict_ids=tuple(item.conflict_id for item in graph.conflicts),
            graph_hash=graph.graph_hash,
            needs_review=True,
        )
        return self.render(graph, selection, provider=provider)
