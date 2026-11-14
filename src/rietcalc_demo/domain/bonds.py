"""Coordination: the symmetry-unique bonds of each independent atom.

A Ti on an inversion centre has six Ti-O contacts, but only three distinct ones:
each distance occurs twice.  Grouping contacts by neighbour and distance turns a
long list into the table a crystallographer reads - neighbour, distance,
multiplicity - and the multiplicities add up to the coordination number.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from rietcalc_demo.domain.distances import Contact
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.structure import Structure

#: Distances closer than this (Angstrom) to the same neighbour are one bond type.
SAME_BOND = 1e-3


@dataclass(frozen=True, slots=True)
class BondGroup:
    target: str  # label of the neighbour's independent atom
    distance: Measured
    multiplicity: int


@dataclass(frozen=True, slots=True)
class Coordination:
    source: str
    number: int  # coordination number = sum of the multiplicities
    groups: tuple[BondGroup, ...]  # by increasing distance


@dataclass(slots=True)
class _Tally:
    """A bond type while the contacts are being counted (the only mutable value here)."""

    target: int
    distance: Measured
    count: int = 1

    def matches(self, contact: Contact) -> bool:
        return (
            self.target == contact.target
            and abs(self.distance.value - contact.distance.value) <= SAME_BOND
        )


def coordination(structure: Structure, found: Iterable[Contact]) -> tuple[Coordination, ...]:
    """Group the contacts of every independent atom into symmetry-unique bonds."""
    tallies: dict[int, list[_Tally]] = {i: [] for i in range(len(structure.atoms))}
    for contact in found:
        bucket = tallies[contact.source]
        match = next((t for t in bucket if t.matches(contact)), None)
        if match is None:
            bucket.append(_Tally(contact.target, contact.distance))
        else:
            match.count += 1
    return tuple(
        _finish(structure, source_index, bucket) for source_index, bucket in tallies.items()
    )


def _finish(structure: Structure, source_index: int, bucket: list[_Tally]) -> Coordination:
    groups = sorted(
        (BondGroup(structure.atoms[t.target].label, t.distance, t.count) for t in bucket),
        key=lambda g: (g.distance.value, g.target),
    )
    return Coordination(
        source=structure.atoms[source_index].label,
        number=sum(g.multiplicity for g in groups),
        groups=tuple(groups),
    )
