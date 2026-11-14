"""The analysis as a plain-text report."""

from __future__ import annotations

import textwrap

from rietcalc_demo import __version__
from rietcalc_demo.application.service import DistanceRun
from rietcalc_demo.domain import format_measured as fm

_RULE = "=" * 68


def _line(label: str, value: str) -> str:
    return f"  {label + ' ':.<22} {value}"


def _wrapped(label: str, value: str) -> list[str]:
    """A long value continues on the next lines, aligned under its start."""
    first, *rest = textwrap.wrap(value, width=43) or ["-"]
    return [_line(label, first), *(" " * 25 + text for text in rest)]


class PlainTextReport:
    """Implements :class:`rietcalc_demo.application.ports.ReportRenderer`."""

    def render(self, run: DistanceRun) -> str:
        a = run.analysis
        st, cell, s = a.structure, a.structure.cell, a.settings
        out = [
            f"RietCalc Demo {__version__} - interatomic distances",
            _RULE,
            "",
            "Structure",
            _line("File", run.source.name),
            *_wrapped("Title", st.title),
            _line("a, b, c (A)", "   ".join(fm(p.value, p.esd) for p in (cell.a, cell.b, cell.c))),
            _line(
                "alpha, beta, gamma",
                "   ".join(fm(p.value, p.esd) for p in (cell.alpha, cell.beta, cell.gamma))
                + " deg",
            ),
            _line("Volume (A^3)", fm(a.volume.value, a.volume.esd)),
            _line("Symmetry operators", str(len(st.operators))),
            _line("Atoms", f"{len(st.atoms)} independent, {a.atoms_in_cell} in the cell"),
            _line("Distance range", f"{s.r_min:.3f} <= d < {s.r_max:.3f} A"),
            "",
            "Independent atoms",
            f"  {'Label':<7}{'El':<4}{'x':>14}{'y':>14}{'z':>14}{'Occ':>10}{'Mult':>6}",
        ]
        for atom, mult in zip(st.atoms, a.multiplicities, strict=True):
            out.append(
                f"  {atom.label:<7}{atom.element:<4}"
                f"{fm(atom.x.value, atom.x.esd):>14}"
                f"{fm(atom.y.value, atom.y.esd):>14}"
                f"{fm(atom.z.value, atom.z.esd):>14}"
                f"{fm(atom.occupancy.value, atom.occupancy.esd):>10}{mult:>6}"
            )
        out += ["", "Symmetry-unique bonds (d in A, e.s.d. in the last digit)"]
        for c in a.coordination:
            out.append(f"  {c.source}   coordination number {c.number}")
            if not c.groups:
                out.append("      no neighbour in the range")
            for g in c.groups:
                bond = f"{c.source}-{g.target}"
                out.append(
                    f"      {bond:<10}{fm(g.distance.value, g.distance.esd):>13}  x{g.multiplicity}"
                )
        out += [
            "",
            _RULE,
            "e.s.d.'s: first-order propagation from the six cell parameters and the",
            "coordinates of both atoms, taken as independent (as in the full RietCalc).",
            "value(e.s.d.) written by the rule of 19 of the crystallographic journals.",
            "",
        ]
        return "\n".join(out)
