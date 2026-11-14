"""Render the screenshots of the demo used in the README.

    python tools/make_screenshots.py

The window is laid out by the real Windows platform plugin but never appears on
screen; it is rendered at 2x into ``docs/img``.  (The ``offscreen`` plugin is no
use here: it has no fonts, so every label would come out as empty boxes.)  Every
picture shows the bundled synthetic structure, so the result is reproducible.

Screenshots of the full program are made separately by
``tools/make_full_screenshots.py``.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme, setThemeColor

from rietcalc_demo.main import build_service, data_path
from rietcalc_demo.ui.main_window import MainWindow
from rietcalc_demo.ui.presenter import MainPresenter

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"
SCALE = 2
SIZE = (1280, 800)
PAGE = {False: "#f3f3f3", True: "#202020"}  # window background per theme
LIGHT_BACKDROP = ("#cfe3f7", "#8fb8e8")
DARK_BACKDROP = ("#1b2a41", "#0b1220")


def settle(app: QApplication, milliseconds: int = 600) -> None:
    """Let the window finish what it is doing, animations included.

    A fixed number of event-loop rounds is not enough: the tab indicator slides to
    its new place with a timed animation, and a picture taken too early shows one
    tab highlighted and another tab's content.
    """
    deadline = time.monotonic() + milliseconds / 1000
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)


def grab(window: MainWindow, dark: bool) -> Image.Image:
    pixmap = QPixmap(window.size() * SCALE)
    pixmap.setDevicePixelRatio(SCALE)
    pixmap.fill(QColor(PAGE[dark]))
    window.render(pixmap, QPoint(0, 0))
    raw = OUT / "_raw.png"
    pixmap.save(str(raw))
    image = Image.open(raw).convert("RGBA")
    image.load()
    raw.unlink()
    return image


def framed(shot: Image.Image, top: str, bottom: str, margin: int = 110) -> Image.Image:
    """The window on a gradient backdrop with rounded corners and a soft shadow."""
    radius = 9 * SCALE
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *shot.size], radius=radius, fill=255)
    width, height = shot.width + 2 * margin, shot.height + 2 * margin

    canvas = Image.new("RGBA", (width, height))
    a, b = (Image.new("RGBA", (1, 1), c).getpixel((0, 0)) for c in (top, bottom))
    draw = ImageDraw.Draw(canvas)
    for y in range(height):
        t = y / (height - 1)
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(round(p + (q - p) * t) for p, q in zip(a, b, strict=True)),
        )

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [margin, margin + 18, margin + shot.width, margin + shot.height + 18],
        radius=radius,
        fill=(0, 0, 0, 120),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
    canvas.paste(shot, (margin, margin), mask)
    return canvas.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setFont(QFont("Segoe UI", 10))
    setTheme(Theme.LIGHT)
    setThemeColor("#0067c0")

    window = MainWindow(QIcon(str(data_path("icon.ico"))))
    window.setMicaEffectEnabled(False)  # Mica is composed by the OS, not by Qt
    presenter = MainPresenter(window, build_service(), data_path("sample_structure.cif"))
    window.bind(presenter)
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.resize(*SIZE)
    window.show()
    settle(app)

    presenter.open_sample()
    settle(app)
    shots: dict[str, tuple[Image.Image, tuple[str, str]]] = {
        "structure": (grab(window, False), LIGHT_BACKDROP)
    }

    presenter.calculate()  # switches to the bond table
    settle(app)
    shots["bonds"] = (grab(window, False), LIGHT_BACKDROP)

    window.set_dark(True)
    window.page.show_tab("histogram")
    settle(app)
    shots["histogram"] = (grab(window, True), DARK_BACKDROP)

    window.page.show_tab("bonds")
    settle(app)
    shots["bonds-dark"] = (grab(window, True), DARK_BACKDROP)

    window.set_dark(False)
    window.page.show_tab("report")
    settle(app)
    shots["report"] = (grab(window, False), LIGHT_BACKDROP)

    for name, (shot, backdrop) in shots.items():
        target = OUT / f"demo-{name}.png"
        framed(shot, *backdrop).save(target, optimize=True)
        print(f"wrote {target}  {shot.width}x{shot.height}")
    window.close()


if __name__ == "__main__":
    main()
