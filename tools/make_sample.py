"""Write the synthetic sample structure shipped with the demo.

    python tools/make_sample.py

The sample is a perovskite of the CaTiO3 / GdFeO3 type in space group Pnma: a
three-dimensional network of corner-sharing TiO6 octahedra, tilted so that the
calcium site is irregular.  The structure type is textbook crystallography; the
numbers below are NOT a published refinement.  Coordinates were chosen to give a
chemically sensible geometry (Ti-O about 1.95 A, bond-valence sums near the formal
charges), and the e.s.d.'s are invented at a typical powder-diffraction level.

The sample is meant to exercise everything the demo does:

* a centrosymmetric group with glide planes and a screw axis - eight operators,
  none of them a pure lattice translation;
* every kind of site: general (O2, 8d), on a mirror plane (Ca1 and O1, 4c), and on
  an inversion centre with all three coordinates fixed (Ti1, 4b);
* coordinates fixed by symmetry carry no e.s.d., refined ones do, so the error
  propagation has both cases to handle;
* distorted coordination: six Ti-O bonds in two groups, an eight-to-twelve-fold
  calcium site with many distinct distances - a non-trivial histogram.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "rietcalc_demo" / "data" / "sample_structure.cif"

# the eight operators of Pnma (No. 62), standard setting
OPERATORS = (
    "x, y, z",
    "-x+1/2, -y, z+1/2",
    "-x, y+1/2, -z",
    "x+1/2, -y+1/2, -z+1/2",
    "-x, -y, -z",
    "x+1/2, y, -z+1/2",
    "x, -y+1/2, z",
    "-x+1/2, y+1/2, z+1/2",
)

# label, type symbol, x, y, z, occupancy, B_iso   (value(esd) as written in a CIF)
ATOMS = (
    ("Ca1", "Ca2+", "0.0352(4)", "0.25", "0.9932(5)", "1", "0.62(4)"),
    ("Ti1", "Ti4+", "0", "0", "0.5", "1", "0.38(3)"),
    ("O1", "O2-", "0.4908(9)", "0.25", "0.0714(9)", "1", "0.55(9)"),
    ("O2", "O2-", "0.2888(6)", "0.0371(4)", "0.7113(6)", "1", "0.58(7)"),
)

CELL = (
    ("_cell_length_a", "5.4423(3)"),
    ("_cell_length_b", "7.6401(4)"),
    ("_cell_length_c", "5.3807(3)"),
    ("_cell_angle_alpha", "90"),
    ("_cell_angle_beta", "90"),
    ("_cell_angle_gamma", "90"),
)


def render() -> str:
    lines = [
        "# Synthetic demo structure written by tools/make_sample.py.",
        "# CaTiO3-type perovskite, space group Pnma.  NOT a published refinement:",
        "# the coordinates and e.s.d.'s are chosen for the demonstration.",
        "",
        "data_CaTiO3_type_synthetic",
        "_chemical_name_common  'CaTiO3-type perovskite (synthetic demo data)'",
        "_chemical_formula_sum  'Ca Ti O3'",
        "",
    ]
    lines += [f"{tag:<22s} {value}" for tag, value in CELL]
    lines += [
        "",
        "_space_group_name_H-M_alt  'P n m a'",
        "_space_group_IT_number     62",
        "",
        "loop_",
        "_space_group_symop_operation_xyz",
    ]
    lines += [f"'{op}'" for op in OPERATORS]
    lines += [
        "",
        "loop_",
        "_atom_site_label",
        "_atom_site_type_symbol",
        "_atom_site_fract_x",
        "_atom_site_fract_y",
        "_atom_site_fract_z",
        "_atom_site_occupancy",
        "_atom_site_B_iso_or_equiv",
    ]
    lines += ["  ".join(f"{field:<10s}" for field in atom).rstrip() for atom in ATOMS]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
