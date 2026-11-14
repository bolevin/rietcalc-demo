from __future__ import annotations

import pytest

from rietcalc_demo.domain import histogram


def test_bins_from_first_to_last_non_empty_with_gaps_kept() -> None:
    bins = histogram([1.94, 1.96, 2.37, 2.38], width=0.2, low=0.0)
    assert [(round(b.low, 6), b.count) for b in bins] == [(1.8, 2), (2.0, 0), (2.2, 2)]


def test_a_value_on_a_bin_edge_opens_the_next_bin() -> None:
    # bins are [low, high): 0.5 belongs to [0.5, 0.75), not to [0.25, 0.5)
    (only,) = histogram([0.5, 0.6], width=0.25)
    assert (only.low, only.high, only.count) == (0.5, 0.75, 2)


def test_values_below_low_are_ignored_and_nothing_gives_nothing() -> None:
    assert histogram([0.5], width=0.1, low=1.0) == ()
    assert histogram([], width=0.1) == ()


@pytest.mark.parametrize("width", [0.0, -0.1, float("nan")])
def test_the_width_must_be_positive(width: float) -> None:
    with pytest.raises(ValueError, match="width"):
        histogram([1.0], width)
