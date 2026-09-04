from __future__ import annotations

import time

import pytest
from resolveflow.agent.contracts import AgentBudgets
from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.eval.ab_runner import RunMetrics
from resolveflow.eval.scenarios import all_scenarios
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator
from resolveflow.retrieval.cohere import CohereEmbedAdapter, ProviderAdapterError
from resolveflow.retrieval.fixture import FixtureEmbeddingAdapter, FixtureRerankAdapter


class FailingEmbedder(FixtureEmbeddingAdapter):
    model = "embed-v4.0"
    supports_deadline = True
    provider_backed = True

    def embed_query(self, text: str, *, timeout_seconds: float | None = None):  # type: ignore[no-untyped-def]
        del text, timeout_seconds
        raise ProviderAdapterError("embed", self.model)


class FailingReranker(FixtureRerankAdapter):
    model = "rerank-v4.0-fast"
    supports_deadline = True
    provider_backed = True

    def rerank(
        self,
        query: str,
        documents: tuple[str, ...],
        top_n: int,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[tuple[int, float], ...]:
        del query, documents, top_n, timeout_seconds
        raise ProviderAdapterError("rerank", self.model)


@pytest.mark.parametrize(
    ("embedder", "reranker", "code"),
    [
        (FailingEmbedder(), FixtureRerankAdapter(), "retrieval_embed_provider_error"),
        (FixtureEmbeddingAdapter(), FailingReranker(), "retrieval_rerank_provider_error"),
    ],
)
def test_retrieval_provider_failure_returns_auditable_needs_review_snapshot(
    embedder: object, reranker: object, code: str
) -> None:
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(),
        GovernedAgent(FixtureChatAdapter()),
        embedding_adapter=embedder,  # type: ignore[arg-type]
        rerank_adapter=reranker,  # type: ignore[arg-type]
    )

    snapshot = orchestrator.run(canonical_hero_case())

    assert snapshot.retrieval.failure_code == code
    assert snapshot.response.needs_review is True
    assert snapshot.response.route is None
    assert snapshot.provider_traces == ()
    assert snapshot.timing is not None
    assert snapshot.timing.provider_call_count == 1
    assert snapshot.action.state == "not_proposed"
    metrics = RunMetrics(all_scenarios()[0], "guarded-v1", snapshot, orchestrator.corpus)
    assert metrics.terminal_reason == code
    assert any(
        event.outcome == "failed" and event.safe_detail.get("failure_code") == code
        for event in snapshot.trace
    )
    if code == "retrieval_embed_provider_error":
        assert any(event.event_name == "retrieval.fusion.not_attempted" for event in snapshot.trace)
    else:
        assert any(
            event.event_name == "retrieval.fusion.completed" and event.outcome == "ok"
            for event in snapshot.trace
        )
    assert any(event.event_name == "tools.bounded.not_attempted" for event in snapshot.trace)
    assert any(
        event.event_name == "evidence_graph.verification.not_attempted" for event in snapshot.trace
    )


class DeadlineAwareSlowEmbedder(FixtureEmbeddingAdapter):
    model = "embed-v4.0"
    supports_deadline = True

    def __init__(self) -> None:
        self.received_timeout: float | None = None

    def embed_query(self, text: str, *, timeout_seconds: float | None = None) -> tuple[float, ...]:
        self.received_timeout = timeout_seconds
        assert timeout_seconds is not None
        time.sleep(timeout_seconds + 0.005)
        return super().embed_query(text)


def test_orchestrator_propagates_one_deadline_through_retrieval() -> None:
    embedder = DeadlineAwareSlowEmbedder()
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(),
        GovernedAgent(FixtureChatAdapter(), budgets=AgentBudgets(wall_clock_seconds=0.02)),
        embedding_adapter=embedder,
        rerank_adapter=FixtureRerankAdapter(),
    )
    started = time.perf_counter()

    snapshot = orchestrator.run(canonical_hero_case())

    assert time.perf_counter() - started < 0.1
    assert embedder.received_timeout is not None
    assert 0 < embedder.received_timeout <= 0.02
    assert snapshot.retrieval.failure_code == "wall_clock_budget_exhausted"
    assert snapshot.response.needs_review is True


def test_zero_norm_cohere_embedding_fails_to_an_auditable_snapshot() -> None:
    class ZeroVectorClient:
        def embed(self, **kwargs: object) -> object:
            texts = kwargs["texts"]
            assert isinstance(texts, list)
            return type(
                "Response",
                (),
                {"embeddings": type("Vectors", (), {"float": [[0.0, 0.0] for _ in texts]})()},
            )()

    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(),
        GovernedAgent(FixtureChatAdapter()),
        embedding_adapter=CohereEmbedAdapter(ZeroVectorClient(), dimension=2),
        rerank_adapter=FixtureRerankAdapter(),
    )

    snapshot = orchestrator.run(canonical_hero_case())

    assert snapshot.retrieval.failure_code == "retrieval_embed_provider_error"
    assert snapshot.retrieval.embedding_source == "unavailable"
    assert snapshot.retrieval.rerank_payload_checksum is None
    assert snapshot.response.needs_review is True
    assert snapshot.provider_traces == ()


def test_unbounded_retrieval_adapter_is_rejected_before_invocation() -> None:
    class UnboundedEmbedder:
        model = "unbounded-embedder"

        def __init__(self) -> None:
            self.calls = 0

        def embed_query(self, text: str) -> tuple[float, ...]:
            del text
            self.calls += 1
            return (1.0, 0.0)

        def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            self.calls += 1
            return tuple((1.0, 0.0) for _ in texts)

    embedder = UnboundedEmbedder()
    orchestrator = ResolveOrchestrator(
        FixtureContextRepository(),
        GovernedAgent(FixtureChatAdapter()),
        embedding_adapter=embedder,  # type: ignore[arg-type]
        rerank_adapter=FixtureRerankAdapter(),
    )

    snapshot = orchestrator.run(canonical_hero_case())

    assert embedder.calls == 0
    assert snapshot.retrieval.failure_code == "retrieval_deadline_unsupported"
    assert snapshot.timing is not None
    assert snapshot.timing.provider_call_count == 0


def test_unbounded_context_repository_is_rejected_before_invocation() -> None:
    class UnboundedContextRepository:
        def __init__(self) -> None:
            self.calls = 0

        def enrich(self, case: object) -> tuple[object, ...]:
            del case
            self.calls += 1
            return ()

    repository = UnboundedContextRepository()
    orchestrator = ResolveOrchestrator(
        repository,  # type: ignore[arg-type]
        GovernedAgent(FixtureChatAdapter()),
        embedding_adapter=FixtureEmbeddingAdapter(),
        rerank_adapter=FixtureRerankAdapter(),
    )

    snapshot = orchestrator.run(canonical_hero_case())

    assert repository.calls == 0
    assert snapshot.retrieval.failure_code == "context_deadline_unsupported"
    assert snapshot.retrieval.failure_stage == "context"
    assert snapshot.response.needs_review is True
    assert snapshot.timing is not None
    assert snapshot.timing.provider_call_count == 0
