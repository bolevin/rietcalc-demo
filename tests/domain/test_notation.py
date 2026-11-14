"""value(e.s.d.) notation: the rule of 19 and its inverse."""

from __future__ import annotations

import pytest

from rietcalc_demo.domain import format_measured, parse_measured


@pytest.mark.parametrize(
    ("value", "esd", "expected"),
    [
        (1.948915, 0.000975, "1.9489(10)"),  # 0.00098 rounds to 10: two digits
        (0.0352, 0.0004, "0.0352(4)"),  # one digit 2..9 stays one digit
        (2.355185, 0.0055, "2.355(6)"),  # 55 > 19: back to one digit
        (223.72798, 0.0211, "223.73(2)"),
        (5.4423, 0.0003, "5.4423(3)"),
        (1.0, 0.013, "1.000(13)"),  # 13 <= 19 keeps two digits
        (1.0, 0.023, "1.00(2)"),  # 23 > 19: one digit
        (12345.6, 25.0, "12350(30)"),  # an e.s.d. above 19 rounds the value to tens
    ],
)
def test_rule_of_nineteen(value: float, esd: float, expected: str) -> None:
    assert format_measured(value, esd) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.25, "0.25"), (0.5, "0.5"), (0.0, "0"), (90.0, "90"), (-0.0, "0"), (1.0, "1")],
)
def test_a_value_without_esd_drops_trailing_zeros(value: float, expected: str) -> None:
    assert format_measured(value, 0.0) == expected


def test_half_up_rounding_not_bankers() -> None:
    # binary floating point would print 0.12 for 0.125 with Python's round()
    assert format_measured(0.125, 0.002) == "0.125(2)"


@pytest.mark.parametrize(
    ("text", "value", "esd"),
    [
        ("0.0352(4)", 0.0352, 0.0004),
        ("5.4423(3)", 5.4423, 0.0003),
        ("1.9489(10)", 1.9489, 0.0010),
        ("90", 90.0, 0.0),
        ("0.25", 0.25, 0.0),
        ("12(3)", 12.0, 3.0),
    ],
)
def test_parse(text: str, value: float, esd: float) -> None:
    got_value, got_esd = parse_measured(text)
    assert got_value == pytest.approx(value)
    assert got_esd == pytest.approx(esd)


@pytest.mark.parametrize("text", ["0.1(x)", "(4)", "0.1(4", "1.2.3"])
def test_parse_rejects_malformed_text(text: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - float() and our own check both raise it
        parse_measured(text)
