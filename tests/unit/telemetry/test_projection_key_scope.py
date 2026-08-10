from __future__ import annotations

from resolveflow.telemetry.projection import public_projection


def test_audit_signal_keys_survive_the_public_projection() -> None:
    """Substring key matching used to redact the fields the artifact exists to publish.

    `authorization` matched `authorization_mode` and the ToolTrace `authorization`
    verdict; `token` matched `input_tokens`/`output_tokens`. A public auditor could
    not see whether a tool call was allowed or denied, and the projected values were
    no longer valid against ProviderUsage / ToolTrace.
    """
    projected = public_projection(
        {
            "run_inputs": {"authorization_mode": "enforced"},
            "tool_traces": [
                {"name": "propose_jira_issue", "authorization": "denied", "status": "rejected"}
            ],
            "provider_traces": [
                {"usage": {"input_tokens": 180, "output_tokens": 160, "total_tokens": 340}}
            ],
        }
    )

    assert projected["run_inputs"]["authorization_mode"] == "enforced"
    assert projected["tool_traces"][0]["authorization"] == "denied"
    usage = projected["provider_traces"][0]["usage"]
    assert usage == {"input_tokens": 180, "output_tokens": 160, "total_tokens": 340}


def test_credential_shaped_keys_are_still_redacted() -> None:
    projected = public_projection(
        {
            "api_key": "abc",
            "cohere_api_key": "abc",
            "access_token": "abc",
            "token": "abc",
            "authorization_header": "Bearer abc",
            "client_secret": "abc",
            "password": "abc",
            "cookie": "abc",
            "system_prompt": "hidden",
            "reasoning": "hidden",
            "traceback": "hidden",
            "raw_payload": "hidden",
        }
    )

    assert set(projected.values()) == {"[REDACTED]"}


def test_secret_shaped_values_are_still_scrubbed_under_a_safe_key() -> None:
    projected = public_projection({"safe_detail": "sent Authorization: Bearer abcdefghijklmnop"})

    assert "abcdefghijklmnop" not in projected["safe_detail"]
    assert "[SECRET]" in projected["safe_detail"]
