"""First-order error propagation against results known in closed form."""

from __future__ import annotations

import math
from collections.abc import Sequence

import pytest

from rietcalc_demo.domain.propagation import propagate


def test_a_linear_function_is_exact() -> None:
    def f(p: Sequence[float]) -> float:
        return 3.0 * p[0] - 2.0 * p[1]

    assert propagate(f, (10.0, 4.0), (0.1, 0.2)) == pytest.approx(math.hypot(0.3, 0.4))


def test_a_product_gives_the_relative_rule() -> None:
    def f(p: Sequence[float]) -> float:
        return p[0] * p[1]

    # sigma(xy)/xy = sqrt((sx/x)^2 + (sy/y)^2)
    expected = 6.0 * math.hypot(0.02 / 2.0, 0.06 / 3.0)
    assert propagate(f, (2.0, 3.0), (0.02, 0.06)) == pytest.approx(expected, rel=1e-8)


def test_fixed_parameters_contribute_nothing() -> None:
    calls: list[int] = []

    def f(p: Sequence[float]) -> float:
        calls.append(1)
        return p[0] ** 2 + p[1] ** 2

    assert propagate(f, (1.0, 2.0), (0.0, 0.0)) == 0.0
    assert not calls  # a zero e.s.d. is skipped, not evaluated


def test_lengths_must_match() -> None:
    with pytest.raises(ValueError, match="length"):
        propagate(lambda p: p[0], (1.0,), (0.1, 0.2))
