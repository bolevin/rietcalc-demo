"""A measured quantity: a value and its estimated standard deviation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from rietcalc_demo.domain.errors import InvalidStructureError


@dataclass(frozen=True, slots=True)
class Measured:
    """``value`` with e.s.d. ``esd``.

    An e.s.d. of zero means "not refined": a coordinate fixed by symmetry, or a
    cell angle that the lattice type forces to 90 degrees.  It is a real value
    in the error propagation, not a missing one.
    """

    value: float
    esd: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise InvalidStructureError(f"Value {self.value!r} is not a finite number.")
        if not math.isfinite(self.esd) or self.esd < 0:
            raise InvalidStructureError(f"e.s.d. {self.esd!r} must be zero or positive.")

    @property
    def refined(self) -> bool:
        return self.esd > 0
