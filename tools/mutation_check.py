"""Test the tests: break the code on purpose and expect the suite to notice.

    python tools/mutation_check.py

Each mutation below is one plausible mistake.  It is applied to a temporary copy
of the project, the named tests are run against the copy, and they must FAIL.
A mutation that survives means a guard that guards nothing - the script then
exits with status 1.  The working tree is never touched.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "src/rietcalc_demo/domain"


@dataclass(frozen=True)
class Mutation:
    name: str
    file: str
    old: str
    new: str
    tests: str


MUTATIONS = [
    Mutation(
        "Propagation: the derivative taken over half the step",
        f"{DOMAIN}/propagation.py",
        "derivative = (upper - lower) / (2.0 * step)",
        "derivative = (upper - lower) / step",
        "tests/domain/test_propagation.py",
    ),
    Mutation(
        "Propagation: errors added linearly, not in quadrature",
        f"{DOMAIN}/propagation.py",
        "total += (derivative * esd) ** 2",
        "total += abs(derivative * esd)",
        "tests/domain/test_propagation.py",
    ),
    Mutation(
        "Metric: the a-b cross term without its factor 2",
        f"{DOMAIN}/cell.py",
        "+ 2.0 * a * b * cos_g * dx * dy",
        "+ a * b * cos_g * dx * dy",
        "tests/domain/test_cell.py",
    ),
    Mutation(
        "Volume: the triple-cosine term with the wrong sign",
        f"{DOMAIN}/cell.py",
        "+ 2.0 * ca * cb * cg",
        "- 2.0 * ca * cb * cg",
        "tests/domain/test_cell.py",
    ),
    Mutation(
        "Cell: angles that close no volume accepted",
        f"{DOMAIN}/cell.py",
        "_angle_factor(self.alpha.value, self.beta.value, self.gamma.value) < 1e-3:",
        "_angle_factor(self.alpha.value, self.beta.value, self.gamma.value) < 0.0:",
        "tests/domain/test_cell.py",
    ),
    Mutation(
        "Symmetry: a transformed e.s.d. keeps the sign of the rotation",
        f"{DOMAIN}/symmetry.py",
        "abs(r[0][0] * esd[0] + r[0][1] * esd[1] + r[0][2] * esd[2]),",
        "r[0][0] * esd[0] + r[0][1] * esd[1] + r[0][2] * esd[2],",
        "tests/domain/test_symmetry.py",
    ),
    Mutation(
        "Symmetry: the translation of x forgotten",
        f"{DOMAIN}/symmetry.py",
        "r[0][0] * position[0] + r[0][1] * position[1] + r[0][2] * position[2] + float(t[0]),",
        "r[0][0] * position[0] + r[0][1] * position[1] + r[0][2] * position[2],",
        "tests/domain/test_symmetry.py",
    ),
    Mutation(
        "Expansion: images not folded back into the cell",
        f"{DOMAIN}/expansion.py",
        "position = (_fold(p[0]), _fold(p[1]), _fold(p[2]))",
        "position = p",
        "tests/domain/test_structure_and_expansion.py",
    ),
    Mutation(
        "Expansion: an atom on a special position counted once per operator",
        f"{DOMAIN}/expansion.py",
        "        if any(_same_site(position, image.position) for image in images):\n"
        "            continue\n",
        "",
        "tests/domain/test_structure_and_expansion.py",
    ),
    Mutation(
        "Distances: R max included in the range",
        f"{DOMAIN}/distances.py",
        "d >= r_max:",
        "d > r_max:",
        "tests/domain/test_distances_and_bonds.py",
    ),
    Mutation(
        "Distances: lattice repeats searched in one direction only",
        f"{DOMAIN}/distances.py",
        "range(math.ceil(s - p - r), ",
        "range(math.ceil(s - p), ",
        "tests/domain/test_golden.py",
    ),
    Mutation(
        "Distances: the e.s.d.'s of the cell left out",
        f"{DOMAIN}/distances.py",
        "(*cell.esds, *source.position_esd, *image.esd)",
        "(*(0.0,) * 6, *source.position_esd, *image.esd)",
        "tests/domain/test_golden.py",
    ),
    Mutation(
        "Bonds: equal distances to different atoms merged into one bond",
        f"{DOMAIN}/bonds.py",
        "            self.target == contact.target\n            and abs(",
        "            abs(",
        "tests/domain/test_distances_and_bonds.py",
    ),
    Mutation(
        "Notation: the rule of 19 becomes a rule of 29",
        f"{DOMAIN}/notation.py",
        "if two_digits <= 19:",
        "if two_digits <= 29:",
        "tests/domain/test_notation.py",
    ),
    Mutation(
        "Notation: banker's rounding",
        f"{DOMAIN}/notation.py",
        "rounding=ROUND_HALF_UP)",
        'rounding="ROUND_HALF_EVEN")',
        "tests/domain/test_notation.py",
    ),
    Mutation(
        "Notation: an e.s.d. read one decimal too fine",
        f"{DOMAIN}/notation.py",
        "int(digits) * 10.0 ** (-decimals)",
        "int(digits) * 10.0 ** (-decimals - 1)",
        "tests/domain/test_notation.py",
    ),
    Mutation(
        "Histogram: a value on a bin edge counted in the bin below",
        f"{DOMAIN}/histogram.py",
        "k = math.floor((value - low) / width)",
        "k = math.ceil((value - low) / width) - 1",
        "tests/domain/test_histogram.py",
    ),
    Mutation(
        "CIF: an apostrophe inside a quoted string ends it",
        "src/rietcalc_demo/adapters/cif.py",
        "line[end] == ch and (end + 1 == len(line) or line[end + 1].isspace())",
        "line[end] == ch",
        "tests/adapters/test_cif.py",
    ),
    Mutation(
        "Presenter: a failed calculation leaves the old result on screen",
        "src/rietcalc_demo/ui/presenter.py",
        "            self._run = None\n            self._view.clear_result()\n",
        "            self._run = None\n",
        "tests/ui/test_presenter.py",
    ),
    Mutation(
        "Window: the histogram keeps its colours on a theme switch",
        "src/rietcalc_demo/ui/main_window.py",
        "        setTheme(Theme.DARK if dark else Theme.LIGHT)\n"
        "        self.page.histogram.set_dark(dark)\n",
        "        setTheme(Theme.DARK if dark else Theme.LIGHT)\n",
        "tests/ui/test_main_window.py",
    ),
    Mutation(
        "Window: number fields follow the system locale",
        "src/rietcalc_demo/ui/main_window.py",
        "            spin.setLocale(number_locale)\n",
        "",
        "tests/ui/test_main_window.py",
    ),
    Mutation(
        "Architecture: the calculation starts to depend on numpy",
        f"{DOMAIN}/histogram.py",
        "import math\n",
        "import math\n\nimport numpy\n",
        "tests/architecture",
    ),
    Mutation(
        "Architecture: the presenter reaches for Qt",
        "src/rietcalc_demo/ui/presenter.py",
        "from pathlib import Path\n",
        "from pathlib import Path\n\nfrom PySide6.QtCore import Qt\n",
        "tests/architecture",
    ),
]


def run(mutation: Mutation, work: Path) -> bool:
    """True if the tests failed, i.e. the mutation was caught."""
    target = work / mutation.file
    source = (ROOT / mutation.file).read_text("utf-8")
    if source.count(mutation.old) != 1:
        sys.exit(f"{mutation.name}: the text to replace occurs {source.count(mutation.old)} times")
    target.write_text(source.replace(mutation.old, mutation.new), "utf-8", newline="\n")
    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", mutation.tests],
            cwd=work,
            env={
                **os.environ,
                "PYTHONPATH": str(work / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        target.write_text(source, "utf-8", newline="\n")
    return done.returncode == 1  # 1 = tests ran and failed; anything else is not a catch


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in ("src", "tests"):
            shutil.copytree(ROOT / name, work / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "pyproject.toml", work)
        shutil.copy(ROOT / "README.md", work)

        control = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=work,
            env={**os.environ, "PYTHONPATH": str(work / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        if control.returncode != 0:
            sys.exit("Control run failed: the unmutated copy must pass.\n" + control.stdout)
        print("control: unmutated copy passes")

        survived = []
        for mutation in MUTATIONS:
            caught = run(mutation, work)
            print(f"  {'caught  ' if caught else 'SURVIVED'}  {mutation.name}")
            if not caught:
                survived.append(mutation.name)

    print(f"\n{len(MUTATIONS) - len(survived)} of {len(MUTATIONS)} mutations caught")
    sys.exit(1 if survived else 0)


if __name__ == "__main__":
    main()
