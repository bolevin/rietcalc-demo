"""The Qt window: a passive view.  It shows what it is given and reports clicks."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    DoubleSpinBox,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    NavigationItemPosition,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    SegmentedWidget,
    StrongBodyLabel,
    TableWidget,
    Theme,
    isDarkTheme,
    setFont,
    setTheme,
)
from qfluentwidgets import FluentIcon as Icon

from rietcalc_demo import __version__
from rietcalc_demo.domain import MAX_RANGE
from rietcalc_demo.ui.plot import HistogramPanel
from rietcalc_demo.ui.view import (
    Metric,
    ResultViewModel,
    SettingsInput,
    StructureViewModel,
)

_MUTED = ("#6b6b6b", "#a6a6a6")  # light theme, dark theme
_ACCENT = ("#0067c0", "#4cc2ff")
_EMPTY = "—"
_MONO = QFont("Consolas", 10)

ABOUT = f"""\
RietCalc Demo {__version__}

A crystal structure is given by its unit cell, its space-group operators and a
handful of independent atoms.  Everything a chemist wants to know about bonding -
which atoms touch, how far apart they are, how many neighbours each atom has -
has to be computed from that, and every result inherits the uncertainty of the
refined cell and coordinates.

This program reads a CIF and reports
  - every interatomic distance in a chosen range, with its estimated standard
    deviation propagated from the e.s.d.'s of the cell and of both atoms;
  - the symmetry-unique bonds of each atom and its coordination number;
  - the multiplicity of every site and the cell volume with its e.s.d.

It is a demonstration version of RietCalc by Aleksandr A. Levin and Boris A. Levin.
The full program - a port of the FORTRAN original, verified number by number
against it - adds bond angles, radial distribution functions with anomalous and
form-factor weighting, bond-valence sums, thermal-motion corrections, X-ray
density and batch processing.

Free software under the GNU General Public License, version 3 or later.
"""


class Actions(Protocol):
    """The intents the window forwards; implemented by the presenter."""

    def open_file(self) -> None: ...

    def open_sample(self) -> None: ...

    def calculate(self) -> None: ...

    def save_report(self) -> None: ...


class MetricCard(CardWidget):
    """Caption, a large value, and a line of context underneath."""

    def __init__(self, caption: str, *, headline: bool = False) -> None:
        super().__init__()
        self.setMinimumHeight(104)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        self.caption = CaptionLabel(caption)
        self.caption.setTextColor(*_MUTED)
        self.value = BodyLabel(_EMPTY)
        setFont(self.value, 26 if headline else 22, QFont.Weight.DemiBold)
        if headline:
            self.value.setTextColor(*_ACCENT)
        self.hint = CaptionLabel("")
        self.hint.setTextColor(*_MUTED)
        layout.addWidget(self.caption)
        layout.addStretch(1)
        layout.addWidget(self.value)
        layout.addWidget(self.hint)

    def show_metric(self, metric: Metric | None) -> None:
        if metric is not None:
            self.caption.setText(metric.caption)
        self.value.setText(metric.value if metric else _EMPTY)
        self.hint.setText(metric.hint if metric else "")


def _titled_card(title: str) -> tuple[CardWidget, QVBoxLayout]:
    card = CardWidget()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 16)
    layout.setSpacing(10)
    layout.addWidget(StrongBodyLabel(title))
    return card, layout


def _table(headers: tuple[str, ...]) -> TableWidget:
    table = TableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(list(headers))
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setBorderVisible(True)
    table.setBorderRadius(8)
    table.setWordWrap(False)
    table.verticalHeader().setDefaultSectionSize(34)  # dense: show the whole table
    return table


def _size_columns(table: TableWidget, stretch: tuple[int, ...]) -> None:
    """Stretch the given columns, size the others to their content."""
    header = table.horizontalHeader()
    for column in range(table.columnCount()):
        header.setSectionResizeMode(
            column,
            QHeaderView.ResizeMode.Stretch
            if column in stretch
            else QHeaderView.ResizeMode.ResizeToContents,
        )


def _fill(table: TableWidget, rows: list[tuple[str, ...]], *, numeric_from: int = 1) -> None:
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            item = QTableWidgetItem(text)
            if c >= numeric_from:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(r, c, item)


class AnalysisPage(QWidget):
    METRICS = ("Atoms in the cell", "Contacts", "Shortest bond, Å", "Unique bonds")

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("analysisPage")
        number_locale = QLocale.c()  # "." as decimal separator, everywhere

        # ---- left column: input -------------------------------------
        structure_card, structure_box = _titled_card("Structure")
        self.file_label = BodyLabel("No file loaded")
        self.title_label = CaptionLabel("")
        self.title_label.setWordWrap(True)
        self.title_label.setTextColor(*_MUTED)
        self.summary_label = CaptionLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextColor(*_MUTED)
        self.open_button = PushButton(Icon.FOLDER, "Open CIF")
        self.sample_button = PushButton(Icon.DOCUMENT, "Load sample")
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.sample_button)
        for widget in (self.file_label, self.title_label, self.summary_label):
            structure_box.addWidget(widget)
        structure_box.addLayout(buttons)

        range_card, range_box = _titled_card("Distance range")
        self.r_min_spin = DoubleSpinBox()
        self.r_max_spin = DoubleSpinBox()
        for spin in (self.r_min_spin, self.r_max_spin):
            spin.setDecimals(2)
            spin.setSingleStep(0.1)
            spin.setRange(0.0, MAX_RANGE)
            spin.setLocale(number_locale)
        self.r_min_spin.setValue(0.0)
        self.r_max_spin.setValue(3.2)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for row, (caption, widget) in enumerate(
            (("R min, Å", self.r_min_spin), ("R max, Å", self.r_max_spin))
        ):
            grid.addWidget(BodyLabel(caption), row, 0)
            grid.addWidget(widget, row, 1)
        grid.setColumnStretch(0, 1)
        range_box.addLayout(grid)
        hint = CaptionLabel(
            "Every atom of the crystal within the range is listed, with an e.s.d. "
            "propagated from the cell and from both atoms."
        )
        hint.setWordWrap(True)
        hint.setTextColor(*_MUTED)
        range_box.addWidget(hint)

        self.calculate_button = PrimaryPushButton(Icon.PLAY, "Calculate")
        self.save_button = PushButton(Icon.SAVE, "Save report")
        self.calculate_button.setEnabled(False)
        self.save_button.setEnabled(False)

        left = QVBoxLayout()
        left.setSpacing(12)
        left.addWidget(structure_card)
        left.addWidget(range_card)
        left.addWidget(self.calculate_button)
        left.addWidget(self.save_button)
        left.addStretch(1)
        left.setContentsMargins(0, 0, 0, 0)
        left_holder = QWidget()
        left_holder.setLayout(left)
        left_holder.setFixedWidth(344)

        # ---- right column: results ----------------------------------
        self.headline_card = MetricCard("Cell volume, Å³", headline=True)
        self.metric_cards = [MetricCard(caption) for caption in self.METRICS]
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(self.headline_card, 4)
        for card in self.metric_cards:
            metrics.addWidget(card, 3)

        self.bonds_table = _table(("Atom", "CN", "Bond", "Distance, Å", "Multiplicity"))
        _size_columns(self.bonds_table, stretch=(2, 3))

        self.histogram = HistogramPanel()
        histogram_card = CardWidget()
        histogram_layout = QVBoxLayout(histogram_card)
        histogram_layout.setContentsMargins(6, 6, 6, 6)
        histogram_layout.addWidget(self.histogram)

        # one row across the page: a, b, c, alpha, beta, gamma and the volume
        self.cell_table = _table(("a",))
        self.cell_table.setFixedHeight(84)
        self.cell_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.atoms_table = _table(
            ("Atom", "El", "x", "y", "z", "Occupancy", "Multiplicity", "Position")
        )
        _size_columns(self.atoms_table, stretch=(2, 3, 4))
        # the unit-cell content: what the operators make of the independent atoms
        self.cell_atoms_table = _table(("Atom", "Operator", "x", "y", "z"))
        _size_columns(self.cell_atoms_table, stretch=(1,))
        self.operators_label = BodyLabel("")
        self.operators_label.setFont(_MONO)
        self.operators_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        operators_card, operators_box = _titled_card("Symmetry operators")
        operators_box.addWidget(self.operators_label)
        operators_box.addStretch(1)
        operators_card.setFixedWidth(300)
        lower = QHBoxLayout()
        lower.setSpacing(12)
        lower.addWidget(self.cell_atoms_table, 1)
        lower.addWidget(operators_card)
        structure_page = QWidget()
        structure_layout = QVBoxLayout(structure_page)
        structure_layout.setContentsMargins(0, 0, 0, 0)
        structure_layout.setSpacing(12)
        structure_layout.addWidget(self.cell_table)
        structure_layout.addWidget(self.atoms_table)
        structure_layout.addLayout(lower, 1)

        self.report = PlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setFont(_MONO)
        self.report.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        self.report.setPlaceholderText("The report appears here after the calculation.")

        self.stack = QStackedWidget()
        self.tabs = SegmentedWidget()
        for key, title, widget in (
            ("structure", "Structure", structure_page),
            ("bonds", "Bonds", self.bonds_table),
            ("histogram", "Histogram", histogram_card),
            ("report", "Report", self.report),
        ):
            self.stack.addWidget(widget)
            self.tabs.addItem(key, title, lambda w=widget: self.stack.setCurrentWidget(w))
        self.tabs.setCurrentItem("structure")
        tabs_row = QHBoxLayout()
        tabs_row.addWidget(self.tabs)
        tabs_row.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(12)
        right.addLayout(metrics)
        right.addLayout(tabs_row)
        right.addWidget(self.stack, 1)

        page = QHBoxLayout(self)
        page.setContentsMargins(24, 16, 24, 24)
        page.setSpacing(20)
        page.addWidget(left_holder)
        page.addLayout(right, 1)

    def show_tab(self, key: str) -> None:
        self.tabs.setCurrentItem(key)
        index = ("structure", "bonds", "histogram", "report").index(key)
        self.stack.setCurrentIndex(index)


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("aboutPage")
        card, box = _titled_card("About")
        text = BodyLabel(ABOUT)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(text)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.addWidget(card)
        layout.addStretch(1)


class MainWindow(FluentWindow):
    """Implements :class:`rietcalc_demo.ui.view.MainView`."""

    def __init__(self, icon: QIcon | None = None) -> None:
        super().__init__()
        self.setWindowTitle("RietCalc Demo")
        if icon is not None:
            self.setWindowIcon(icon)
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        self.page = AnalysisPage()
        self.about = AboutPage()
        self.addSubInterface(self.page, Icon.HOME, "Distances")
        self.addSubInterface(self.about, Icon.INFO, "About", NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=Icon.CONSTRACT,
            text="Light / dark",
            onClick=self.toggle_theme,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.page.histogram.set_dark(isDarkTheme())

    def bind(self, actions: Actions) -> None:
        self._actions = actions  # the connections below do not keep it alive
        self.page.open_button.clicked.connect(actions.open_file)
        self.page.sample_button.clicked.connect(actions.open_sample)
        self.page.calculate_button.clicked.connect(actions.calculate)
        self.page.save_button.clicked.connect(actions.save_report)

    def toggle_theme(self) -> None:
        self.set_dark(not isDarkTheme())

    def set_dark(self, dark: bool) -> None:
        setTheme(Theme.DARK if dark else Theme.LIGHT)
        self.page.histogram.set_dark(dark)

    # ---- MainView ------------------------------------------------------
    def show_structure(self, structure: StructureViewModel) -> None:
        page = self.page
        page.file_label.setText(structure.file_name)
        page.title_label.setText(structure.title)
        page.title_label.setVisible(bool(structure.title))
        page.summary_label.setText(structure.summary)
        page.cell_table.setColumnCount(len(structure.cell))
        page.cell_table.setHorizontalHeaderLabels([name for name, _value in structure.cell])
        _fill(page.cell_table, [tuple(value for _name, value in structure.cell)], numeric_from=0)
        _size_columns(page.cell_table, stretch=tuple(range(len(structure.cell))))
        _fill(
            page.atoms_table,
            [
                (a.label, a.element, a.x, a.y, a.z, a.occupancy, a.multiplicity, a.position)
                for a in structure.atoms
            ],
            numeric_from=2,
        )
        page.operators_label.setText(
            "\n".join(f"{k + 1:>2}  {op}" for k, op in enumerate(structure.operators))
        )
        _fill(
            page.cell_atoms_table,
            [(r.label, r.operator, r.x, r.y, r.z) for r in structure.cell_atoms],
            numeric_from=2,
        )
        page.calculate_button.setEnabled(True)
        page.show_tab("structure")

    def show_result(self, result: ResultViewModel) -> None:
        page = self.page
        page.headline_card.show_metric(result.headline)
        for card, metric in zip(page.metric_cards, result.metrics, strict=True):
            card.show_metric(metric)
        _fill(
            page.bonds_table,
            [(b.source, b.coordination, b.bond, b.distance, b.multiplicity) for b in result.bonds],
            numeric_from=3,
        )
        page.histogram.set_histogram(result.histogram)
        page.report.setPlainText(result.report)
        page.save_button.setEnabled(True)
        page.show_tab("bonds")

    def clear_result(self) -> None:
        page = self.page
        page.headline_card.show_metric(None)
        for card in page.metric_cards:
            card.show_metric(None)
        page.bonds_table.setRowCount(0)
        page.histogram.clear()
        page.report.clear()
        page.save_button.setEnabled(False)

    def show_error(self, title: str, message: str) -> None:
        InfoBar.error(
            title, message, duration=8000, position=InfoBarPosition.TOP_RIGHT, parent=self
        )

    def show_success(self, title: str, message: str) -> None:
        InfoBar.success(
            title, message, duration=5000, position=InfoBarPosition.TOP_RIGHT, parent=self
        )

    def settings(self) -> SettingsInput:
        return SettingsInput(r_min=self.page.r_min_spin.value(), r_max=self.page.r_max_spin.value())

    def ask_open_path(self) -> Path | None:
        name, _ = QFileDialog.getOpenFileName(
            self, "Open structure", "", "Crystallographic Information File (*.cif);;All files (*)"
        )
        return Path(name) if name else None

    def ask_save_path(self, suggested: Path) -> Path | None:
        name, _ = QFileDialog.getSaveFileName(
            self, "Save report", str(suggested), "Text file (*.txt);;All files (*)"
        )
        return Path(name) if name else None
