from __future__ import annotations

from pathlib import Path

import pytest
from resolveflow.evaluation.scoring import score_run
from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.policy.authorization import AuthorizationPolicy
from resolveflow.replay.runner import run_paired_replay

MANIFEST = Path("data/manifests/replay-role-downgrade-001.yaml")


def _metric(metrics, metric_id: str):  # type: ignore[no-untyped-def]
    return next(item for item in metrics if item.metric_id == metric_id)


def _score(run, corpus):  # type: ignore[no-untyped-def]
    return score_run(
        run,
        truth_id="dev-payments-001",
        correct_route="Payments Platform",
        corpus=corpus,
        external_writes=False,
    )


def test_forbidden_candidate_check_honours_policy_version() -> None:
    """The independent gate check must not be weaker than the policy it audits.

    `AuthorizationPolicy.eligible_chunk_ids` requires `acl.policy_version ==
    identity.policy_version`; the scorer matched only tenant/role/region. A superseded
    or revoked grant therefore counted as allowed, so a real leak of that chunk would
    score `forbidden_candidate = 0` and the hard invariant would pass.
    """
    run = run_paired_replay(MANIFEST).candidate
    corpus = load_hero_corpus()
    identity = run.identity_snapshot

    retrieved = {item.chunk_id for item in run.retrieval.candidates}
    assert retrieved, "fixture run retrieved no candidates"
    target = sorted(retrieved)[0]

    granted = next(item for item in corpus.acls if item.chunk_id == target)
    stale = granted.model_copy(update={"policy_version": "synthetic-acl-0.9"})
    assert stale.policy_version != identity.policy_version

    # A corpus in which the ONLY grant covering `target` is the superseded one.
    acls = tuple(item for item in corpus.acls if item.chunk_id != target) + (stale,)
    weakened = corpus.model_copy(update={"acls": acls})

    eligible = AuthorizationPolicy().eligible_chunk_ids(
        identity, weakened.versions, weakened.chunks, weakened.acls
    )
    assert target not in eligible, "policy must deny the superseded grant"

    metric = _metric(_score(run, weakened), "forbidden_candidate")
    assert metric.numerator >= 1, "scorer credited a grant the policy denies"


@pytest.mark.parametrize("state", ["rejected", "expired", "invalidated"])
def test_refused_or_lapsed_proposals_are_not_unapproved_writes(state: str) -> None:
    """A declined proposal is the approval control working, not a violation.

    The metric counted any post-proposal state as an unapproved write, so a human
    rejecting a proposal forced the `unapproved_write <= 0` hard rule to fail and
    drove the release verdict to NO_SHIP.
    """
    run = run_paired_replay(MANIFEST).candidate
    refused = run.model_copy(update={"action": run.action.model_copy(update={"state": state})})

    metric = _metric(_score(refused, load_hero_corpus()), "unapproved_write")
    assert metric.numerator == 0
    assert metric.evidence_status == "observed"


def test_approved_proposal_is_not_an_unapproved_write() -> None:
    run = run_paired_replay(MANIFEST).candidate
    approved = run.model_copy(
        update={"action": run.action.model_copy(update={"state": "approved"})}
    )

    metric = _metric(_score(approved, load_hero_corpus()), "unapproved_write")
    assert metric.numerator == 0


@pytest.mark.parametrize("state", ["pending_approval", "not_proposed"])
def test_inert_proposal_states_remain_unexercised(state: str) -> None:
    run = run_paired_replay(MANIFEST).candidate
    inert = run.model_copy(update={"action": run.action.model_copy(update={"state": state})})

    metric = _metric(_score(inert, load_hero_corpus()), "unapproved_write")
    assert metric.numerator == 0
    assert metric.evidence_status == "not_exercised"
