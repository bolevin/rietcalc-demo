# 0004 — The error model of the full program, in double precision, verified by a golden master

Status: accepted

## Context

The full RietCalc reproduces its FORTRAN original digit for digit and therefore works the
way the original does: single-precision arithmetic, forward differences for the
derivatives. Its model of the errors is that of the original too:

1. A distance is a function of twelve parameters — six of the cell, three coordinates of
   the source atom, three of the neighbour — and the twelve are treated as independent,
   even when the neighbour is a symmetry image of the source itself.
2. The coordinate e.s.d.'s of an atom are carried to its image under an operator *R* as
   \|*R*·σ\|, row by row.

Both are simplifications. Point 1 ignores that an atom and its own image share their
refined coordinates. Point 2 is exact for operators whose rows hold a single ±1 — all
operators of orthorhombic and higher-symmetry groups in their standard settings — but for
a row such as `x-y` it gives \|σx − σy\| where independent errors would give
√(σx² + σy²).

The demo has no listing to reproduce, but its numbers must be demonstrably right.

## Decision

- Keep the error model of the full program, both points, so that the two programs can be
  compared number by number. Correcting it is a scientific decision for the author of the
  method, not a side effect of a demo.
- Calculate in ordinary double precision, with central differences and a step near the
  cube root of the machine epsilon (`domain/propagation.py`).
- Do not share code with the full program. Instead, record what the full program computes
  for the bundled structure (`tools/make_golden.py` → `tests/golden/sample_reference.json`)
  and require the demo to agree (`tests/domain/test_golden.py`).
- Tolerances follow from the reference's precision: 2 × 10⁻⁶ Å for distances (measured
  noise 6 × 10⁻⁷ Å), 10⁻³ relative for e.s.d.'s (measured 4.6 × 10⁻⁴, the noise of
  single-precision forward differences).

## Consequences

- The calculation reads like the formulas, with no precision emulation in the way.
- Agreement between two independent implementations is evidence for both. It also showed
  where the reference is noisy: the full program computes Ca1–O2 as 2.37797 Å from one
  end and 2.37798 Å from the other; the demo gives the same value from both ends, and a
  property test holds it to that.
- The test needs only this repository; re-recording the reference needs the full program.
  The JSON stores the SHA-256 of the structure, and a test fails if the structure changes
  without the reference being recorded again.
- The sample is orthorhombic, so the golden master cannot see point 2 at work. For
  hexagonal and trigonal structures the demo's e.s.d.'s inherit the simplification; this is
  listed as a risk in `docs/architecture.md`, section 11.
