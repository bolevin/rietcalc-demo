"""The distance histogram: how many contacts fall into each 0.05 A bin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedLayout, QWidget
from qfluentwidgets import BodyLabel

from rietcalc_demo.ui.view import HistogramViewModel

pg.setConfigOptions(antialias=True)


@dataclass(frozen=True, slots=True)
class PlotPalette:
    background: str
    text: str
    axis: str
    bar: str
    edge: str
    grid: int  # alpha of the grid lines, 0-255


LIGHT = PlotPalette(
    background="#fbfbfb", text="#3b3b3b", axis="#b4b4b4", bar="#1565c0", edge="#0d3c75", grid=40
)
DARK = PlotPalette(
    background="#2b2b2b", text="#d6d6d6", axis="#5a5a5a", bar="#5aa9f8", edge="#9ccbff", grid=50
)


class HistogramPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: HistogramViewModel | None = None
        self._palette = LIGHT

        self._graphics = pg.GraphicsLayoutWidget()
        self._plot = self._graphics.addPlot()
        self._graphics.ci.setContentsMargins(4, 8, 12, 4)
        self._plot.getAxis("left").setWidth(56)
        self._plot.setMenuEnabled(False)
        self._plot.hideButtons()

        self._placeholder = BodyLabel("Calculate to see the distance histogram.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._graphics)
        self._apply_palette()

    def set_histogram(self, data: HistogramViewModel) -> None:
        self._data = data
        self._draw()
        self._plot.enableAutoRange()
        self._stack.setCurrentWidget(self._graphics)

    def clear(self) -> None:
        self._data = None
        self._plot.clear()
        self._stack.setCurrentWidget(self._placeholder)

    def set_dark(self, dark: bool) -> None:
        self._palette = DARK if dark else LIGHT
        self._apply_palette()
        self._draw()

    # pyqtgraph resolves colours when an item is created, so a theme change
    # re-applies every pen and rebuilds the bars.
    def _apply_palette(self) -> None:
        p = self._palette
        self._graphics.setBackground(p.background)
        for name in ("left", "bottom"):
            axis = self._plot.getAxis(name)
            axis.setPen(p.axis)
            axis.setTextPen(p.text)
        self._plot.showGrid(x=True, y=True, alpha=p.grid / 255)
        self._plot.setLabel("left", "Number of contacts", color=p.text)
        self._plot.setLabel("bottom", "Distance, Å", color=p.text)

    def _draw(self) -> None:
        self._plot.clear()
        if self._data is None:
            return
        p, v = self._palette, self._data
        counts = np.asarray(v.counts)
        filled = counts > 0  # an empty bin would leave a stray line on the axis
        self._plot.addItem(
            pg.BarGraphItem(
                x=np.asarray(v.centres)[filled],
                height=counts[filled],
                width=v.width * 0.86,
                brush=pg.mkBrush(p.bar),
                pen=pg.mkPen(p.edge, width=1),
            )
        )
        self._plot.setTitle(v.caption, color=p.text, size="10pt")
