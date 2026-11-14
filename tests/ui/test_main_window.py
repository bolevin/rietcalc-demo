"""The Qt window wired to the real presenter and service.

These tests check the wiring - buttons, tables, tabs, theme - and run without a
screen.  How the window LOOKS is checked differently: the offscreen platform
has no fonts, so appearance is reviewed on the screenshots that
tools/make_screenshots.py renders with the real platform.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QLocale
from pytestqt.qtbot import QtBot
from qfluentwidgets import Theme, isDarkTheme, setTheme

from rietcalc_demo.main import build_service
from rietcalc_demo.ui.main_window import MainWindow
from rietcalc_demo.ui.plot import DARK, LIGHT
from rietcalc_demo.ui.presenter import MainPresenter


@pytest.fixture
def window(qtbot: QtBot, sample_path: Path) -> MainWindow:
    setTheme(Theme.LIGHT)
    w = MainWindow()
    qtbot.addWidget(w)
    w.bind(MainPresenter(w, build_service(), sample_path))
    return w


def test_buttons_start_disabled_and_enable_in_order(window: MainWindow) -> None:
    page = window.page
    assert not page.calculate_button.isEnabled()
    assert not page.save_button.isEnabled()
    page.sample_button.click()
    assert page.calculate_button.isEnabled()
    assert not page.save_button.isEnabled()
    page.calculate_button.click()
    assert page.save_button.isEnabled()


def test_tables_are_filled(window: MainWindow) -> None:
    page = window.page
    page.sample_button.click()
    assert page.atoms_table.rowCount() == 4
    assert page.cell_atoms_table.rowCount() == 20
    assert page.cell_table.item(0, 0).text() == "5.4423(3)"
    page.calculate_button.click()
    assert page.bonds_table.rowCount() == 32
    assert page.bonds_table.item(0, 3).text() == "2.355(6)"
    assert page.headline_card.value.text() == "223.73(2)"


def test_tabs_follow_the_workflow(window: MainWindow) -> None:
    page = window.page
    page.sample_button.click()
    assert page.stack.currentIndex() == 0  # structure first
    page.calculate_button.click()
    assert page.stack.currentIndex() == 1  # then the bonds
    page.show_tab("report")
    assert "coordination number" in page.report.toPlainText()


def test_a_new_file_clears_the_old_result(window: MainWindow) -> None:
    page = window.page
    page.sample_button.click()
    page.calculate_button.click()
    page.sample_button.click()
    assert page.bonds_table.rowCount() == 0
    assert not page.save_button.isEnabled()


def test_theme_switch_recolours_the_histogram(window: MainWindow) -> None:
    window.page.sample_button.click()
    window.page.calculate_button.click()
    histogram = window.page.histogram
    assert histogram._palette is LIGHT
    window.toggle_theme()
    assert isDarkTheme()
    assert histogram._palette is DARK
    assert histogram._graphics.backgroundBrush().color().name() == DARK.background
    window.toggle_theme()
    assert histogram._palette is LIGHT


def test_numbers_use_a_point_whatever_the_system_locale(qtbot: QtBot, sample_path: Path) -> None:
    QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
    try:
        w = MainWindow()
        qtbot.addWidget(w)
        assert w.page.r_min_spin.text() == "0.00"
        assert w.page.r_max_spin.text() == "3.20"
    finally:
        QLocale.setDefault(QLocale.c())
