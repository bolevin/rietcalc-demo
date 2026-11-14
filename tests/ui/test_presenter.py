"""The presenter against a fake view: every decision of the UI, without a window."""

from __future__ import annotations

from pathlib import Path

import pytest

from rietcalc_demo.main import build_service
from rietcalc_demo.ui.presenter import MainPresenter
from rietcalc_demo.ui.view import ResultViewModel, SettingsInput, StructureViewModel


class FakeView:
    def __init__(self) -> None:
        self.structure: StructureViewModel | None = None
        self.result: ResultViewModel | None = None
        self.errors: list[tuple[str, str]] = []
        self.successes: list[str] = []
        self.range = SettingsInput(0.0, 3.2)
        self.open_path: Path | None = None
        self.save_path: Path | None = None
        self.cleared = 0

    def show_structure(self, structure: StructureViewModel) -> None:
        self.structure = structure

    def show_result(self, result: ResultViewModel) -> None:
        self.result = result

    def clear_result(self) -> None:
        self.result = None
        self.cleared += 1

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def show_success(self, title: str, message: str) -> None:
        self.successes.append(title)

    def settings(self) -> SettingsInput:
        return self.range

    def ask_open_path(self) -> Path | None:
        return self.open_path

    def ask_save_path(self, suggested: Path) -> Path | None:
        return self.save_path


@pytest.fixture
def view() -> FakeView:
    return FakeView()


@pytest.fixture
def presenter(view: FakeView, sample_path: Path) -> MainPresenter:
    return MainPresenter(view, build_service(), sample_path)


def test_loading_the_sample_shows_the_structure(view: FakeView, presenter: MainPresenter) -> None:
    presenter.open_sample()
    s = view.structure
    assert s is not None
    assert s.summary == "Pnma · 8 operators · 4 independent atoms, 20 in the cell"
    assert s.cell[0] == ("a, Å", "5.4423(3)")
    assert s.cell[-1] == ("V, Å³", "223.73(2)")
    assert [(a.label, a.multiplicity, a.position) for a in s.atoms] == [
        ("Ca1", "4", "special"),
        ("Ti1", "4", "special"),
        ("O1", "4", "special"),
        ("O2", "8", "general"),
    ]
    assert len(s.cell_atoms) == 20
    assert s.cell_atoms[1].operator == "2: -x+1/2, -y, z+1/2"


def test_calculation_fills_metrics_bonds_and_histogram(
    view: FakeView, presenter: MainPresenter
) -> None:
    presenter.open_sample()
    presenter.calculate()
    r = view.result
    assert r is not None
    assert r.headline.value == "223.73(2)"
    assert [m.value for m in r.metrics] == ["20", "47", "1.9489(10)", "32"]
    assert r.metrics[2].hint == "Ti1–O1"
    first = r.bonds[0]
    assert (first.source, first.coordination, first.bond) == ("Ca1", "12", "Ca1–O1")
    assert r.bonds[1].source == ""  # continuation lines leave the atom blank
    assert sum(r.histogram.counts) == 47
    assert "rule of 19" in r.report


def test_bad_range_reports_an_error_and_clears(view: FakeView, presenter: MainPresenter) -> None:
    presenter.open_sample()
    presenter.calculate()
    view.range = SettingsInput(3.0, 1.0)
    presenter.calculate()
    assert view.result is None
    assert view.errors == [("Cannot calculate", "R max must be greater than R min.")]


def test_calculate_without_structure(view: FakeView, presenter: MainPresenter) -> None:
    presenter.calculate()
    assert view.errors[0][0] == "No structure"


def test_unreadable_file_is_an_error_not_a_crash(
    view: FakeView, presenter: MainPresenter, tmp_path: Path
) -> None:
    broken = tmp_path / "broken.cif"
    broken.write_text("data_x\n_cell_length_a 4\n", encoding="utf-8")
    presenter.load(broken)
    assert view.structure is None
    assert view.errors[0][0] == "Cannot open broken.cif"
    presenter.load(tmp_path / "missing.cif")
    assert view.errors[1][0] == "Cannot open missing.cif"


def test_save_report(view: FakeView, presenter: MainPresenter, tmp_path: Path) -> None:
    presenter.save_report()
    assert view.errors[-1][0] == "Nothing to save"
    presenter.open_sample()
    presenter.calculate()
    view.save_path = tmp_path / "report.txt"
    presenter.save_report()
    assert view.successes == ["Report saved"]
    assert "Ti1-O1" in view.save_path.read_text("utf-8")


def test_cancelled_dialogs_do_nothing(view: FakeView, presenter: MainPresenter) -> None:
    presenter.open_file()  # the open dialog returns None
    assert view.structure is None
    assert not view.errors
