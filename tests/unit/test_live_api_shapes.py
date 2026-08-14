"""Guard the live-call shapes against the installed Cohere SDK.

These are the assumptions that cost real API calls when they are wrong. Each one
is checked against the SDK's own types rather than against documentation, so a
version bump that renames a field fails here instead of failing halfway through
a budgeted live run.
"""

from __future__ import annotations

import inspect

import pytest

from resolveflow.eval.budget import SDK_MAX_RETRIES
from resolveflow.retrieval.cohere import CohereRerankAdapter, read_float_embeddings

cohere = pytest.importorskip("cohere")


def test_embed_float_vectors_are_read_from_the_field_that_exists() -> None:
    """``embeddings.float`` does not exist; the field is ``float_``.

    Reading the wrong one raises AttributeError inside the embed pass, which is
    step one of the live run -- after the embed calls have been billed.
    """
    from cohere.types import EmbedByTypeResponseEmbeddings

    assert "float_" in EmbedByTypeResponseEmbeddings.model_fields
    assert not hasattr(EmbedByTypeResponseEmbeddings(float_=[[0.1]]), "float")

    class _Response:
        embeddings = EmbedByTypeResponseEmbeddings(float_=[[0.1, 0.2]])

    assert read_float_embeddings(_Response()) == [[0.1, 0.2]]


def test_read_float_embeddings_fails_loudly_when_there_are_none() -> None:
    from cohere.types import EmbedByTypeResponseEmbeddings

    class _Response:
        embeddings = EmbedByTypeResponseEmbeddings()

    with pytest.raises(AttributeError):
        read_float_embeddings(_Response())


def test_chat_accepts_every_keyword_the_adapter_sends() -> None:
    parameters = set(inspect.signature(cohere.ClientV2.chat).parameters)
    for name in ("model", "messages", "documents", "tools", "strict_tools", "max_tokens",
                 "temperature", "seed", "safety_mode"):
        assert name in parameters, f"ClientV2.chat has no parameter {name!r}"


def test_rerank_accepts_the_keywords_the_adapter_sends() -> None:
    parameters = set(inspect.signature(cohere.ClientV2.rerank).parameters)
    for name in ("model", "query", "documents", "top_n"):
        assert name in parameters, f"ClientV2.rerank has no parameter {name!r}"
    # v2 rerank dropped return_documents; sending it would be a 4xx.
    assert "return_documents" not in parameters


def test_embed_accepts_the_keywords_the_adapter_sends() -> None:
    parameters = set(inspect.signature(cohere.ClientV2.embed).parameters)
    for name in ("model", "texts", "input_type", "embedding_types", "output_dimension"):
        assert name in parameters, f"ClientV2.embed has no parameter {name!r}"


def test_only_real_rerank_model_ids_are_accepted() -> None:
    """There is no bare ``rerank-v4.0``; only -fast and -pro exist."""
    for model in ("rerank-v4.0-fast", "rerank-v4.0-pro"):
        CohereRerankAdapter(client=object(), model=model)
    with pytest.raises(ValueError):
        CohereRerankAdapter(client=object(), model="rerank-v4.0")


def test_sdk_retries_are_disabled_so_the_ledger_counts_every_http_request() -> None:
    """The SDK retries internally by default and the wrapper never sees it.

    With SDK retries on, a rate-limited burst spends up to 3x the counted calls
    against a 1,000-call monthly quota, and the ledger's "exactly N calls" claim
    is simply untrue.
    """
    assert SDK_MAX_RETRIES == 0
    assert "max_retries" in inspect.signature(cohere.ClientV2.__init__).parameters


def test_live_modules_import_every_name_they_reference() -> None:
    """A module that uses SDK_MAX_RETRIES but forgets to import it raises
    NameError only when the live path executes -- after a real key is loaded and
    calls are about to be spent. Importing the module and checking the name is
    resolvable catches that at test time instead.

    This is the exact bug that stopped a live run: ab_cli referenced
    SDK_MAX_RETRIES at its ClientV2 construction line without importing it.
    """
    import importlib

    for module_name in (
        "resolveflow.eval.ab_cli",
        "resolveflow.eval.embed_corpus",
        "resolveflow.eval.safety_mode_probe",
    ):
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        if "SDK_MAX_RETRIES" in source:
            assert hasattr(module, "SDK_MAX_RETRIES"), (
                f"{module_name} references SDK_MAX_RETRIES but does not import it; "
                f"the live path would raise NameError after loading the API key"
            )


def test_ab_cli_cohere_harness_construction_resolves_all_names(monkeypatch) -> None:
    """Drive _build_harness down the cohere branch far enough to execute the
    ClientV2 construction line, with a fake key and a stub SDK so no network
    call is made. If any name on that path is unbound, this fails here rather
    than mid-run."""
    from resolveflow.eval import ab_cli
    from resolveflow.eval.embed_corpus import CACHE_PATH

    if not CACHE_PATH.exists():
        import pytest

        pytest.skip("embedding cache not present in this checkout")

    monkeypatch.setenv("RESOLVEFLOW_COHERE_API_KEY", "test-key-not-used")

    class _StubClientV2:
        def __init__(self, **kwargs):
            # The construction line passes max_retries=SDK_MAX_RETRIES; if that
            # name were unbound the call would never reach here.
            assert "max_retries" in kwargs

    monkeypatch.setattr(cohere, "ClientV2", _StubClientV2)
    harness, client = ab_cli._build_harness("cohere", 400)
    assert client is not None
