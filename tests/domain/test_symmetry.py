"""Space-group operators: parsing the CIF notation and applying it."""

from __future__ import annotations

from fractions import Fraction

import pytest

from rietcalc_demo.domain import InvalidStructureError, SymmetryOperator


@pytest.mark.parametrize(
    ("text", "rotation", "translation"),
    [
        ("x, y, z", ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0, 0, 0)),
        ("-x+1/2, -y, z+1/2", ((-1, 0, 0), (0, -1, 0), (0, 0, 1)), ("1/2", 0, "1/2")),
        ("1/2+x, 1/2-y, -z", ((1, 0, 0), (0, -1, 0), (0, 0, -1)), ("1/2", "1/2", 0)),
        ("x-y, x, z+1/6", ((1, -1, 0), (1, 0, 0), (0, 0, 1)), (0, 0, "1/6")),
        ("'-X, Y+0.5, -Z'", ((-1, 0, 0), (0, 1, 0), (0, 0, -1)), (0, "1/2", 0)),
    ],
)
def test_parse(text: str, rotation: object, translation: tuple[object, ...]) -> None:
    op = SymmetryOperator.parse(text)
    assert op.rotation == rotation
    assert op.translation == tuple(Fraction(str(t)) for t in translation)


def test_apply_and_identity() -> None:
    op = SymmetryOperator.parse("-x+1/2, -y, z+1/2")
    assert op.apply((0.1, 0.2, 0.3)) == pytest.approx((0.4, -0.2, 0.8))
    assert not op.is_identity
    assert SymmetryOperator.parse("x, y, z").is_identity
    assert SymmetryOperator.parse("x+1, y, z").is_identity  # a lattice repeat of x,y,z


def test_esd_follows_the_rotation_as_in_the_full_program() -> None:
    # |R . sigma| row by row: signs drop out, a permutation swaps the e.s.d.'s
    assert SymmetryOperator.parse("-y, x, -z").apply_esd((0.1, 0.2, 0.3)) == pytest.approx(
        (0.2, 0.1, 0.3)
    )


@pytest.mark.parametrize("text", ["x, y, z", "-x+1/2, -y, z+1/2", "x-y, x, z+1/6"])
def test_str_round_trip(text: str) -> None:
    op = SymmetryOperator.parse(text)
    assert SymmetryOperator.parse(str(op)) == op


@pytest.mark.parametrize(
    "text",
    ["x, y", "x, x, z", "2x, y, z", "x, y, q", "x, , z", "x, y, z+1/0"],
)
def test_invalid_operators_are_refused(text: str) -> None:
    with pytest.raises(InvalidStructureError):
        SymmetryOperator.parse(text)
