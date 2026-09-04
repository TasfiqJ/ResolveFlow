from __future__ import annotations

import json

import pytest
from pydantic import ValidationError
from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.findings import CitationDraft, ClaimDraft, FirstPassFindings, UnknownDraft
from resolveflow.agent.service import GovernedAgent

_VALID = json.dumps({"claims": [], "citations": [], "unknowns": []}, sort_keys=True)


def test_fenced_findings_survive_crlf_and_a_padded_info_string() -> None:
    """A strict equality check on the opening fence line rejected well-formed bodies.

    Requiring the line to be exactly ``` or ```json meant a carriage return or a
    trailing space raised "unsupported findings fence", stamping the trace malformed
    and burning a whole repair provider call on a valid response.
    """
    for opening in ("```json", "```JSON", "```", "```json ", "```\t"):
        for newline in ("\n", "\r\n"):
            text = f"{opening}{newline}{_VALID}{newline}```"
            parsed = GovernedAgent._parse_findings(text)
            assert isinstance(parsed, FirstPassFindings)


def test_unfenced_and_plain_json_still_parse() -> None:
    assert isinstance(GovernedAgent._parse_findings(_VALID), FirstPassFindings)
    assert isinstance(GovernedAgent._parse_findings(f"  {_VALID}  "), FirstPassFindings)


def test_strict_schema_drops_keywords_but_never_property_names() -> None:
    """The projection walked every dict, so a field NAMED like a keyword vanished.

    Dropping e.g. a property called "pattern" from `properties` while leaving it in
    `required` produces a schema the provider rejects outright.
    """
    schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "minLength": 1},
            "maximum": {"type": "integer", "maximum": 10},
            "rollout_id": {"type": "string", "pattern": r"^[a-z0-9-]+$"},
        },
        "required": ["pattern", "maximum", "rollout_id"],
        "$defs": {"minItems": {"type": "string", "minLength": 2}},
    }

    projected = CohereChatAdapter._strict_schema(schema)

    assert set(projected["properties"]) == {"pattern", "maximum", "rollout_id"}
    assert set(projected["$defs"]) == {"minItems"}
    # ...while the unsupported keywords inside those subschemas are still removed.
    assert projected["properties"]["pattern"] == {"type": "string"}
    assert projected["properties"]["maximum"] == {"type": "integer"}
    assert projected["properties"]["rollout_id"] == {"type": "string"}
    assert projected["$defs"]["minItems"] == {"type": "string"}
    assert projected["required"] == ["pattern", "maximum", "rollout_id"]


def test_strict_schema_preserves_refs() -> None:
    schema = FirstPassFindings.model_json_schema()
    projected = CohereChatAdapter._strict_schema(schema)
    assert set(schema.get("$defs", {})) == set(projected.get("$defs", {}))


def test_findings_parser_drops_invalid_sibling_claim_without_rewriting_valid_claim() -> None:
    payload = {
        "schema_version": "1.0",
        "citations": [
            {
                "citation_id": "cite_valid",
                "document_id": "chunk_valid",
                "exact_quote": "issuer-routing-v3 completed",
            }
        ],
        "claims": [
            {
                "claim_id": "claim_valid",
                "kind": "fact",
                "text": "issuer-routing-v3 completed",
                "subject": "rollout",
                "value": "completed",
                "citation_ids": ["cite_valid"],
            },
            {
                "claim_id": "claim_invalid_route",
                "kind": "route",
                "text": "Route to Payments Platform",
                "subject": "route",
                "value": "Payments Platform",
                "citation_ids": [],
            },
        ],
        "unknowns": [],
        "requested_proposal": "none",
    }

    findings = GovernedAgent._parse_findings(json.dumps(payload))

    assert [item.claim_id for item in findings.claims] == ["claim_valid"]
    assert findings.claims[0].text == "issuer-routing-v3 completed"


@pytest.mark.parametrize("bad_collection", [None, {}, "not-a-list", 7])
@pytest.mark.parametrize("field", ["claims", "citations", "unknowns"])
def test_findings_salvage_normalizes_non_list_collections_to_safe_failure(
    field: str, bad_collection: object
) -> None:
    payload: dict[str, object] = {
        "claims": [],
        "citations": [],
        "unknowns": [],
        field: bad_collection,
    }

    with pytest.raises(ValueError, match="no valid claims or unknowns"):
        GovernedAgent._salvage_findings(payload)


def test_findings_reject_duplicate_unknown_ids() -> None:
    unknown = UnknownDraft(unknown_id="u1", field="route", text="Unknown", reason_code="missing")

    with pytest.raises(ValidationError, match="duplicate unknown IDs"):
        FirstPassFindings(claims=(), citations=(), unknowns=(unknown, unknown))


def test_findings_reject_duplicate_citation_ids_within_one_claim() -> None:
    citation = CitationDraft(citation_id="c1", document_id="doc-1", exact_quote="supported")
    claim = ClaimDraft(
        claim_id="claim-1",
        kind="fact",
        text="supported",
        subject="status",
        value="supported",
        citation_ids=("c1", "c1"),
    )

    with pytest.raises(ValidationError, match="duplicate citation IDs within a claim"):
        FirstPassFindings(claims=(claim,), citations=(citation,), unknowns=())


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": "2.0"},
        {"schema_version": "1.0", "unrecognized_authority": True},
    ],
)
def test_findings_salvage_rejects_unknown_envelope_contracts(
    mutation: dict[str, object],
) -> None:
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "claims": [],
        "citations": [],
        "unknowns": [
            {
                "unknown_id": "u1",
                "field": "route",
                "text": "Route is unknown",
                "reason_code": "context_not_found",
            }
        ],
        **mutation,
    }

    with pytest.raises(ValueError, match="schema version|unknown top-level"):
        GovernedAgent._parse_findings(json.dumps(payload))
