"""Structural and cryptographic integrity checks for retained run snapshots.

Run snapshots are content-addressed envelopes, but publication and recovery must
also validate the hashes and references nested inside that envelope.  Keeping the
checks here gives the live/public hero verifier and the A/B artifact pipeline one
definition of evidence closure.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from resolveflow.agent.contracts import ProviderTrace, ToolTrace
from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.verifier.models import EvidenceGraph, VerifiedCitation

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOOL_AUTHORITIES = {
    "lookup_customer_context": "read_only",
    "query_rollout_record": "read_only",
    "query_prior_incident": "read_only",
    "propose_jira_issue": "inert_proposal",
}
_SOURCE_FIELDS = (
    "source_status",
    "freshness",
    "source_operation",
    "source_as_of",
    "source_version",
    "source_checksum",
)


def _validate_tool_trace(trace: ToolTrace) -> None:
    """Reject impossible tool/authorization combinations, including legacy traces."""

    if not _SHA256_RE.fullmatch(trace.arguments_hash):
        raise ValueError("tool trace arguments hash is invalid")
    if trace.source_checksum is not None and not _SHA256_RE.fullmatch(trace.source_checksum):
        raise ValueError("tool trace source checksum is invalid")

    expected_authority = _TOOL_AUTHORITIES.get(trace.name)
    source_values = tuple(getattr(trace, field) for field in _SOURCE_FIELDS)
    has_source_metadata = any(value is not None for value in source_values)

    if expected_authority is None:
        if not (
            trace.status == "rejected"
            and trace.authorization == "not_evaluated"
            and trace.authority is None
            and trace.safe_error_code == "tool_not_allowlisted"
            and not trace.provenance_ids
            and not has_source_metadata
        ):
            raise ValueError("unknown tool trace is not a fail-closed rejection")
        return

    if trace.authority is not None and trace.authority != expected_authority:
        raise ValueError("tool trace authority does not match the allowlisted tool")

    if trace.status == "ok":
        if trace.authorization != "allowed" or trace.safe_error_code is not None:
            raise ValueError("successful tool trace has inconsistent authorization state")
        if not trace.provenance_ids or any(not item.strip() for item in trace.provenance_ids):
            raise ValueError("successful tool trace has no usable provenance")
        if len(set(trace.provenance_ids)) != len(trace.provenance_ids):
            raise ValueError("successful tool trace has duplicate provenance IDs")

        if trace.authority is None:
            # Historical A/B evidence predates the authority/source extension.
            # The original allowlisted name, authorization decision, argument
            # hash, and provenance remain available and are validated above.
            if has_source_metadata:
                raise ValueError("legacy tool trace carries a partial source envelope")
            return

        if expected_authority == "read_only":
            if any(value is None for value in source_values):
                raise ValueError("successful read trace has an incomplete source envelope")
            if trace.freshness != "run_context" or trace.source_version != "context-result/1.0":
                raise ValueError("successful read trace has invalid freshness/version metadata")
        elif has_source_metadata:
            raise ValueError("inert proposal trace must not claim read-source provenance")
        return

    if trace.status == "rejected":
        if (
            trace.authorization not in {"denied", "not_evaluated"}
            or not trace.safe_error_code
            or trace.provenance_ids
            or has_source_metadata
        ):
            raise ValueError("rejected tool trace has inconsistent fail-closed state")
        return

    if (
        trace.authorization != "allowed"
        or not trace.safe_error_code
        or trace.provenance_ids
        or has_source_metadata
    ):
        raise ValueError("failed tool trace has inconsistent execution state")


def _citation_projection(citation: VerifiedCitation) -> dict[str, Any]:
    return {
        "citation_id": citation.citation_id,
        "source_id": citation.document_id,
        "title": citation.title,
        "version": citation.version,
        "locator": citation.locator,
        "excerpt": citation.excerpt,
        "claim_id": citation.claim_id,
        "verifier_codes": citation.verifier_codes,
    }


def validate_snapshot_evidence(
    snapshot: RunSnapshot,
    payload: dict[str, Any],
    *,
    allow_legacy_graph_hash: bool = False,
) -> EvidenceGraph:
    """Validate nested evidence, tool, and audit closure for one snapshot.

    ``payload`` is required because historical hashes were computed from the
    serialized JSON representation.  Re-dumping a typed model can normalize
    values and would validate a representation different from the published
    bytes.
    """

    raw_graph = payload.get("evidence_graph")
    if not isinstance(raw_graph, dict):
        raise ValueError("snapshot evidence graph is not an object")
    try:
        graph = EvidenceGraph.model_validate(raw_graph)
    except ValidationError as exc:
        raise ValueError("snapshot evidence graph schema is invalid") from exc
    if not _SHA256_RE.fullmatch(graph.graph_hash):
        raise ValueError("snapshot evidence graph hash is invalid")

    graph_body = {key: value for key, value in raw_graph.items() if key != "graph_hash"}
    expected_graph_hash = checksum(graph_body)
    # The retained A/B and first live-hero cohorts were created immediately
    # before graph schema_version became an explicit hash input.  Omitting that
    # one constant is the only accepted compatibility form; RunSnapshot's outer
    # content hash still binds the serialized schema_version field.
    legacy_graph_hash = checksum(
        {key: value for key, value in graph_body.items() if key != "schema_version"}
    )
    if graph.graph_hash != expected_graph_hash and not (
        allow_legacy_graph_hash
        and raw_graph.get("schema_version") == "1.0"
        and graph.graph_hash == legacy_graph_hash
    ):
        raise ValueError("snapshot evidence graph hash is invalid")
    if graph.run_id != snapshot.run_id:
        raise ValueError("snapshot evidence graph is bound to a different run")
    if snapshot.response.graph_hash != graph.graph_hash:
        raise ValueError("snapshot response is not bound to its evidence graph")

    graph_claims = {claim.claim_id: claim for claim in graph.claims}
    if any(
        claim_id not in graph_claims or graph_claims[claim_id].status.value != "supported"
        for claim_id in snapshot.response.claim_ids
    ):
        raise ValueError("snapshot response selects an unsupported or unknown claim")
    citation_projections = [_citation_projection(citation) for citation in graph.citations]
    for citation in snapshot.response.citations:
        if citation.model_dump(mode="python") not in citation_projections:
            raise ValueError("snapshot response citation is not present in its evidence graph")
    if snapshot.response.route is not None and not any(
        candidate.route == snapshot.response.route
        and candidate.claim_id in snapshot.response.claim_ids
        for candidate in graph.route_candidates
    ):
        raise ValueError("snapshot response route is not selected from its evidence graph")

    provider_ids: set[str] = set()
    for raw_trace in snapshot.provider_traces:
        provider_trace = ProviderTrace.model_validate(raw_trace)
        if provider_trace.provider_call_id in provider_ids:
            raise ValueError("snapshot contains duplicate provider-call IDs")
        provider_ids.add(provider_trace.provider_call_id)

    tool_call_ids: set[str] = set()
    for raw_trace in snapshot.tool_traces:
        tool_trace = ToolTrace.model_validate(raw_trace)
        if tool_trace.tool_call_id in tool_call_ids:
            raise ValueError("snapshot contains duplicate tool-call IDs")
        tool_call_ids.add(tool_trace.tool_call_id)
        _validate_tool_trace(tool_trace)

    raw_events = payload.get("trace")
    if not isinstance(raw_events, list) or len(raw_events) != len(snapshot.trace):
        raise ValueError("snapshot audit event envelope is invalid")
    if not raw_events:
        raise ValueError("snapshot audit chain is empty")
    previous_hash: str | None = None
    event_ids: set[str] = set()
    for index, (event, raw_event) in enumerate(zip(snapshot.trace, raw_events, strict=True), 1):
        if not isinstance(raw_event, dict):
            raise ValueError("snapshot audit event is not an object")
        if event.sequence != index:
            raise ValueError("snapshot audit event sequence is not contiguous")
        if event.event_id in event_ids:
            raise ValueError("snapshot audit event IDs are not unique")
        event_ids.add(event.event_id)
        if event.correlation_id != snapshot.run_id:
            raise ValueError("snapshot audit event is bound to a different run")
        if event.versions.get("build") != snapshot.build_id:
            raise ValueError("snapshot audit event is bound to a different build")
        if event.previous_event_hash != previous_hash:
            raise ValueError("snapshot audit chain link is invalid")
        if not _SHA256_RE.fullmatch(event.event_hash):
            raise ValueError("snapshot audit event hash is invalid")
        expected_event_hash = checksum(
            {
                key: value
                for key, value in raw_event.items()
                if key not in {"event_id", "event_hash"}
            }
        )
        if event.event_hash != expected_event_hash:
            raise ValueError("snapshot audit event hash is invalid")
        previous_hash = event.event_hash

    return graph
