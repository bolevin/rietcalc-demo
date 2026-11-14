"""What the presenter may ask of a window, and the data it hands over.

View models carry text that is already formatted and plain tuples of numbers.
The window draws them and decides nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AtomRow:
    label: str
    element: str
    x: str
    y: str
    z: str
    occupancy: str
    multiplicity: str
    position: str  # "general" or "special"


@dataclass(frozen=True, slots=True)
class CellAtomRow:
    """One atom of the unit cell and the operator that put it there."""

    label: str
    operator: str  # "2: -x+1/2, -y, z+1/2"
    x: str
    y: str
    z: str


@dataclass(frozen=True, slots=True)
class StructureViewModel:
    file_name: str
    title: str
    summary: str  # "Pnma - 8 operators - 4 independent atoms"
    cell: tuple[tuple[str, str], ...]  # ("a, A", "5.4423(3)"), ..., ("V, A^3", ...)
    atoms: tuple[AtomRow, ...]
    operators: tuple[str, ...]
    cell_atoms: tuple[CellAtomRow, ...]


@dataclass(frozen=True, slots=True)
class Metric:
    caption: str
    value: str
    hint: str = ""


@dataclass(frozen=True, slots=True)
class BondRow:
    """One line of the bond table.  ``source`` is empty on continuation lines."""

    source: str
    coordination: str
    bond: str  # "Ti1-O1"
    distance: str  # "1.9489(10)"
    multiplicity: str  # "x2"


@dataclass(frozen=True, slots=True)
class HistogramViewModel:
    centres: tuple[float, ...]
    counts: tuple[int, ...]
    width: float
    caption: str


@dataclass(frozen=True, slots=True)
class ResultViewModel:
    headline: Metric
    metrics: tuple[Metric, ...]
    bonds: tuple[BondRow, ...]
    histogram: HistogramViewModel
    report: str


@dataclass(frozen=True, slots=True)
class SettingsInput:
    """The settings as the widgets hold them."""

    r_min: float
    r_max: float


class MainView(Protocol):
    def show_structure(self, structure: StructureViewModel) -> None: ...

    def show_result(self, result: ResultViewModel) -> None: ...

    def clear_result(self) -> None: ...

    def show_error(self, title: str, message: str) -> None: ...

    def show_success(self, title: str, message: str) -> None: ...

    def settings(self) -> SettingsInput: ...

    def ask_open_path(self) -> Path | None: ...

    def ask_save_path(self, suggested: Path) -> Path | None: ...
