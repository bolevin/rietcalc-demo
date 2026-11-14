# 0006 — Ship synthetic sample data only

Status: accepted

## Context

A demonstration needs a structure to load, and the tests need a fixed input. Refined
structures belong to the people who measured and refined them, often to work that is not
yet published; the reference data of the full program are such structures.

## Decision

The repository contains one structure, written by `tools/make_sample.py`: a CaTiO₃-type
perovskite in space group *Pnma* (No. 62), four independent atoms, cell and coordinates
close to the textbook structure, every e.s.d. invented. Oxidation states are given in the
atom types (`Ca2+`, `Ti4+`, `O2-`), so the same file exercises the bond-valence sums of
the full program.

## Consequences

- Nothing in the repository, the screenshots or the tests is anyone's measurement —
  including the screenshots of the full program, which show this structure too.
- The structure has what the calculation is about: atoms on special positions (Ca, Ti and
  O1 on mirror planes or inversion centres, multiplicity 4) next to one in the general
  position (O2, multiplicity 8), an octahedron with three different Ti–O bonds, and a
  twelve-fold cage around Ca.
- It is chemically sensible: in the full program its bond-valence sums come out as
  Ca 2.07, Ti 4.12, O 2.09 and 2.05, with a global instability index of 0.08.
- The file is reproducible byte for byte; its SHA-256 is stored with the reference values.
- An orthorhombic sample cannot show everything — see the limits of
  [ADR 0004](0004-error-model-of-the-full-program.md).
