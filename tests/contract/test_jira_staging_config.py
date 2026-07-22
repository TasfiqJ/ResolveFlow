from __future__ import annotations

import pytest
from resolveflow.actions.connectors import DisabledJiraCloudConnector, JiraStagingConfig
from resolveflow.actions.models import DispatchPayload


def test_staging_mapping_is_narrow_and_adapter_stays_disabled() -> None:
    config = JiraStagingConfig(base_url="https://example.atlassian.net", project_key="DEV")
    connector = DisabledJiraCloudConnector(config=config)
    assert dict(config.priority_map) == {"High": "High", "Medium": "Medium", "Low": "Low"}
    with pytest.raises(RuntimeError, match="real_jira_connector_disabled"):
        connector.create_issue(DispatchPayload.model_construct())


def test_staging_requires_https_and_valid_project() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        JiraStagingConfig(base_url="http://example.test", project_key="DEV")
    with pytest.raises(ValueError, match="project key"):
        JiraStagingConfig(base_url="https://example.test", project_key="bad-key")
