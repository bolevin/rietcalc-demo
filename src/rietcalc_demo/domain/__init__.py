"""The calculation itself: pure functions and immutable values.

Nothing in this package reads a file, opens a window or imports anything outside
the standard library.  The rule is checked in CI (see ``[tool.importlinter]``).
"""

from rietcalc_demo.domain.analysis import MAX_RANGE, DistanceAnalysis, DistanceSettings, analyse
from rietcalc_demo.domain.bonds import BondGroup, Coordination
from rietcalc_demo.domain.cell import UnitCell
from rietcalc_demo.domain.distances import Contact
from rietcalc_demo.domain.errors import DomainError, InvalidSettingsError, InvalidStructureError
from rietcalc_demo.domain.expansion import Image, expand, multiplicities
from rietcalc_demo.domain.histogram import Bin, histogram
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.notation import format_measured, parse_measured
from rietcalc_demo.domain.structure import Atom, Structure
from rietcalc_demo.domain.symmetry import SymmetryOperator

__all__ = [
    "MAX_RANGE",
    "Atom",
    "Bin",
    "BondGroup",
    "Contact",
    "Coordination",
    "DistanceAnalysis",
    "DistanceSettings",
    "DomainError",
    "Image",
    "InvalidSettingsError",
    "InvalidStructureError",
    "Measured",
    "Structure",
    "SymmetryOperator",
    "UnitCell",
    "analyse",
    "expand",
    "format_measured",
    "histogram",
    "multiplicities",
    "parse_measured",
]
