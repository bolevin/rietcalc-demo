"""A crystal structure: the unit cell, the space-group operators and the atoms."""

from __future__ import annotations

from dataclasses import dataclass

from rietcalc_demo.domain.cell import UnitCell, Vector
from rietcalc_demo.domain.errors import InvalidStructureError
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.symmetry import SymmetryOperator

#: The default occupancy: a site that is fully and exactly occupied.
FULL = Measured(1.0)


@dataclass(frozen=True, slots=True)
class Atom:
    """One independent (asymmetric-unit) atom with fractional coordinates."""

    label: str
    element: str
    x: Measured
    y: Measured
    z: Measured
    occupancy: Measured = FULL

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise InvalidStructureError("An atom has an empty label.")
        if not self.element.strip():
            raise InvalidStructureError(f"Atom {self.label} has no element.")
        if not 0 < self.occupancy.value <= 1:
            raise InvalidStructureError(
                f"Atom {self.label}: occupancy {self.occupancy.value} is outside (0, 1]."
            )

    @property
    def position(self) -> Vector:
        return (self.x.value, self.y.value, self.z.value)

    @property
    def position_esd(self) -> Vector:
        return (self.x.esd, self.y.esd, self.z.esd)


@dataclass(frozen=True, slots=True)
class Structure:
    """The asymmetric unit and everything needed to build the full crystal from it."""

    title: str
    cell: UnitCell
    operators: tuple[SymmetryOperator, ...]
    atoms: tuple[Atom, ...]
    space_group: str = ""  # Hermann-Mauguin symbol, for display only

    def __post_init__(self) -> None:
        if not self.atoms:
            raise InvalidStructureError("The structure has no atoms.")
        if not self.operators:
            raise InvalidStructureError("The structure has no symmetry operators.")
        if not any(op.is_identity for op in self.operators):
            # without x,y,z the list is not a group: the atoms would not even map to
            # themselves, and every multiplicity would be wrong
            raise InvalidStructureError("The symmetry operators do not include x, y, z.")
        labels = [atom.label for atom in self.atoms]
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            raise InvalidStructureError(f"Duplicate atom labels: {', '.join(duplicates)}.")

    def atom(self, label: str) -> Atom:
        for atom in self.atoms:
            if atom.label == label:
                return atom
        raise KeyError(label)
