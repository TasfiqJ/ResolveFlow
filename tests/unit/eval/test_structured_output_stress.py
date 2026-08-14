from resolveflow.eval.structured_output_stress import classify_response

SCHEMA = {
    "type": "object",
    "properties": {"field": {"type": "string"}},
    "required": ["field"],
}


def test_classifies_valid_and_required_field_failures() -> None:
    assert classify_response('{"field":"value"}', SCHEMA, "complete") == "valid"
    assert classify_response("{}", SCHEMA, "complete") == "missing_field"


def test_classifies_wrong_type_prose_refusal_and_truncation() -> None:
    assert classify_response('{"field":1}', SCHEMA, "complete") == "wrong_type"
    assert classify_response("plain response", SCHEMA, "complete") == "prose_instead_of_json"
    assert classify_response("I cannot comply", SCHEMA, "complete") == "refusal"
    assert classify_response('{"field":', SCHEMA, "max_tokens") == "truncation"
