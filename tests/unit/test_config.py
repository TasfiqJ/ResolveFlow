from __future__ import annotations

import pytest
from pydantic import ValidationError
from resolveflow.config import Settings


def test_public_profile_rejects_write_credentials() -> None:
    with pytest.raises(ValidationError, match="public mode"):
        Settings(environment="public", jira_api_token="not-a-real-token")


def test_live_public_requires_provider_kill_switch_enablement() -> None:
    with pytest.raises(ValidationError, match="explicitly enabled"):
        Settings(public_live_mode=True, cohere_allow_live=False)
