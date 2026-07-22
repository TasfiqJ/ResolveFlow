from __future__ import annotations

from typing import Protocol

from resolveflow.domain.models import CanonicalCase, ContextResult, FinalResponse


class AgentPort(Protocol):
    def resolve(self, case: CanonicalCase, context: tuple[ContextResult, ...]) -> FinalResponse: ...


class RetrievalPort(Protocol):
    """Stage 02 boundary; implementations must return only policy-eligible evidence."""

    def retrieve(self, case: CanonicalCase) -> tuple[str, ...]: ...


class VerifierPort(Protocol):
    """Stage 03 boundary for claim-level verification."""

    def verify(self, response: FinalResponse) -> FinalResponse: ...
