from __future__ import annotations

import os

import pytest
from resolveflow.config import get_settings

SAFE_TEST_ENVIRONMENT = {
    "RESOLVEFLOW_ENVIRONMENT": "snapshot",
    "RESOLVEFLOW_BUILD_ID": "foundation-v1",
    "RESOLVEFLOW_GIT_SHA": "uncommitted",
    "RESOLVEFLOW_COHERE_ALLOW_LIVE": "false",
    "RESOLVEFLOW_COHERE_API_KEY": "",
    "RESOLVEFLOW_PUBLIC_LIVE_MODE": "false",
    "RESOLVEFLOW_SLACK_SIGNING_SECRET": "",
    "RESOLVEFLOW_JIRA_API_TOKEN": "",
    "RESOLVEFLOW_JIRA_REAL_ENABLED": "false",
    "RESOLVEFLOW_JIRA_EXTERNAL_WRITES_AUTHORIZED": "false",
    "RESOLVEFLOW_ACTION_DISPATCH_ENABLED": "false",
}
for variable_name, safe_value in SAFE_TEST_ENVIRONMENT.items():
    os.environ[variable_name] = safe_value
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def isolate_runtime_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep developer secrets and live switches from changing test behavior."""
    for name, value in SAFE_TEST_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
