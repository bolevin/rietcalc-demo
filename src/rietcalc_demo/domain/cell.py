"""The unit cell: its metric, its volume and distances between fractional positions."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from rietcalc_demo.domain.errors import InvalidStructureError
from rietcalc_demo.domain.measured import Measured
from rietcalc_demo.domain.propagation import propagate

Vector = tuple[float, float, float]


def metric_distance(cell: Sequence[float], delta: Sequence[float]) -> float:
    """|delta| in Angstrom for fractional ``delta`` in a cell (a, b, c, alpha, beta, gamma).

    d^2 = a^2 dx^2 + b^2 dy^2 + c^2 dz^2
          + 2ab cos(gamma) dx dy + 2ac cos(beta) dx dz + 2bc cos(alpha) dy dz

    Angles in degrees.  This one formula is the whole geometry of the program; it
    takes plain numbers so that the error propagation can perturb every one of them.
    """
    a, b, c, alpha, beta, gamma = cell
    dx, dy, dz = delta
    cos_a = math.cos(math.radians(alpha))
    cos_b = math.cos(math.radians(beta))
    cos_g = math.cos(math.radians(gamma))
    square = (
        a * a * dx * dx
        + b * b * dy * dy
        + c * c * dz * dz
        + 2.0 * a * b * cos_g * dx * dy
        + 2.0 * a * c * cos_b * dx * dz
        + 2.0 * b * c * cos_a * dy * dz
    )
    return math.sqrt(max(square, 0.0))


def _angle_factor(alpha: float, beta: float, gamma: float) -> float:
    """V / (abc): the volume of a cell with unit edges, between 0 and 1."""
    ca, cb, cg = (math.cos(math.radians(x)) for x in (alpha, beta, gamma))
    return math.sqrt(max(1.0 - ca * ca - cb * cb - cg * cg + 2.0 * ca * cb * cg, 0.0))


def _volume(cell: Sequence[float]) -> float:
    a, b, c, alpha, beta, gamma = cell
    return a * b * c * _angle_factor(alpha, beta, gamma)


@dataclass(frozen=True, slots=True)
class UnitCell:
    """Lengths in Angstrom, angles in degrees, each with its e.s.d."""

    a: Measured
    b: Measured
    c: Measured
    alpha: Measured
    beta: Measured
    gamma: Measured

    def __post_init__(self) -> None:
        for name in ("a", "b", "c"):
            if getattr(self, name).value <= 0:
                raise InvalidStructureError(f"Cell length {name} must be positive.")
        for name in ("alpha", "beta", "gamma"):
            if not 0 < getattr(self, name).value < 180:
                raise InvalidStructureError(f"Cell angle {name} must lie between 0 and 180.")
        # Judged without the lengths: 120/120/120 closes no volume, but rounding
        # leaves about 1e-8 of it, and a long cell would multiply that up.
        if _angle_factor(self.alpha.value, self.beta.value, self.gamma.value) < 1e-3:
            raise InvalidStructureError("The cell angles describe no volume.")

    @property
    def parameters(self) -> tuple[Measured, ...]:
        return (self.a, self.b, self.c, self.alpha, self.beta, self.gamma)

    @property
    def values(self) -> tuple[float, ...]:
        return tuple(p.value for p in self.parameters)

    @property
    def esds(self) -> tuple[float, ...]:
        return tuple(p.esd for p in self.parameters)

    @property
    def volume(self) -> Measured:
        return Measured(_volume(self.values), propagate(_volume, self.values, self.esds))

    def reciprocal_lengths(self) -> Vector:
        """a*, b*, c* in 1/Angstrom: bound the lattice translations a search must try.

        A fractional difference along x can only be shorter than R if |dx| <= R * a*,
        so these three numbers decide how many neighbouring cells to visit.
        """
        a, b, c, alpha, beta, gamma = self.values
        sa, sb, sg = (math.sin(math.radians(x)) for x in (alpha, beta, gamma))
        v = _volume(self.values)
        return (b * c * sa / v, a * c * sb / v, a * b * sg / v)

    def distance(self, p: Vector, q: Vector) -> float:
        return metric_distance(self.values, (q[0] - p[0], q[1] - p[1], q[2] - p[2]))
