def test_verdict_links_every_failing_replay(candidate_bundle) -> None:  # type: ignore[no-untyped-def]
    verdict = candidate_bundle.baseline.verdict
    expected = {
        link
        for outcome in verdict.hard_outcomes
        if outcome.status == "fail"
        for link in outcome.failing_replay_links
    }
    assert expected
    assert set(verdict.failing_replay_links) == expected
