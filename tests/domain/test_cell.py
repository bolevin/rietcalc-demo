"""The unit cell: metric, volume and the e.s.d. of the volume."""

from __future__ import annotations

import math

import pytest

from rietcalc_demo.domain import InvalidStructureError, Measured, UnitCell
from rietcalc_demo.domain.cell import metric_distance


def orthorhombic(lengths: tuple[float, float, float], esds: tuple[float, float, float]) -> UnitCell:
    (a, b, c), (sa, sb, sc) = lengths, esds
    return UnitCell(
        Measured(a, sa), Measured(b, sb), Measured(c, sc), Measured(90), Measured(90), Measured(90)
    )


def test_orthorhombic_volume_and_its_esd_match_the_closed_form() -> None:
    cell = orthorhombic((5.4423, 7.6401, 5.3807), (0.0003, 0.0004, 0.0003))
    v = 5.4423 * 7.6401 * 5.3807
    # V = abc, so (sigma V / V)^2 is the sum of the squared relative e.s.d.'s
    sv = v * math.sqrt((0.0003 / 5.4423) ** 2 + (0.0004 / 7.6401) ** 2 + (0.0003 / 5.3807) ** 2)
    assert cell.volume.value == pytest.approx(v, rel=1e-12)
    assert cell.volume.esd == pytest.approx(sv, rel=1e-6)


def test_hexagonal_volume() -> None:
    cell = UnitCell(
        Measured(3.0), Measured(3.0), Measured(5.0), Measured(90), Measured(90), Measured(120)
    )
    assert cell.volume.value == pytest.approx(3.0 * 3.0 * 5.0 * math.sqrt(3) / 2)


def test_metric_distance_in_an_oblique_cell() -> None:
    # gamma = 120: the vector (1, 1, 0) has length a, the classic hexagonal identity
    assert metric_distance((3.0, 3.0, 5.0, 90, 90, 120), (1.0, 1.0, 0.0)) == pytest.approx(3.0)
    assert metric_distance((3.0, 3.0, 5.0, 90, 90, 120), (1.0, -1.0, 0.0)) == pytest.approx(
        3.0 * math.sqrt(3)
    )


def test_reciprocal_lengths_of_an_orthogonal_cell_are_inverse_lengths() -> None:
    cell = orthorhombic((4.0, 5.0, 8.0), (0, 0, 0))
    assert cell.reciprocal_lengths() == pytest.approx((1 / 4, 1 / 5, 1 / 8))


@pytest.mark.parametrize(
    ("lengths", "angles"),
    [
        ((0.0, 1.0, 1.0), (90, 90, 90)),  # a zero length
        ((1.0, 1.0, 1.0), (180, 90, 90)),  # an angle out of range
        ((1.0, 1.0, 1.0), (120, 120, 120)),  # three angles that close no volume
    ],
)
def test_impossible_cells_are_refused(
    lengths: tuple[float, float, float], angles: tuple[float, float, float]
) -> None:
    with pytest.raises(InvalidStructureError):
        UnitCell(*(Measured(v) for v in (*lengths, *angles)))
