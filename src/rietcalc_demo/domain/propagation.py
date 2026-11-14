"""First-order propagation of independent errors.

For a result ``f(p1, ..., pn)`` computed from parameters with e.s.d.'s
``s1, ..., sn`` that are assumed independent,

    sigma(f)^2 = sum_i (df/dp_i * s_i)^2

This is the rule the original FORTRAN program and the full RietCalc use for every
distance.  They take the derivatives by forward differences in single precision,
which leaves visible noise in the last digit; here the derivatives are central
differences in double precision, so the method is the same and the noise is gone.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

#: Relative step of the central difference.  The rounding error of a central
#: difference grows as eps/h and its truncation error as h^2, so the total error is
#: smallest near the cube root of the double-precision epsilon, about 6e-6.
RELATIVE_STEP = 6e-6


def propagate(
    function: Callable[[Sequence[float]], float],
    values: Sequence[float],
    esds: Sequence[float],
) -> float:
    """The e.s.d. of ``function(values)`` for independent errors ``esds``."""
    if len(values) != len(esds):
        raise ValueError("values and esds differ in length")
    point = list(values)
    total = 0.0
    for i, (value, esd) in enumerate(zip(values, esds, strict=True)):
        if esd == 0.0:
            continue  # a fixed parameter adds nothing; skip two evaluations
        step = RELATIVE_STEP * max(abs(value), 1.0)
        point[i] = value + step
        upper = function(point)
        point[i] = value - step
        lower = function(point)
        point[i] = value
        derivative = (upper - lower) / (2.0 * step)
        total += (derivative * esd) ** 2
    return math.sqrt(total)
