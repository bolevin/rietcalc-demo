"""Interatomic distances with their e.s.d.'s.

For each independent atom (the *source*) every atom of the crystal within the
requested range is found - including the lattice repeats of the source itself -
and each distance gets an e.s.d. from twelve independent parameters: the six cell
parameters, the three coordinates of the source and the three of the neighbour.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass

from rietcalc_demo.domain.cell import Vector, metric_distance
from rietcalc_demo.domain.expansion import Image, expand
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.propagation import propagate
from rietcalc_demo.domain.structure import Structure

#: A neighbour closer than this is the source atom itself.
SELF = 1e-4


@dataclass(frozen=True, slots=True)
class Contact:
    """One source-neighbour pair."""

    source: int  # index into Structure.atoms
    target: int  # independent atom the neighbour is a copy of
    distance: Measured
    operator: int  # operator that produced the neighbour
    translation: tuple[int, int, int]  # lattice repeat added to it


def _distance(parameters: Sequence[float]) -> float:
    """Distance from the twelve parameters: cell (6), source xyz (3), neighbour xyz (3)."""
    return metric_distance(
        parameters[0:6],
        (
            parameters[9] - parameters[6],
            parameters[10] - parameters[7],
            parameters[11] - parameters[8],
        ),
    )


def _translations(
    source: Vector, image: Vector, reach: Vector
) -> itertools.product[tuple[int, ...]]:
    """Every lattice repeat of ``image`` that can lie within the range of ``source``."""
    ranges = (
        range(math.ceil(s - p - r), math.floor(s - p + r) + 1)
        for s, p, r in zip(source, image, reach, strict=True)
    )
    return itertools.product(*ranges)


def contacts(structure: Structure, r_min: float, r_max: float) -> tuple[Contact, ...]:
    """All pairs with ``r_min <= d < r_max``, sorted by source, then distance."""
    cell = structure.cell
    reach = tuple(r_max * length for length in cell.reciprocal_lengths())
    images: tuple[Image, ...] = expand(structure)
    found: list[Contact] = []
    for source_index, source in enumerate(structure.atoms):
        start = source.position
        for image in images:
            for n in _translations(start, image.position, (reach[0], reach[1], reach[2])):
                end = (image.position[0] + n[0], image.position[1] + n[1], image.position[2] + n[2])
                d = cell.distance(start, end)
                if d < SELF or d < r_min or d >= r_max:
                    continue
                esd = propagate(
                    _distance,
                    (*cell.values, *start, *end),
                    (*cell.esds, *source.position_esd, *image.esd),
                )
                found.append(
                    Contact(
                        source=source_index,
                        target=image.atom,
                        distance=Measured(d, esd),
                        operator=image.operator,
                        translation=(n[0], n[1], n[2]),
                    )
                )
    found.sort(key=lambda c: (c.source, c.distance.value, c.target))
    return tuple(found)
