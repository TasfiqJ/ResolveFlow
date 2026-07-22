from __future__ import annotations

from resolveflow.domain.models import CanonicalCase, Citation, ContextResult, FinalResponse


class FixtureAgent:
    """Recorded cited result; no provider call and no connector write."""

    def resolve(self, case: CanonicalCase, context: tuple[ContextResult, ...]) -> FinalResponse:
        rollout = next(item for item in context if item.operation == "get_rollouts")
        if rollout.status.value != "ok":
            raise ValueError("fixture response requires rollout evidence")
        return FinalResponse(
            summary=(
                "The failures align with the issuer-routing-v3 rollout. Route this synthetic "
                "incident to Payments Platform and verify rollback readiness before any change."
            ),
            recommended_steps=(
                "Confirm the affected cluster before executing a rollback.",
                "Compare PYM-431 rates before and after rollout-payments-2026-07-15.",
                "Prepare an inert Jira proposal for Payments Platform review.",
            ),
            unknowns=("The affected cluster ID is not available.",),
            citations=(
                Citation(
                    citation_id="cite_rollout_001",
                    source_id="rollout-row-20260715",
                    title="Synthetic rollout record",
                    version="1",
                    locator="row rollout-payments-2026-07-15",
                    excerpt="issuer-routing-v3 completed before PYM-431 failures",
                ),
                Citation(
                    citation_id="cite_runbook_001",
                    source_id="runbook-payments-rollback-v3",
                    title="Payments rollback runbook",
                    version="3",
                    locator="section 2: preconditions",
                    excerpt=(
                        "Identify the affected cluster and compare error rates before rollback."
                    ),
                ),
            ),
        )
