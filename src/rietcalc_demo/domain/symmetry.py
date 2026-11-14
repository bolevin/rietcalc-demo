"""Space-group operators in the notation every CIF uses: ``-x+1/2, y, z+1/2``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from rietcalc_demo.domain.errors import InvalidStructureError

Vector = tuple[float, float, float]
Matrix = tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]

_AXES = "xyz"
_TERM = re.compile(r"[+-]?[^+-]+")


def _parse_component(text: str) -> tuple[tuple[int, int, int], Fraction]:
    """One coordinate of an operator, e.g. ``-x+1/2`` -> ((-1, 0, 0), 1/2)."""
    row = [0, 0, 0]
    shift = Fraction(0)
    compact = text.replace(" ", "").lower()
    if not compact:
        raise InvalidStructureError("An operator has an empty coordinate.")
    for term in _TERM.findall(compact):
        sign = -1 if term.startswith("-") else 1
        body = term.lstrip("+-")
        if body in _AXES:
            row[_AXES.index(body)] += sign
        else:
            try:
                shift += sign * Fraction(body)
            except (ValueError, ZeroDivisionError):
                raise InvalidStructureError(f"Cannot read {text!r} as an operator term.") from None
    return (row[0], row[1], row[2]), shift


@dataclass(frozen=True, slots=True)
class SymmetryOperator:
    """``x' = R x + t``: an integer rotation part and an exact fractional translation."""

    rotation: Matrix
    translation: tuple[Fraction, Fraction, Fraction]

    def __post_init__(self) -> None:
        det = _determinant(self.rotation)
        if det not in (1, -1):
            raise InvalidStructureError(
                f"Operator {self} is not a crystallographic operation (det = {det})."
            )

    @classmethod
    def parse(cls, text: str) -> SymmetryOperator:
        parts = text.strip().strip("'\"").split(",")
        if len(parts) != 3:
            raise InvalidStructureError(f"Operator {text!r} does not have three coordinates.")
        rows, shifts = zip(*(_parse_component(p) for p in parts), strict=True)
        return cls((rows[0], rows[1], rows[2]), (shifts[0], shifts[1], shifts[2]))

    @property
    def is_identity(self) -> bool:
        return self.rotation == ((1, 0, 0), (0, 1, 0), (0, 0, 1)) and all(
            t % 1 == 0 for t in self.translation
        )

    def apply(self, position: Vector) -> Vector:
        r, t = self.rotation, self.translation
        return (
            r[0][0] * position[0] + r[0][1] * position[1] + r[0][2] * position[2] + float(t[0]),
            r[1][0] * position[0] + r[1][1] * position[1] + r[1][2] * position[2] + float(t[1]),
            r[2][0] * position[0] + r[2][1] * position[1] + r[2][2] * position[2] + float(t[2]),
        )

    def apply_esd(self, esd: Vector) -> Vector:
        """e.s.d. of the transformed coordinates: ``|R . sigma|`` row by row.

        This is how the full program carries the coordinate e.s.d.'s of an atom over
        to its symmetry images, and the demo keeps the same model so that the two
        agree.  For the axis-permuting and sign-changing operators of orthorhombic
        and higher-symmetry groups it is exact; ADR 0004 records the simplification
        it makes for operators such as ``x-y``.
        """
        r = self.rotation
        return (
            abs(r[0][0] * esd[0] + r[0][1] * esd[1] + r[0][2] * esd[2]),
            abs(r[1][0] * esd[0] + r[1][1] * esd[1] + r[1][2] * esd[2]),
            abs(r[2][0] * esd[0] + r[2][1] * esd[1] + r[2][2] * esd[2]),
        )

    def __str__(self) -> str:
        return ", ".join(
            _format_component(row, t)
            for row, t in zip(self.rotation, self.translation, strict=True)
        )


def _format_component(row: tuple[int, int, int], shift: Fraction) -> str:
    out = ""
    for coefficient, axis in zip(row, _AXES, strict=True):
        if coefficient:
            sign = "-" if coefficient < 0 else ("+" if out else "")
            out += sign + ("" if abs(coefficient) == 1 else str(abs(coefficient))) + axis
    if shift:
        out += ("+" if shift > 0 and out else "") + str(shift)
    return out or "0"


def _determinant(m: Matrix) -> int:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )
