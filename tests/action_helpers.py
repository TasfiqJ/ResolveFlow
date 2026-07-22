from __future__ import annotations

from datetime import datetime, timezone

from resolveflow.actions.models import ActionProposal
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator

NOW = datetime(2026, 7, 21, 0, 1, tzinfo=timezone.utc)


def fixture_proposal() -> ActionProposal:
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(), GovernedAgent(FixtureChatAdapter())
    )
    orchestrator.run(canonical_hero_case())
    assert orchestrator.latest_proposal is not None
    return orchestrator.latest_proposal
