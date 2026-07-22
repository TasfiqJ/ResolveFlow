from __future__ import annotations

from typing import Protocol

from resolveflow.domain.models import CanonicalCase, ContextResult


class ContextRepository(Protocol):
    def enrich(self, case: CanonicalCase) -> tuple[ContextResult, ...]: ...
