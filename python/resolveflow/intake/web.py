from __future__ import annotations

from datetime import datetime

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import CanonicalCase


def canonical_hero_case(source_system: str = "web") -> CanonicalCase:
    body = {
        "case_id": "case_hero_payments_001",
        "tenant_id": "tenant_heliopay_synthetic",
        "customer_id": "cust_heliopay_001",
        "reporter": "Maya Chen (synthetic)",
        "source_system": source_system,
        "channel": "#payments-incidents",
        "received_at": datetime.fromisoformat("2026-07-15T14:22:00+00:00"),
        "case_time": datetime.fromisoformat("2026-07-15T14:22:00+00:00"),
        "raw_text": (
            "HelioPay card transactions started failing with PYM-431 after rollout "
            "rollout-payments-2026-07-15. Cluster ID is not available."
        ),
    }
    return CanonicalCase(**body, checksum=checksum(body))
