from __future__ import annotations

import json
from pathlib import Path

from resolveflow.agent.contracts import UntrustedEvidenceDocument
from resolveflow.agent.security import detect_hostile_evidence
from resolveflow.domain.hashing import checksum


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
        "approval_bypass",
    }
    assert all(item["legitimate_fact"] for item in fixtures)
    assert all(item["expected_blocked_effects"] for item in fixtures)
    assert payload["provenance"]["type"] == "synthetic_agent_authored"


def test_every_attack_payload_exercises_its_expected_deterministic_controls() -> None:
    payload = json.loads(
        Path("data/security/prompt-injection-fixtures.json").read_text(encoding="utf-8")
    )

    for item in payload["fixtures"]:
        document = UntrustedEvidenceDocument(
            document_id=item["fixture_id"],
            artifact_id=item["fixture_id"],
            artifact_version_id=f"{item['fixture_id']}_v1",
            title=f"Synthetic attack fixture {item['family']}",
            version="1",
            locator="security-fixture",
            content=item["content"],
            content_checksum=checksum(item["content"]),
            hostile=True,
        )
        observed = {event.effect.value for event in detect_hostile_evidence((document,))}
        assert set(item["expected_blocked_effects"]) <= observed
