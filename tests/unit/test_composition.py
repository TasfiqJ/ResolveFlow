from __future__ import annotations

import pytest
from resolveflow.agent.cohere import CohereChatAdapter
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.composition import build_orchestrator
from resolveflow.config import Settings
from resolveflow.retrieval.cohere import CohereEmbedAdapter, CohereRerankAdapter
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


def test_fixture_composition_applies_configured_agent_policy_without_live_adapters() -> None:
    orchestrator = build_orchestrator(
        Settings(
            cohere_command_model="command-configured",
            agent_max_provider_calls=3,
            agent_max_total_tokens=2048,
        )
    )

    assert isinstance(orchestrator.agent.provider, FixtureChatAdapter)
    assert isinstance(orchestrator.embedding_adapter, FixtureEmbeddingAdapter)
    assert isinstance(orchestrator.rerank_adapter, FixtureRerankAdapter)
    assert orchestrator.provenance == "recorded_fixture"
    assert orchestrator.agent.model == "command-configured"
    assert orchestrator.agent.budgets.max_provider_calls == 3
    assert orchestrator.agent.budgets.max_total_tokens == 2048


def test_live_composition_wires_chat_embedding_and_rerank_to_one_path() -> None:
    client = object()
    settings = Settings(
        cohere_allow_live=True,
        cohere_api_key="synthetic-test-key",
        cohere_command_model="command-configured",
        cohere_embed_model="embed-configured",
        cohere_rerank_fast_model="rerank-v4.0-fast",
    )

    orchestrator = build_orchestrator(settings, cohere_client=client)

    assert isinstance(orchestrator.agent.provider, CohereChatAdapter)
    assert orchestrator.agent.provider.client is client
    assert orchestrator.agent.model == "command-configured"
    assert isinstance(orchestrator.embedding_adapter, CohereEmbedAdapter)
    assert orchestrator.embedding_adapter.model == "embed-configured"
    assert isinstance(orchestrator.rerank_adapter, CohereRerankAdapter)
    assert orchestrator.rerank_adapter.model == "rerank-v4.0-fast"
    assert orchestrator.provenance == "live_provider"


def test_client_injection_cannot_bypass_live_mode_authority() -> None:
    with pytest.raises(ValueError, match="live mode is disabled"):
        build_orchestrator(Settings(), cohere_client=object())
