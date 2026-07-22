from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from urllib.parse import urlparse

from resolveflow.actions.models import (
    ConnectorDisposition,
    ConnectorResult,
    DispatchPayload,
    ReconciliationResult,
)
from resolveflow.domain.hashing import checksum


class ConnectorFault(str, Enum):
    NONE = "none"
    TIMEOUT_BEFORE_SEND = "timeout_before_send"
    TIMEOUT_AFTER_ACCEPT = "timeout_after_accept"
    ACKNOWLEDGEMENT_LOST = "acknowledgement_lost"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    PERMISSION_DENIED = "permission_denied"


class JiraConnector(Protocol):
    def create_issue(self, payload: DispatchPayload) -> ConnectorResult: ...

    def reconcile(self, idempotency_key: str) -> ReconciliationResult: ...


@dataclass(frozen=True)
class JiraStagingConfig:
    """Narrow development-project mapping; values are discovered, never model-authored."""

    base_url: str
    project_key: str
    issue_type: str = "Task"
    team_field: str = "team"
    priority_map: tuple[tuple[str, str], ...] = (
        ("High", "High"),
        ("Medium", "Medium"),
        ("Low", "Low"),
    )

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("jira staging base URL must use HTTPS")
        if not self.project_key.isascii() or not self.project_key.replace("_", "").isalnum():
            raise ValueError("jira staging project key is invalid")
        if {source for source, _ in self.priority_map} != {"High", "Medium", "Low"}:
            raise ValueError("jira staging priority mapping must be complete")


@dataclass
class SyntheticJiraConnector:
    """Deterministic Jira double with remote-marker reconciliation."""

    faults: deque[ConnectorFault] = field(default_factory=deque)
    _issues: dict[str, tuple[str, str]] = field(default_factory=dict)

    def queue_faults(self, *faults: ConnectorFault) -> None:
        self.faults.extend(faults)

    def create_issue(self, payload: DispatchPayload) -> ConnectorResult:
        fingerprint = checksum(payload)
        existing = self._issues.get(payload.idempotency_marker)
        if existing is not None:
            return ConnectorResult(
                disposition=ConnectorDisposition.ACKNOWLEDGED,
                request_fingerprint=fingerprint,
                remote_issue_key=existing[0],
                provider_request_id=existing[1],
            )
        fault = self.faults.popleft() if self.faults else ConnectorFault.NONE
        if fault is ConnectorFault.TIMEOUT_BEFORE_SEND:
            return ConnectorResult(
                disposition=ConnectorDisposition.PRE_SEND_FAILURE,
                request_fingerprint=fingerprint,
                safe_error_code="jira_timeout_before_send",
            )
        if fault in {ConnectorFault.TIMEOUT_AFTER_ACCEPT, ConnectorFault.ACKNOWLEDGEMENT_LOST}:
            issue_key, request_id = self._record(payload, fingerprint)
            return ConnectorResult(
                disposition=ConnectorDisposition.UNCERTAIN,
                request_fingerprint=fingerprint,
                provider_request_id=request_id,
                safe_error_code=(
                    "jira_timeout_after_possible_accept"
                    if fault is ConnectorFault.TIMEOUT_AFTER_ACCEPT
                    else "jira_acknowledgement_lost"
                ),
            )
        if fault is ConnectorFault.RATE_LIMITED:
            return ConnectorResult(
                disposition=ConnectorDisposition.RATE_LIMITED,
                request_fingerprint=fingerprint,
                safe_error_code="jira_rate_limited",
                retry_after_seconds=15,
            )
        if fault is ConnectorFault.SERVER_ERROR:
            return ConnectorResult(
                disposition=ConnectorDisposition.SERVER_ERROR,
                request_fingerprint=fingerprint,
                safe_error_code="jira_server_error",
            )
        if fault is ConnectorFault.PERMISSION_DENIED:
            return ConnectorResult(
                disposition=ConnectorDisposition.PERMISSION_DENIED,
                request_fingerprint=fingerprint,
                safe_error_code="jira_permission_denied",
            )
        issue_key, request_id = self._record(payload, fingerprint)
        return ConnectorResult(
            disposition=ConnectorDisposition.ACKNOWLEDGED,
            request_fingerprint=fingerprint,
            remote_issue_key=issue_key,
            provider_request_id=request_id,
        )

    def reconcile(self, idempotency_key: str) -> ReconciliationResult:
        existing = self._issues.get(idempotency_key)
        return ReconciliationResult(
            found=existing is not None,
            idempotency_key=idempotency_key,
            remote_issue_key=existing[0] if existing else None,
            safe_code="jira_marker_found" if existing else "jira_marker_not_found",
        )

    @property
    def issue_count(self) -> int:
        return len(self._issues)

    def _record(self, payload: DispatchPayload, fingerprint: str) -> tuple[str, str]:
        issue_key = f"SYN-{len(self._issues) + 1}"
        request_id = f"synthetic-{fingerprint.split(':', 1)[1][:12]}"
        self._issues[payload.idempotency_marker] = (issue_key, request_id)
        return issue_key, request_id


@dataclass(frozen=True)
class DisabledJiraCloudConnector:
    """Real-adapter boundary. This build cannot send because it is always disabled."""

    enabled: bool = False
    config: JiraStagingConfig | None = None

    def create_issue(self, payload: DispatchPayload) -> ConnectorResult:
        del payload
        raise RuntimeError("real_jira_connector_disabled")

    def reconcile(self, idempotency_key: str) -> ReconciliationResult:
        del idempotency_key
        raise RuntimeError("real_jira_connector_disabled")
