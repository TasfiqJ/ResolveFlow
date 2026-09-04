from __future__ import annotations

import pytest
from resolveflow.retrieval.engine import _cosine


def test_cosine_is_invariant_to_vector_magnitude() -> None:
    assert _cosine((10.0, 0.0), (2.0, 0.0)) == pytest.approx(1.0)
    assert _cosine((10.0, 0.0), (0.0, 200.0)) == pytest.approx(0.0)
    assert _cosine((1e308, 1e308), (1e308, 1e308)) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("left", "right", "message"),
    [
        ((1.0,), (1.0, 2.0), "equal dimensions"),
        ((0.0, 0.0), (1.0, 0.0), "non-zero norm"),
        ((float("nan"), 0.0), (1.0, 0.0), "finite"),
    ],
)
def test_cosine_rejects_malformed_vectors(
    left: tuple[float, ...], right: tuple[float, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _cosine(left, right)
