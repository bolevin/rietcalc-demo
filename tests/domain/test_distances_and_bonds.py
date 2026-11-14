"""Distances, their e.s.d.'s and the coordination table, checked by hand."""

from __future__ import annotations

import math

import pytest

from conftest import IDENTITY, cubic_cell
from rietcalc_demo.domain import (
    Atom,
    DistanceSettings,
    InvalidSettingsError,
    Measured,
    Structure,
    analyse,
)


def test_primitive_cubic_shells(primitive_cubic: Structure) -> None:
    result = analyse(primitive_cubic, DistanceSettings(0.0, 6.0))
    (x1,) = result.coordination
    shells = [(round(g.distance.value, 6), g.multiplicity) for g in x1.groups]
    # 6 neighbours along the axes, 12 along the face diagonals; the body diagonal
    # (4 * sqrt 3 = 6.93 A) is already outside R max
    assert shells == [(4.0, 6), (round(4 * math.sqrt(2), 6), 12)]
    assert x1.number == 18


def test_esd_of_a_lattice_repeat_is_the_esd_of_the_cell(primitive_cubic: Structure) -> None:
    # d = a * |n| with the coordinates fixed, so sigma(d) = sigma(a) * |n|, the
    # same 0.002 A for the neighbour at one cell edge - but with a, b, c refined
    # independently the face diagonal mixes two of them:
    # d = sqrt(a^2 + b^2) -> sigma = sqrt((a sa)^2 + (b sb)^2) / d = 0.002 * a*sqrt2 / d
    result = analyse(primitive_cubic, DistanceSettings(0.0, 6.0))
    first, second = result.coordination[0].groups
    assert first.distance.esd == pytest.approx(0.002, rel=1e-6)
    assert second.distance.esd == pytest.approx(0.002, rel=1e-6)


def test_range_limits_are_r_min_inclusive_r_max_exclusive(primitive_cubic: Structure) -> None:
    assert len(analyse(primitive_cubic, DistanceSettings(4.0, 4.5)).contacts) == 6
    assert len(analyse(primitive_cubic, DistanceSettings(0.0, 4.0)).contacts) == 0


def test_sample_titanium_octahedron(sample: Structure) -> None:
    result = analyse(sample, DistanceSettings(0.0, 2.2))
    ti = next(c for c in result.coordination if c.source == "Ti1")
    # Ti on an inversion centre: six oxygens, three symmetry-unique Ti-O bonds
    assert ti.number == 6
    assert [g.multiplicity for g in ti.groups] == [2, 2, 2]
    assert {g.target for g in ti.groups} == {"O1", "O2"}
    assert all(1.94 < g.distance.value < 1.97 for g in ti.groups)


def test_a_bond_reads_the_same_from_both_ends(sample: Structure) -> None:
    """Ca1-O2 and O2-Ca1 are one bond: same distance, same e.s.d.

    The full program, in single precision, prints these two as 2.37797 and 2.37798;
    in double precision there is nothing left to differ.
    """
    result = analyse(sample, DistanceSettings())
    ca_o2 = {
        round(g.distance.value, 10): g.distance.esd
        for c in result.coordination
        if c.source == "Ca1"
        for g in c.groups
        if g.target == "O2"
    }
    o2_ca = {
        round(g.distance.value, 10): g.distance.esd
        for c in result.coordination
        if c.source == "O2"
        for g in c.groups
        if g.target == "Ca1"
    }
    assert ca_o2.keys() == o2_ca.keys()
    for d, esd in ca_o2.items():
        assert o2_ca[d] == pytest.approx(esd, rel=1e-9)


@pytest.mark.parametrize(("r_min", "r_max"), [(-1.0, 3.0), (3.0, 3.0), (2.0, 1.0), (0.0, 9.0)])
def test_settings_out_of_range_are_refused(r_min: float, r_max: float) -> None:
    with pytest.raises(InvalidSettingsError):
        DistanceSettings(r_min, r_max)


def test_equal_distances_to_different_atoms_stay_separate_bonds() -> None:
    """A at the origin; B and C each half a cell away, along x and along y.

    Both neighbours sit at exactly 2 A, two of each - but A-B and A-C are still
    two different bonds at one length, and the table must say so.
    """
    structure = Structure(
        "two neighbours, one distance",
        cubic_cell(4.0),
        (IDENTITY,),
        (
            Atom("A", "X", Measured(0.0), Measured(0.0), Measured(0.0)),
            Atom("B", "X", Measured(0.5), Measured(0.0), Measured(0.0)),
            Atom("C", "X", Measured(0.0), Measured(0.5), Measured(0.0)),
        ),
    )
    a = analyse(structure, DistanceSettings(0.0, 2.5)).coordination[0]
    assert [(g.target, round(g.distance.value, 6), g.multiplicity) for g in a.groups] == [
        ("B", 2.0, 2),
        ("C", 2.0, 2),
    ]
