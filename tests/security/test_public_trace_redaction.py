from __future__ import annotations

import json

from resolveflow.telemetry.projection import public_projection, public_projection_checksum


def test_public_projection_deterministically_removes_sensitive_material() -> None:
    source = {
        "run_id": "run_safe",
        "authorization": "Bearer very-secret-value-12345",
        "hidden_prompt": "never expose this",
        "private_path": "/home/operator/private/config.json",
        "detail": {"classification": "restricted", "title": "Legal strategy"},
        "safe": "PYM-431",
    }
    projected = public_projection(source)
    encoded = json.dumps(projected, sort_keys=True)
    assert "very-secret" not in encoded
    assert "never expose" not in encoded
    assert "/home/operator" not in encoded
    assert "Legal strategy" not in encoded
    assert "PYM-431" in encoded
    assert public_projection_checksum(source) == public_projection_checksum(source)
