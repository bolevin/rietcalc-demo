"""Golden master: the demo against the full RietCalc program.

``tests/golden/sample_reference.json`` holds what the full program computes for
the bundled structure (recorded by ``tools/make_golden.py``).  The two code bases
share no code - the full program is a port of the FORTRAN original and works in
single precision, the demo is new and works in double - so agreement here is
independent evidence for both.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from rietcalc_demo.domain import DistanceSettings, Structure, analyse

REFERENCE: dict[str, Any] = json.loads(
    (Path(__file__).parents[1] / "golden" / "sample_reference.json").read_text("utf-8")
)
#: Distances: the full program's single precision leaves ~6e-7 A of noise (measured
#: worst case on this sample); three times that still separates every bond.
DISTANCE_TOLERANCE = 2e-6
#: e.s.d.'s: the full program takes single-precision forward differences with a
#: step of 1e-4, which leaves up to 4.6e-4 relative noise (measured); the demo takes
#: double-precision central differences.
ESD_TOLERANCE = 1e-3


@pytest.fixture(scope="module")
def result(sample: Structure) -> Any:
    return analyse(sample, DistanceSettings(REFERENCE["r_min"], REFERENCE["r_max"]))


def test_reference_belongs_to_the_bundled_structure(sample_path: Path) -> None:
    digest = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    assert digest == REFERENCE["structure_sha256"], (
        "The sample changed; re-record the reference with tools/make_golden.py."
    )


def test_cell_content_and_volume(result: Any) -> None:
    assert result.atoms_in_cell == REFERENCE["atoms_in_cell"]
    assert len(result.contacts) == REFERENCE["contacts"]
    assert result.volume.value == pytest.approx(REFERENCE["volume"], rel=1e-9)
    assert result.volume.esd == pytest.approx(REFERENCE["volume_esd"], rel=1e-9)


@pytest.mark.parametrize("source", sorted(REFERENCE["coordination"]))
def test_coordination_matches_the_full_program(result: Any, source: str) -> None:
    expected = REFERENCE["coordination"][source]
    mine = next(c for c in result.coordination if c.source == source)
    assert mine.number == expected["number"]
    assert len(mine.groups) == len(expected["bonds"])
    for got, want in zip(mine.groups, expected["bonds"], strict=True):
        assert got.target == want["target"]
        assert got.multiplicity == want["multiplicity"]
        assert got.distance.value == pytest.approx(want["distance"], abs=DISTANCE_TOLERANCE)
        assert got.distance.esd == pytest.approx(want["esd"], rel=ESD_TOLERANCE)
