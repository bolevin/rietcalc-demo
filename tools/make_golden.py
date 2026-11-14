"""Record the reference values the golden-master test compares against.

    set RIETCALC_FULL_APP=C:\\path\\to\\riet_clc
    python tools/make_golden.py

The values come from the full RietCalc program (not part of this repository),
run on the bundled synthetic structure.  The demo was written independently of
that code base - different language level, different precision, different
algorithm for finding neighbours - so agreement between the two is evidence for
both.  The JSON this script writes is committed, so the test itself needs nothing
but the repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "src" / "rietcalc_demo" / "data" / "sample_structure.cif"
OUT = ROOT / "tests" / "golden" / "sample_reference.json"
R_MIN, R_MAX = 0.0, 3.2


def main() -> None:
    full_app = os.environ.get("RIETCALC_FULL_APP")
    if not full_app or not (Path(full_app) / "core" / "engine.py").exists():
        sys.exit("Set RIETCALC_FULL_APP to the folder of the full RietCalc program.")
    sys.path.insert(0, str(Path(full_app) / "core"))
    import engine  # type: ignore[import-not-found]
    import output  # type: ignore[import-not-found]

    run = engine.run(str(SAMPLE), cor=1.0, rmin=R_MIN, rmax=R_MAX, nwar=2, metdp=1)
    s = run.s
    coordination = {}
    for k1, _za, cn, groups in output.iter_unique_bond_groups(s, run.res):
        coordination[output._label(s, k1 - 1)] = {
            "number": cn,
            "bonds": [
                {
                    "target": output._label(s, nat - 1),
                    "distance": dist,
                    "esd": sd,
                    "multiplicity": mult,
                }
                for nat, dist, sd, mult in sorted(groups, key=lambda g: (g[1], g[0]))
            ],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "reference": f"RietCalc {output.VERSION} (full program)",
                "note": "The full program computes distances and their e.s.d.'s in "
                "single precision (REAL*4, as its FORTRAN original), so the values "
                "carry about seven significant digits.",
                "structure_sha256": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
                "r_min": R_MIN,
                "r_max": R_MAX,
                "atoms_in_cell": sum(round(m) for m in s.rMult),
                "volume": s.Vol,
                "volume_esd": s.dVol,
                "contacts": sum(len(scan) for _k, scan in run.res),
                "coordination": coordination,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
