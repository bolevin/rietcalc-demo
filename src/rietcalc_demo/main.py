"""Composition root: the only place that knows every concrete class."""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from rietcalc_demo import __version__
from rietcalc_demo.adapters.cif import CifReader
from rietcalc_demo.adapters.files import FileTextStore
from rietcalc_demo.adapters.text_report import PlainTextReport
from rietcalc_demo.application import DistanceService


def data_path(name: str) -> Path:
    """A file shipped inside the package (also inside the frozen .exe)."""
    return Path(str(resources.files("rietcalc_demo") / "data" / name))


def build_service() -> DistanceService:
    return DistanceService(reader=CifReader(), renderer=PlainTextReport(), store=FileTextStore())


def _selftest() -> int:
    """Load the bundled sample, compute its distances and check the result is sane."""
    from rietcalc_demo.domain import DistanceSettings

    service = build_service()
    run = service.analyse(service.load(data_path("sample_structure.cif")), DistanceSettings())
    a = run.analysis
    ti = next(c for c in a.coordination if c.source == "Ti1")
    shortest = min(c.distance.value for c in a.contacts)
    ok = (
        a.atoms_in_cell == 20
        and len(a.contacts) == 47
        and ti.number == 8
        and abs(shortest - 1.948915) < 1e-5
    )
    # ASCII only: a frozen Windows build may print to a cp1251 console
    print(
        f"SELFTEST {'OK' if ok else 'FAIL'}  atoms in cell = {a.atoms_in_cell}, "
        f"contacts = {len(a.contacts)}, shortest = {shortest:.5f} A"
    )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rietcalc-demo", description=__doc__)
    parser.add_argument("structure", nargs="?", type=Path, help="CIF file to open")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--selftest", action="store_true", help="verify the build and exit")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()

    # Qt is imported here so that --selftest and --version need no display
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication
    from qfluentwidgets import Theme, setTheme, setThemeColor

    from rietcalc_demo.ui.main_window import MainWindow
    from rietcalc_demo.ui.presenter import MainPresenter

    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Segoe UI", 10))
    setTheme(Theme.AUTO)
    setThemeColor("#0067c0")

    window = MainWindow(QIcon(str(data_path("icon.ico"))))
    presenter = MainPresenter(window, build_service(), data_path("sample_structure.cif"))
    window.bind(presenter)
    window.show()
    if args.structure is not None:
        presenter.load(args.structure)
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
