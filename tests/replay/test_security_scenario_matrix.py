from resolveflow.replay.security_matrix import (
    expand_security_matrix,
    load_security_matrix,
    load_security_matrix_execution,
)


def test_two_hundred_draft_security_scenarios_are_declared_without_live_calls() -> None:
    matrix = load_security_matrix()
    scenarios = expand_security_matrix(matrix)

    assert matrix.declared_scenario_count == 200
    assert matrix.live_provider_calls == 0
    assert len(scenarios) == 200
    assert len({item.scenario_id for item in scenarios}) == 200
    assert len({item.truth_id for item in scenarios}) == 10
    assert len({item.attack_family for item in scenarios}) == 5
    assert all(item.content_label == "DRAFT_PENDING_HUMAN_REVIEW" for item in scenarios)


def test_execution_snapshot_retains_one_checksummed_result_per_declared_cell() -> None:
    execution = load_security_matrix_execution()

    assert execution.executed_count == execution.declared_count == 200
    assert execution.pass_count + execution.failure_count == execution.executed_count
    assert len(execution.results) == execution.executed_count
    assert all(item.passed or item.failure_reasons for item in execution.results)
    assert all(item.provider == "recorded_fixture" for item in execution.results)
