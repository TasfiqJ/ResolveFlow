from __future__ import annotations

import json

from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.findings import FirstPassFindings
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
