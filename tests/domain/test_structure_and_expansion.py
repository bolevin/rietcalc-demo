"""Structure validation and the symmetry expansion of the asymmetric unit."""

from __future__ import annotations

import pytest

from conftest import IDENTITY, cubic_cell
from rietcalc_demo.domain import (
    Atom,
    InvalidStructureError,
    Measured,
    Structure,
    SymmetryOperator,
    expand,
    multiplicities,
)


def atom(label: str, x: float = 0.1, y: float = 0.2, z: float = 0.3) -> Atom:
    return Atom(label, "O", Measured(x), Measured(y), Measured(z))


def test_sample_multiplicities_follow_the_site_symmetry(sample: Structure) -> None:
    # Pnma has 8 operators: a general position (O2, 8d) has 8 images, the sites on
    # the mirror plane (Ca1, O1, 4c) and on the inversion centre (Ti1, 4b) have 4
    assert multiplicities(sample) == (4, 4, 4, 8)
    assert len(expand(sample)) == 20


def test_images_are_folded_into_the_cell_and_distinct(sample: Structure) -> None:
    images = expand(sample)
    assert all(0.0 <= c < 1.0 for image in images for c in image.position)
    positions = [tuple(round(c, 6) for c in image.position) for image in images]
    assert len(positions) == len(set(positions))


def test_an_atom_on_a_mirror_keeps_its_y() -> None:
    mirror = SymmetryOperator.parse("x, -y+1/2, z")
    structure = Structure("m", cubic_cell(), (IDENTITY, mirror), (atom("O1", y=0.25),))
    assert multiplicities(structure) == (1,)  # the mirror maps the atom onto itself


@pytest.mark.parametrize(
    ("operators", "atoms", "message"),
    [
        ((IDENTITY,), (), "no atoms"),
        ((), (atom("O1"),), "no symmetry operators"),
        ((SymmetryOperator.parse("-x, -y, -z"),), (atom("O1"),), "x, y, z"),
        ((IDENTITY,), (atom("O1"), atom("O1")), "Duplicate"),
    ],
)
def test_inconsistent_structures_are_refused(
    operators: tuple[SymmetryOperator, ...], atoms: tuple[Atom, ...], message: str
) -> None:
    with pytest.raises(InvalidStructureError, match=message):
        Structure("bad", cubic_cell(), operators, atoms)


@pytest.mark.parametrize("occupancy", [0.0, -0.5, 1.5])
def test_occupancy_must_lie_in_zero_one(occupancy: float) -> None:
    with pytest.raises(InvalidStructureError, match="occupancy"):
        Atom("O1", "O", Measured(0), Measured(0), Measured(0), Measured(occupancy))


def test_negative_esd_is_refused() -> None:
    with pytest.raises(InvalidStructureError):
        Measured(1.0, -0.1)
