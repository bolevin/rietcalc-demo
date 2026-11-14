# 0005 — e.s.d.'s written by the rule of 19

Status: accepted

## Context

A measured number is written `value(esd)`, the e.s.d. in units of the last digit of the
value. How many digits to keep is a convention, and two are in use here:

- The **full RietCalc** starts from a fixed precision (five decimals for a distance) and
  drops decimals until the e.s.d. needs no more than two digits, so its e.s.d.'s mostly
  carry two, from 10 to 99: the sample's Ca1–O1 bond reads `2.3552(55)`, Ti1–O1
  `1.94892(97)`.
- **Crystallographic journals** ask for the "rule of 19": two digits of e.s.d. when they
  form a number from 10 to 19, otherwise one, and the value rounded to match. The same
  bonds read `2.355(6)` and `1.9489(10)`.

The numbers underneath are the same; only their presentation differs. Unlike the error
model ([ADR 0004](0004-error-model-of-the-full-program.md)), presentation is not compared
by the golden master, which works on numbers.

## Decision

Write every measured number — on screen, in the report, and when reading it back from a
CIF — by the rule of 19, rounding half up, in one pair of functions:
`domain.notation.format_measured` and `parse_measured`.

## Consequences

- What the demo shows can be pasted into a manuscript as it stands, and a value is never
  quoted more finely than its uncertainty supports.
- The demo and the full program print some e.s.d.'s differently. Their screenshots side by
  side show it; the README says why.
- Rounding is explicit: `Decimal` with `ROUND_HALF_UP`, because Python's `round()` rounds
  half to even and binary floats turn many decimal halves into near-halves.
  `test_notation.py::test_half_up_rounding_not_bankers` holds this, and the mutation check
  confirms the test can fail.
- A property test holds the convention for any value and e.s.d.: the printed e.s.d. is
  between 2 and 19 units of the last digit, and reading the text back recovers both
  numbers to that digit.
