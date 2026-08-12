from __future__ import annotations

from typing import Any

from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.contracts import AgentBudgets
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.config import Settings
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.orchestrator import ResolveOrchestrator
from resolveflow.retrieval.cohere import CohereEmbedAdapter, CohereRerankAdapter


def _governed_agent(
    settings: Settings,
    provider: FixtureChatAdapter | CohereChatAdapter,
) -> GovernedAgent:
    return GovernedAgent(
        provider,
        budgets=AgentBudgets(
            max_tool_rounds=settings.agent_max_tool_rounds,
            max_provider_calls=settings.agent_max_provider_calls,
            max_total_tokens=settings.agent_max_total_tokens,
            max_output_tokens_per_call=(2048 if provider.provider_name == "cohere" else 1024),
            wall_clock_seconds=settings.agent_wall_clock_seconds,
            tool_timeout_seconds=settings.agent_tool_timeout_seconds,
        ),
        model=settings.cohere_command_model,
    )


def build_orchestrator(
    settings: Settings,
    *,
    cohere_client: Any | None = None,
) -> ResolveOrchestrator:
    """Build the single Resolve path; live adapters require explicit live authority."""
    if not settings.cohere_allow_live:
        if cohere_client is not None:
            raise ValueError("a Cohere client cannot be injected while live mode is disabled")
        return ResolveOrchestrator(
            FixtureContextRepository(),
            _governed_agent(settings, FixtureChatAdapter()),
        )

    if cohere_client is None:
        if not settings.cohere_api_key:
            raise ValueError("live Cohere composition requires an API key")
        import cohere

        cohere_client = cohere.ClientV2(api_key=settings.cohere_api_key)

    return ResolveOrchestrator(
        FixtureContextRepository(),
        _governed_agent(
            settings,
            CohereChatAdapter(
                client=cohere_client,
                allow_live=True,
                api_key=settings.cohere_api_key,
            ),
        ),
        embedding_adapter=CohereEmbedAdapter(
            cohere_client,
            model=settings.cohere_embed_model,
        ),
        rerank_adapter=CohereRerankAdapter(
            cohere_client,
            settings.cohere_rerank_fast_model,
        ),
    )
