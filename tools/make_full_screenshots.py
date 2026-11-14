"""Render the screenshots of the FULL RietCalc program used in the README.

    set RIETCALC_FULL_APP=C:\\path\\to\\riet_clc
    python tools/make_full_screenshots.py

The full program is not part of this repository; this script only drives it.
It loads the same synthetic structure the demo ships with, runs the real
calculations (distances + angles with e.s.d.'s, bond-valence sums, the radial
distribution function with its partials) and renders the main window and its
tool windows the way they appear on screen.  Nothing is shown on the screen,
and nothing of the full program is changed:

* its settings normally live in the Windows registry; here they are replaced by
  an in-memory stand-in, so the owner's theme and recent files stay untouched;
* the input is a copy of the sample under ``build/``, so the output file the
  program writes next to its input lands there too;
* the number format is English (decimal point), as on an English Windows.

The tool windows (popups) are drawn by the operating system with a title bar;
Qt cannot render that frame, so a plain Windows 11 style title bar is painted
over each one.  Everything inside the windows is the program's own pixels.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PySide6.QtCore import QLocale, QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from make_screenshots import DARK_BACKDROP, LIGHT_BACKDROP, SCALE, settle

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "src" / "rietcalc_demo" / "data" / "sample_structure.cif"
WORK = ROOT / "build" / "full-screenshots" / "examples"
OUT = ROOT / "docs" / "img"
SIZE = (1320, 960)
FONT = "C:/Windows/Fonts/segoeui.ttf"
MARGIN = 110  # backdrop around the windows, in image pixels
RADIUS = 8 * SCALE  # Windows 11 rounds window corners

# The program's own theme list: (index, colour of the window background).
LIGHT = (1, "#f3f3f3")
SLATE = (3, "#2b3138")
OCEAN = (4, "#0b2540")


class MemorySettings:
    """Stands in for QSettings: same calls, nothing reaches the registry."""

    def __init__(self, *_: object) -> None:
        self._values: dict[str, Any] = {}

    def value(self, key: str, default: Any = None, type: Any = None) -> Any:
        found = self._values.get(key, default)
        if type is list:
            return list(found) if found else []
        if type is str:
            return "" if found is None else str(found)
        return found

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - the Qt name
        self._values[key] = value

    def remove(self, key: str) -> None:
        self._values.pop(key, None)


def load_full_program() -> Any:
    full_app = os.environ.get("RIETCALC_FULL_APP")
    if not full_app or not (Path(full_app) / "app.py").exists():
        sys.exit("Set RIETCALC_FULL_APP to the folder of the full RietCalc program.")
    sys.path.insert(0, full_app)
    import app  # type: ignore[import-not-found]

    app.QSettings = MemorySettings
    return app


# ------------------------------------------------------------------ pictures
def render(widget: QWidget, background: str) -> Image.Image:
    pixmap = QPixmap(widget.size() * SCALE)
    pixmap.setDevicePixelRatio(SCALE)
    pixmap.fill(QColor(background))
    widget.render(pixmap, QPoint(0, 0))
    raw = WORK / "_raw.png"
    pixmap.save(str(raw))
    image = Image.open(raw).convert("RGBA")
    image.load()
    raw.unlink()
    return image


def tool_window(body: Image.Image, title: str, dark: bool) -> Image.Image:
    """A popup as Windows shows it: the program's pixels under a title bar."""
    bar = 32 * SCALE
    face, ink = ("#2b2b2b", "#ffffff") if dark else ("#ffffff", "#1a1a1a")
    window = Image.new("RGBA", (body.width, body.height + bar), face)
    draw = ImageDraw.Draw(window)
    font = ImageFont.truetype(FONT, 12 * SCALE)
    draw.text((12 * SCALE, bar // 2), title, fill=ink, font=font, anchor="lm")
    cx, cy, arm = body.width - 23 * SCALE, bar // 2, 5 * SCALE
    for end in ((cx - arm, cy - arm, cx + arm, cy + arm), (cx - arm, cy + arm, cx + arm, cy - arm)):
        draw.line(end, fill=ink, width=SCALE)
    window.paste(body, (0, bar))
    return window


def gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    canvas = Image.new("RGBA", size)
    a, b = (Image.new("RGBA", (1, 1), c).getpixel((0, 0)) for c in (top, bottom))
    draw = ImageDraw.Draw(canvas)
    for y in range(size[1]):
        t = y / (size[1] - 1)
        draw.line(
            [(0, y), (size[0], y)],
            fill=tuple(round(p + (q - p) * t) for p, q in zip(a, b, strict=True)),  # type: ignore[arg-type]
        )
    return canvas


def desktop(
    layers: list[tuple[Image.Image, tuple[int, int]]], backdrop: tuple[str, str], dark: bool
) -> Image.Image:
    """Windows on a gradient, back to front, each with rounded corners and a shadow.

    Positions are in window coordinates (logical pixels) relative to the first
    layer, the main window.
    """
    left = min(x for _, (x, _) in layers) * SCALE
    top = min(y for _, (_, y) in layers) * SCALE
    right = max(x * SCALE + image.width for image, (x, _) in layers)
    bottom = max(y * SCALE + image.height for image, (_, y) in layers)
    size = (right - left + 2 * MARGIN, bottom - top + 2 * MARGIN)
    canvas = gradient(size, *backdrop)
    edge = (255, 255, 255, 40) if dark else (0, 0, 0, 50)
    for image, (x, y) in layers:
        px, py = x * SCALE - left + MARGIN, y * SCALE - top + MARGIN
        box = [px, py, px + image.width - 1, py + image.height - 1]
        shadow = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [box[0], box[1] + 18, box[2], box[3] + 18], radius=RADIUS, fill=(0, 0, 0, 120)
        )
        canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, image.width - 1, image.height - 1], radius=RADIUS, fill=255
        )
        canvas.paste(image, (px, py), mask)
        ImageDraw.Draw(canvas).rounded_rectangle(box, radius=RADIUS, outline=edge, width=1)
    return canvas.convert("RGB")


# ------------------------------------------------------------------ driving the program
def fit_table(pop: QWidget, table: Any) -> None:
    """Widen a popup until its table needs no horizontal scroll bar."""
    table.resizeColumnsToContents()
    needed = table.horizontalHeader().length() + table.verticalHeader().width() + 4
    pop.resize(pop.width() + max(0, needed - table.viewport().width()), pop.height())


def over_plot(session: Session) -> tuple[tuple[int, int], tuple[int, int]]:
    """Where a tool window lies exactly over the plot pane, and its body size."""
    calc, window = session.calc, session.window
    splitter = calc.plot_title.parentWidget().parentWidget()
    handle = splitter.handle(1)
    corner = handle.mapTo(window, QPoint(0, 0))
    title = calc.plot_title.mapTo(window, QPoint(0, 0))
    left, right = corner.x() - 10, corner.x() + handle.width() + 10
    top, bottom = title.y() - 4, corner.y() + handle.height() + 3
    return (left, top), (right - left, bottom - top - 32)


def hide_toasts(window: QWidget) -> None:
    from qfluentwidgets import InfoBar

    for bar in window.findChildren(InfoBar):
        bar.hide()


def calculate(qt: QApplication, calc: Any) -> None:
    calc.calculate()
    deadline = time.monotonic() + 300
    settle(qt, 300)
    while calc.calc_btn.text() != "Calculate":
        if time.monotonic() > deadline:
            sys.exit("The calculation did not finish in five minutes.")
        qt.processEvents()
        time.sleep(0.05)
    settle(qt, 900)
    for pop in calc._popups:  # run warnings, if any, are not part of the picture
        pop.hide()


class Session:
    """The full program's window, and the pictures taken of it."""

    def __init__(self, full: Any, qt: QApplication) -> None:
        self.qt = qt
        self.window = full.MainWindow()
        self.window.setMicaEffectEnabled(False)  # Mica is composed by the OS, not by Qt
        self.calc = self.window.calc
        for top in (self.window, self.calc.gwin, self.calc.bvswin, *self.calc._popups):
            top.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self.window.resize(*SIZE)
        self.window.show()
        self.theme = LIGHT
        self.use_theme(LIGHT)

    @property
    def dark(self) -> bool:
        return self.theme != LIGHT

    def use_theme(self, theme: tuple[int, str]) -> None:
        self.theme = theme
        self.calc.theme.setCurrentIndex(theme[0])
        settle(self.qt)

    def main(self) -> Image.Image:
        hide_toasts(self.window)
        settle(self.qt)
        return render(self.window, self.theme[1])

    def popup(self, pop: QWidget) -> Image.Image:
        settle(self.qt)
        return tool_window(render(pop, self.theme[1]), pop.windowTitle(), self.dark)

    def save(self, name: str, layers: list[tuple[Image.Image, tuple[int, int]]]) -> None:
        backdrop = DARK_BACKDROP if self.dark else LIGHT_BACKDROP
        target = OUT / f"full-{name}.png"
        desktop(layers, backdrop, self.dark).save(target, optimize=True)
        print(f"wrote {target}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    source = WORK / "sample_structure.cif"
    shutil.copyfile(SAMPLE, source)

    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    full = load_full_program()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    qt = QApplication.instance() or QApplication(sys.argv[:1])
    assert isinstance(qt, QApplication)
    qt.setFont(QFont("Segoe UI", 10))
    session = Session(full, qt)
    calc = session.calc

    # ---- distances + angles with e.s.d.'s and bond-valence sums -----------------
    calc._load_path(str(source))
    calc.comment_edit.setPlainText("Synthetic CaTiO3-type structure, Pnma - demo data")
    calc._refresh_comment_disp()
    calc.kind.setCurrentIndex(1)  # Distances + Angles
    calc.rmin.setValue(0.0)
    calc.rmax.setValue(3.5)
    calc.esd.setCurrentIndex(0)  # full: cell and coordinates
    calc.confirm_chk.setChecked(False)
    calculate(qt, calc)

    calc._show_section("dist")
    session.save("distances", [(session.main(), (0, 0))])

    calc._show_section("xyz")
    main = session.main()
    calc._show_cell_popup()
    cell = session.popup(calc.cell_pop)
    calc.cell_pop.hide()
    calc._show_atoms_popup()
    fit_table(calc.atoms_pop, calc.atom_tbl)
    atoms = session.popup(calc.atoms_pop)
    calc.atoms_pop.hide()
    session.save("structure", [(main, (0, 0)), (cell, (560, 96)), (atoms, (300, 400))])

    calc._show_section("bvs")
    main = session.main()
    calc._show_bv_popup()
    table = session.popup(calc.bv_pop)
    titanium = next(i for i, key in enumerate(calc._bv_keys) if key[0] == "Ti")
    calc.bv_tbl.selectRow(titanium)
    calc._bv_cell_clicked(titanium, 0)
    chooser = session.popup(calc.bvpick_pop)
    calc.bvpick_pop.hide()
    calc.bv_pop.hide()
    session.save("bvs", [(main, (0, 0)), (table, (560, 96)), (chooser, (412, 330))])

    session.use_theme(SLATE)
    calc._show_section("angl")
    main = session.main()
    calc._open_bvs_chart()
    place, size = over_plot(session)
    calc.bvswin.resize(*size)
    settle(qt)
    chart = tool_window(render(calc.bvswin, SLATE[1]), calc.bvswin.windowTitle(), True)
    calc.bvswin.hide()
    session.save("angles-dark", [(main, (0, 0)), (chart, place)])

    # ---- the radial distribution function --------------------------------------
    session.use_theme(OCEAN)
    calc.kind.setCurrentIndex(2)  # RDF
    calc.rmax.setValue(12.0)
    calculate(qt, calc)
    print("RDF curves:", ", ".join(calc._curves))
    for curve, near in (("g_TiO", 1.95), ("g_CaO", 2.45), ("g_OO", 2.75), ("g_TiCa", 3.2)):
        line = calc._curves[curve]
        calc._add_pick(line, *calc._peak_near(line, near), "max")
    main = session.main()
    calc._open_graph_window()
    for curve in ("g_TiO", "g_CaO", "g_OO"):
        calc.gchecks[curve].setChecked(True)
    place, size = over_plot(session)  # over the main plot, the picks table stays in view
    calc.gwin.resize(size[0], 450)
    settle(qt)
    calc.gplot.getViewBox().setXRange(1.6, 4.2, padding=0)
    calc._toggle_gregion()  # a marked region, as for recording a mean peak position
    settle(qt)
    graph = tool_window(render(calc.gwin, OCEAN[1]), calc.gwin.windowTitle(), True)
    calc.gwin.hide()
    session.save("rdf", [(main, (0, 0)), (graph, place)])

    # ---- what the RDF weights are built from: f0 coefficients, f' and f'' -------
    session.use_theme(LIGHT)
    main = session.main()
    calc._show_coef_popup()
    fit_table(calc.coef_pop, calc.coef_tbl)
    coefficients = session.popup(calc.coef_pop)
    calc.coef_pop.hide()
    calc._show_anom_popup()
    anomalous = session.popup(calc.anom_pop)
    calc.anom_pop.hide()
    session.save("scattering", [(main, (0, 0)), (coefficients, (330, 96)), (anomalous, (700, 520))])
    session.window.close()


if __name__ == "__main__":
    main()
