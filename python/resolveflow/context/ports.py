from __future__ import annotations

from typing import Protocol

from resolveflow.domain.models import CanonicalCase, ContextResult


class ContextRepository(Protocol):
    supports_deadline: bool

    def enrich(
        self, case: CanonicalCase, *, timeout_seconds: float | None = None
    ) -> tuple[ContextResult, ...]: ...
