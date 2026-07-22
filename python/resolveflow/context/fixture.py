from __future__ import annotations

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import CanonicalCase, ContextResult, ContextStatus


class FixtureContextRepository:
    """Named, deterministic, read-only context operations for the hero fixture."""

    allowed_operations = frozenset(
        {"get_customer_profile", "get_active_clusters", "get_rollouts", "get_open_incidents"}
    )

    def enrich(self, case: CanonicalCase) -> tuple[ContextResult, ...]:
        if case.tenant_id != "tenant_heliopay_synthetic":
            return (self._result("get_customer_profile", ContextStatus.NOT_FOUND, case, {}, ()),)
        return (
            self._result(
                "get_customer_profile",
                ContextStatus.OK,
                case,
                {"customer_id": case.customer_id, "tier": "enterprise", "region": case.region},
                ("customer-row-001",),
            ),
            self._result(
                "get_active_clusters",
                ContextStatus.NOT_FOUND,
                case,
                {"reason": "cluster_id_missing_from_report"},
                (),
            ),
            self._result(
                "get_rollouts",
                ContextStatus.OK,
                case,
                {
                    "rollout_id": "rollout-payments-2026-07-15",
                    "service": "payments-api",
                    "change": "issuer-routing-v3",
                    "status": "completed_before_failures",
                },
                ("rollout-row-20260715",),
            ),
            self._result(
                "get_open_incidents",
                ContextStatus.OK,
                case,
                {"incident_id": "inc-synth-1042", "matching_error": "PYM-431"},
                ("incident-row-1042",),
            ),
        )

    @staticmethod
    def _result(
        operation: str,
        status: ContextStatus,
        case: CanonicalCase,
        data: dict[str, str],
        provenance_ids: tuple[str, ...],
    ) -> ContextResult:
        body = {
            "operation": operation,
            "status": status,
            "as_of": case.case_time,
            "provenance_ids": provenance_ids,
            "data": data,
        }
        return ContextResult(**body, checksum=checksum(body))
