from resolveflow.replay.models import MutationType
from resolveflow.replay.mutations import MUTATION_REGISTRY


def test_every_supported_v1_mutation_has_one_typed_handler() -> None:
    assert set(MUTATION_REGISTRY) == set(MutationType)
    assert len(MUTATION_REGISTRY) == 8
