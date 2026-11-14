"""Properties that must hold for every input, not only for the examples.

Hypothesis generates the structures; each test states a law of geometry or of
error propagation that a correct implementation cannot break.
"""

from __future__ import annotations

import math
import re

from hypothesis import given, settings
from hypothesis import strategies as st

from conftest import IDENTITY
from rietcalc_demo.domain import (
    Atom,
    DistanceSettings,
    Measured,
    Structure,
    SymmetryOperator,
    UnitCell,
    analyse,
    format_measured,
    parse_measured,
)
from rietcalc_demo.domain.cell import metric_distance

INVERSION = SymmetryOperator.parse("-x, -y, -z")

lengths = st.floats(3.0, 9.0)
angles = st.floats(75.0, 110.0)
fractions = st.floats(0.0, 0.999)


@st.composite
def cells(draw: st.DrawFn) -> UnitCell:
    a, b, c = draw(lengths), draw(lengths), draw(lengths)
    # Angles between 75 and 110 degrees always close a volume: no draw is refused.
    alpha, beta, gamma = draw(angles), draw(angles), draw(angles)
    return UnitCell(*(Measured(v, 0.001) for v in (a, b, c)), *map(Measured, (alpha, beta, gamma)))


@st.composite
def structures(draw: st.DrawFn) -> Structure:
    n = draw(st.integers(1, 3))
    atoms = tuple(
        Atom(
            f"A{i}",
            "X",
            Measured(draw(fractions), 0.001),
            Measured(draw(fractions), 0.001),
            Measured(draw(fractions), 0.001),
        )
        for i in range(n)
    )
    return Structure("random", draw(cells()), (IDENTITY, INVERSION), atoms)


@given(cells(), st.tuples(*[st.floats(-1, 1)] * 3))
def test_distance_is_symmetric(cell: UnitCell, delta: tuple[float, float, float]) -> None:
    forward = metric_distance(cell.values, delta)
    backward = metric_distance(cell.values, tuple(-d for d in delta))
    assert math.isclose(forward, backward, rel_tol=1e-12, abs_tol=1e-12)


@settings(max_examples=40, deadline=None)
@given(structures(), st.floats(1.1, 2.0))
def test_scaling_the_cell_scales_every_distance(structure: Structure, k: float) -> None:
    """Multiply a, b, c by k: the same contacts, every distance times k."""
    cell = structure.cell
    scaled = Structure(
        structure.title,
        UnitCell(
            Measured(cell.a.value * k, cell.a.esd),
            Measured(cell.b.value * k, cell.b.esd),
            Measured(cell.c.value * k, cell.c.esd),
            cell.alpha,
            cell.beta,
            cell.gamma,
        ),
        structure.operators,
        structure.atoms,
    )
    base = analyse(structure, DistanceSettings(0.0, 4.0))
    grown = analyse(scaled, DistanceSettings(0.0, 4.0 * k))
    assert sorted(round(c.distance.value * k, 6) for c in base.contacts) == sorted(
        round(c.distance.value, 6) for c in grown.contacts
    )


@settings(max_examples=40, deadline=None)
@given(structures(), st.tuples(fractions, fractions, fractions))
def test_moving_the_origin_changes_no_distance(
    structure: Structure, shift: tuple[float, float, float]
) -> None:
    """Only differences of positions matter, in P1 at least (no operator but x,y,z)."""
    p1 = Structure(structure.title, structure.cell, (IDENTITY,), structure.atoms)
    moved = Structure(
        p1.title,
        p1.cell,
        p1.operators,
        tuple(
            Atom(
                a.label,
                a.element,
                Measured(a.x.value + shift[0], a.x.esd),
                Measured(a.y.value + shift[1], a.y.esd),
                Measured(a.z.value + shift[2], a.z.esd),
            )
            for a in p1.atoms
        ),
    )
    assert _inside(p1) == _inside(moved)


def _inside(structure: Structure) -> list[float]:
    """Distances clear of the R max edge, where rounding may tip one in or out."""
    r_max = DistanceSettings().r_max
    found = (c.distance.value for c in analyse(structure, DistanceSettings()).contacts)
    return sorted(round(d, 6) for d in found if d < r_max - 1e-6)


@settings(max_examples=40, deadline=None)
@given(structures())
def test_esd_is_positive_when_something_is_refined(structure: Structure) -> None:
    for contact in analyse(structure, DistanceSettings()).contacts:
        assert contact.distance.esd > 0


_NOTATION = re.compile(r"^-?\d+(\.\d+)?\((\d+)\)$")


@given(st.floats(-1000, 1000), st.floats(1e-6, 1.0))
def test_notation_keeps_two_to_nineteen_in_the_esd(value: float, esd: float) -> None:
    text = format_measured(value, esd)
    match = _NOTATION.match(text)
    assert match, text
    assert 2 <= int(match.group(2)) <= 19
    parsed_value, parsed_esd = parse_measured(text)
    last_digit = 10.0 ** -(len(match.group(1)) - 1 if match.group(1) else 0)
    # the value is rounded to its last digit, the e.s.d. to one or two digits
    assert abs(parsed_value - value) <= last_digit / 2 + 1e-9
    assert abs(parsed_esd - esd) <= last_digit / 2 + 1e-12
