"""The crystallographic way to write a value with its e.s.d.: ``1.9489(10)``.

The e.s.d. is written as an integer in units of the last digit of the value, and
the value is rounded to that digit.  How many digits the e.s.d. keeps follows the
convention of the crystallographic journals, the "rule of 19": two digits when
they form a number from 10 to 19, otherwise one.  So 0.0013 is written (13) but
0.0023 is written (2), and the value is never quoted more finely than its
uncertainty supports.

(The full RietCalc instead starts from a fixed precision and lets the e.s.d. keep up
to two digits, 10 to 99; ADR 0005 explains why the demo follows the journals.)
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

#: Decimals shown for a value with no e.s.d. (trailing zeros are dropped).
PLAIN_DECIMALS = 6


def _round(number: Decimal, decimals: int) -> Decimal:
    return number.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def format_measured(value: float, esd: float) -> str:
    """``value(esd)`` by the rule of 19; a bare value when ``esd`` is zero."""
    if not math.isfinite(value):
        return str(value)
    v = Decimal(repr(float(value)))
    if not (math.isfinite(esd) and esd > 0):
        text = f"{_round(v, PLAIN_DECIMALS):f}"
        text = text.rstrip("0").rstrip(".") if "." in text else text
        return "0" if text in ("", "-0") else text

    e = Decimal(repr(float(esd)))
    leading = -e.adjusted()  # decimals that put the first significant digit last
    two_digits = int(_round(e.scaleb(leading + 1), 0))  # 10 .. 100
    if two_digits <= 19:
        decimals, digits = leading + 1, two_digits
    else:
        decimals, digits = leading, int(_round(e.scaleb(leading), 0))  # 2 .. 10

    if decimals < 0:
        # an e.s.d. of 20 or more in the units place: round the value to tens,
        # hundreds... and state the e.s.d. in the same units, as the journals do
        scale = 10 ** (-decimals)
        return f"{int(_round(v.scaleb(decimals), 0)) * scale}({digits * scale})"
    return f"{_round(v, decimals):f}({digits})"


def parse_measured(text: str) -> tuple[float, float]:
    """Inverse of :func:`format_measured`: ``"1.9489(10)"`` -> (1.9489, 0.0010).

    A CIF writes measured numbers the same way, so the reader uses this too.
    """
    body = text.strip()
    if "(" not in body:
        return float(body), 0.0
    number, _, rest = body.partition("(")
    digits = rest.removesuffix(")")
    if not (rest.endswith(")") and digits.isdigit() and number):
        raise ValueError(f"{text!r} is not value(e.s.d.)")
    decimals = len(number.split(".", 1)[1]) if "." in number else 0
    return float(number), int(digits) * 10.0 ** (-decimals)
