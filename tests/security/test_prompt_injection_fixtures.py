from __future__ import annotations

import json
from pathlib import Path


def test_prompt_injection_fixture_library_covers_declared_families_and_effects() -> None:
    payload = json.loads(
        Path("data/security/prompt-injection-fixtures.json").read_text(encoding="utf-8")
    )
    fixtures = payload["fixtures"]
    assert {item["family"] for item in fixtures} == {
        "visible_instruction",
        "delimiter_like",
        "multilingual_instruction",
        "fake_system_message",
        "action_bypass",
    }
    assert all(item["legitimate_fact"] for item in fixtures)
    assert all(item["expected_blocked_effects"] for item in fixtures)
    assert payload["provenance"]["type"] == "synthetic_agent_authored"
