from resolveflow.evaluation.integrity import audit_evaluation_integrity


def test_integrity_audit_does_not_count_duplicate_ids_as_independent_truths() -> None:
    audit = audit_evaluation_integrity()

    assert audit.catalog_entry_count == 36
    assert audit.unique_semantic_truth_count == 1
    assert not audit.dataset_distinctness_verified
    assert len(audit.duplicate_truth_groups) == 1
    assert len(audit.duplicate_truth_groups[0]) == 36
    assert audit.human_reviewed_truth_count == 0


def test_declared_security_matrix_is_not_mislabeled_as_executed_replays() -> None:
    audit = audit_evaluation_integrity()

    assert audit.security_matrix_declared_count == 200
    assert audit.security_matrix_expanded_count == 200
    assert audit.security_matrix_full_replay_execution_count == 0
    assert not audit.security_matrix_execution_verified
    assert audit.attack_family_payload_coverage_count == audit.attack_family_count == 5
    assert audit.unique_attack_payload_count == 5
    assert audit.required_variant_payload_count == 20
    assert audit.attack_payload_control_execution_count == 5
    assert audit.attack_payload_control_pass_count == 5
