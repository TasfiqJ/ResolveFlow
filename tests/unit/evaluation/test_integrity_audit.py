from resolveflow.evaluation.integrity import audit_evaluation_integrity


def test_integrity_audit_does_not_count_duplicate_ids_as_independent_truths() -> None:
    audit = audit_evaluation_integrity()

    assert audit.catalog_entry_count == 36
    assert audit.unique_semantic_truth_count == 1
    assert not audit.dataset_distinctness_verified
    assert len(audit.duplicate_truth_groups) == 1
    assert len(audit.duplicate_truth_groups[0]) == 36
    assert audit.human_reviewed_truth_count == 0


def test_security_matrix_execution_is_backed_by_per_cell_replay_results() -> None:
    audit = audit_evaluation_integrity()

    assert audit.security_matrix_declared_count == 200
    assert audit.security_matrix_expanded_count == 200
    assert audit.security_matrix_full_replay_execution_count == 200
    assert audit.security_matrix_execution_verified
    assert audit.security_matrix_pass_count == 200
    assert audit.security_matrix_failure_count == 0
    assert len(audit.security_matrix_results) == 200
    assert len({item.scenario_id for item in audit.security_matrix_results}) == 200
    assert all(item.audit_chain_verified for item in audit.security_matrix_results)
    assert all(item.trace_event_count == 14 for item in audit.security_matrix_results)
    assert all(item.run_content_hash for item in audit.security_matrix_results)
    assert all(item.trace_final_event_hash for item in audit.security_matrix_results)
    assert all(item.passed or item.failure_reasons for item in audit.security_matrix_results)
    assert audit.attack_family_payload_coverage_count == audit.attack_family_count == 5
    assert audit.unique_attack_payload_count == 5
    assert audit.required_variant_payload_count == 20
    assert audit.attack_payload_control_execution_count == 5
    assert audit.attack_payload_control_pass_count == 5
