# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-15

First version.

### Added

- Reader for CIF files: quoted strings, comments, text fields, loops; cell, symmetry
  operators (current and legacy tags), atoms with their e.s.d.'s.
- Symmetry expansion into the unit cell, with atoms on special positions counted once and
  their multiplicities reported.
- Interatomic distances in a range *R*min ≤ *d* < *R*max, lattice repeats included, each
  with its e.s.d. propagated from the cell and the coordinates.
- Coordination table: symmetry-unique bonds with multiplicities and coordination numbers.
- Cell volume with its e.s.d.
- Values and e.s.d.'s written by the rule of 19.
- Distance histogram; light and dark theme.
- Plain-text report, shown on screen and saved on request.
- Synthetic sample structure and the script that writes it.
- `--selftest` to verify a build without opening a window.
