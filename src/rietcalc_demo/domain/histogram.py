"""The distance histogram drawn above the bond table."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Bin:
    low: float
    high: float
    count: int


def histogram(values: Iterable[float], width: float, low: float = 0.0) -> tuple[Bin, ...]:
    """Counts in bins ``[low + k*width, low + (k+1)*width)``.

    The bins run from the first non-empty one to the last; empty bins in between
    are kept, so the result is a contiguous axis.
    """
    if not (math.isfinite(width) and width > 0):
        raise ValueError("The bin width must be a positive number.")
    counts: dict[int, int] = {}
    for value in values:
        if value < low:
            continue
        k = math.floor((value - low) / width)
        counts[k] = counts.get(k, 0) + 1
    if not counts:
        return ()
    first, last = min(counts), max(counts)
    return tuple(
        Bin(low + k * width, low + (k + 1) * width, counts.get(k, 0))
        for k in range(first, last + 1)
    )
