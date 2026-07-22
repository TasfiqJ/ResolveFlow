from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from resolveflow.intake.slack import SlackRequestVerifier, SlackVerificationError


def signature(secret: str, timestamp: str, body: bytes) -> str:
    base = b"v0:" + timestamp.encode() + b":" + body
    return "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()


def test_valid_signature() -> None:
    body = json.dumps({"type": "url_verification", "challenge": "safe"}).encode()
    verifier = SlackRequestVerifier("fixture-secret", clock=lambda: 1000)
    verifier.verify(body, "1000", signature("fixture-secret", "1000", body))


def test_invalid_signature() -> None:
    with pytest.raises(SlackVerificationError, match="slack_signature_invalid"):
        SlackRequestVerifier("fixture-secret", clock=lambda: 1000).verify(b"{}", "1000", "v0=no")


def test_stale_timestamp() -> None:
    with pytest.raises(SlackVerificationError, match="slack_timestamp_stale"):
        SlackRequestVerifier("fixture-secret", clock=lambda: 2000).verify(b"{}", "1000", "v0=no")
