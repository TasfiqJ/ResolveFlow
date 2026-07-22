from __future__ import annotations

from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.domain.hashing import canonical_json, checksum
from resolveflow.domain.models import ContextStatus
from resolveflow.intake.web import canonical_hero_case


def test_canonical_hash_is_stable_across_key_order() -> None:
    assert checksum({"b": 2, "a": 1}) == checksum({"a": 1, "b": 2})
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_web_case_is_synthetic_and_missing_cluster() -> None:
    case = canonical_hero_case()
    assert case.synthetic is True
    assert case.missing_fields == ("cluster_id",)
    assert case.error_code == "PYM-431"


def test_context_is_deterministic_and_failure_codes_are_typed() -> None:
    case = canonical_hero_case()
    repository = FixtureContextRepository()
    first = repository.enrich(case)
    second = repository.enrich(case)
    assert first == second
    clusters = next(item for item in first if item.operation == "get_active_clusters")
    assert clusters.status is ContextStatus.NOT_FOUND
    assert all(item.operation in repository.allowed_operations for item in first)
