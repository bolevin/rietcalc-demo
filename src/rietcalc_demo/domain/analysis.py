"""The one calculation the demo offers, end to end."""

from __future__ import annotations

import math
from dataclasses import dataclass

from rietcalc_demo.domain.bonds import Coordination, coordination
from rietcalc_demo.domain.distances import Contact, contacts
from rietcalc_demo.domain.errors import InvalidSettingsError
from rietcalc_demo.domain.expansion import multiplicities
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.structure import Structure

#: Upper limit of the distance range.  Beyond the first few coordination shells the
#: bond table stops being readable; the full program goes further for its radial
#: distribution functions, which the demo does not include.
MAX_RANGE = 8.0


@dataclass(frozen=True, slots=True)
class DistanceSettings:
    r_min: float = 0.0
    r_max: float = 3.2

    def __post_init__(self) -> None:
        if not (math.isfinite(self.r_min) and math.isfinite(self.r_max)):
            raise InvalidSettingsError("R min and R max must be numbers.")
        if self.r_min < 0:
            raise InvalidSettingsError("R min cannot be negative.")
        if self.r_max <= self.r_min:
            raise InvalidSettingsError("R max must be greater than R min.")
        if self.r_max > MAX_RANGE:
            raise InvalidSettingsError(f"R max is limited to {MAX_RANGE:g} A in the demo.")


@dataclass(frozen=True, slots=True)
class DistanceAnalysis:
    structure: Structure
    settings: DistanceSettings
    volume: Measured
    multiplicities: tuple[int, ...]  # per independent atom
    contacts: tuple[Contact, ...]
    coordination: tuple[Coordination, ...]

    @property
    def atoms_in_cell(self) -> int:
        return sum(self.multiplicities)


def analyse(structure: Structure, settings: DistanceSettings) -> DistanceAnalysis:
    found = contacts(structure, settings.r_min, settings.r_max)
    return DistanceAnalysis(
        structure=structure,
        settings=settings,
        volume=structure.cell.volume,
        multiplicities=multiplicities(structure),
        contacts=found,
        coordination=coordination(structure, found),
    )
