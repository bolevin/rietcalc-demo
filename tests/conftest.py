from __future__ import annotations

import os
from fractions import Fraction
from pathlib import Path

import pytest

# the window tests need no screen; must be set before Qt is imported
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rietcalc_demo.adapters.cif import CifReader
from rietcalc_demo.domain import Atom, Measured, Structure, SymmetryOperator, UnitCell
from rietcalc_demo.main import data_path

IDENTITY = SymmetryOperator(((1, 0, 0), (0, 1, 0), (0, 0, 1)), (Fraction(0),) * 3)


@pytest.fixture(scope="session")
def sample_path() -> Path:
    return data_path("sample_structure.cif")


@pytest.fixture(scope="session")
def sample(sample_path: Path) -> Structure:
    return CifReader().read(sample_path)


def cubic_cell(a: float = 4.0, esd: float = 0.0) -> UnitCell:
    return UnitCell(
        Measured(a, esd),
        Measured(a, esd),
        Measured(a, esd),
        Measured(90.0),
        Measured(90.0),
        Measured(90.0),
    )


@pytest.fixture
def primitive_cubic() -> Structure:
    """One atom at the origin of a 4 A cube: every distance can be done by hand.

    Nearest neighbours: 6 at a = 4; then 12 at a*sqrt(2); then 8 at a*sqrt(3).
    """
    return Structure(
        title="primitive cubic",
        cell=cubic_cell(4.0, 0.002),
        operators=(IDENTITY,),
        atoms=(Atom("X1", "X", Measured(0.0), Measured(0.0), Measured(0.0)),),
    )
