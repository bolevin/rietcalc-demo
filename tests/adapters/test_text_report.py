from __future__ import annotations

from pathlib import Path

from rietcalc_demo.adapters.files import FileTextStore
from rietcalc_demo.adapters.text_report import PlainTextReport
from rietcalc_demo.application import DistanceRun
from rietcalc_demo.domain import DistanceSettings, Structure, analyse


def test_report_lists_cell_atoms_and_bonds(sample: Structure, sample_path: Path) -> None:
    run = DistanceRun(sample_path, analyse(sample, DistanceSettings()))
    text = PlainTextReport().render(run)
    for expected in (
        "sample_structure.cif",
        "5.4423(3)",
        "223.73(2)",
        "4 independent, 20 in the cell",
        "Ti1   coordination number 8",
        "Ti1-O1",
        "1.9489(10)  x2",
        "rule of 19",
    ):
        assert expected in text, expected


def test_store_writes_windows_line_ends(tmp_path: Path) -> None:
    target = tmp_path / "r.txt"
    FileTextStore().save(target, "a\nb\n")
    assert target.read_bytes() == b"a\r\nb\r\n"
