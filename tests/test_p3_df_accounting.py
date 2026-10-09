"""P3-DF accounting presentation regression checks.

These tests exercise the real desktop page with an isolated Catalog and an
in-memory formal Record repository. They cover layout contracts and the
state-preserving behavior of dynamic source rows without reproducing business
calculation logic.
"""

from __future__ import annotations

import gc
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QPoint
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QPushButton, QScrollArea

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


FUEL_SOURCE_ID = "CAR-SRC-FUEL-001"


class P3DFAccountingLayoutTests(unittest.TestCase):
    """Small layout and dynamic-row regressions for the F accounting page."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = build_catalog_database(
            DEFAULT_SOURCE_PATH,
            Path(cls.temp_directory.name) / "catalog.sqlite",
        )
        cls.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(cls.catalog_path),
            as_of=date(2026, 9, 23),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        gc.collect()
        cls.temp_directory.cleanup()

    def setUp(self) -> None:
        self.records = InMemoryRecordRepository()
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.catalog_service,
            record_repository=self.records,
        )
        self.window.resize(1180, 720)
        self.window.show()
        self.application.processEvents()
        shell = self.window.centralWidget()
        self.assertIsInstance(shell, AppShell)
        assert isinstance(shell, AppShell)
        self.shell = shell
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        page = self.shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(page, CarbonMaterialAccountingPage)
        assert isinstance(page, CarbonMaterialAccountingPage)
        self.page = page

    def tearDown(self) -> None:
        # Avoid QMainWindow close confirmation; this fixture has no user
        # project, and deferred deletion also releases Qt child widgets.
        self.window.hide()
        self.window.deleteLater()
        self.application.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.application.processEvents()
        gc.collect()

    def _settle(self) -> None:
        self.application.processEvents()
        self.application.processEvents()

    def _set_fuel_enabled(self, enabled: bool) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_fuel")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        for _ in range(3):
            if self.page._source_is_enabled(FUEL_SOURCE_ID) is enabled:
                return
            toggle.click()
            self._settle()
        self.fail(f"燃料来源未达到预期状态: enabled={enabled!r}")

    def test_result_card_precedes_calculation_basis_and_standard_title_wraps(self) -> None:
        page = self.page
        result_index = page.body_layout.indexOf(page.result_card)
        basis_index = page.body_layout.indexOf(page.process_card)
        self.assertGreaterEqual(result_index, 0)
        self.assertGreaterEqual(basis_index, 0)
        self.assertLess(result_index, basis_index)

        standard_label = page.standard_id_label
        self.assertIsInstance(standard_label, QLabel)
        self.assertTrue(standard_label.wordWrap())
        self.assertTrue(standard_label.hasHeightForWidth())
        self.assertGreater(
            standard_label.heightForWidth(260),
            standard_label.fontMetrics().lineSpacing(),
        )

    def test_dynamic_fuel_row_keeps_precision_and_source_when_reenabled(self) -> None:
        self._set_fuel_enabled(True)
        self.page.add_fuel_button.click()
        self._settle()
        self.assertGreaterEqual(len(self.page._fuel_rows), 2)

        row = self.page._fuel_rows[-1]
        precise_activity = "0.123456789012345678901234"
        source_reference = "燃料检测报告-P3-DF-动态行"
        row.activity.setText(precise_activity)
        row.source_reference.setText(source_reference)
        direct_index = row.carbon_basis.findData("DIRECT")
        measured_index = row.direct_carbon_source.findData("MEASURED")
        self.assertGreaterEqual(direct_index, 0)
        self.assertGreaterEqual(measured_index, 0)
        row.carbon_basis.setCurrentIndex(direct_index)
        row.direct_carbon_source.setCurrentIndex(measured_index)
        self._settle()

        self.assertGreater(row.sizeHint().height(), 0)
        self.assertTrue(row.remove_button.isVisible())

        self._set_fuel_enabled(False)
        self.assertFalse(self.page._source_is_enabled(FUEL_SOURCE_ID))
        self._set_fuel_enabled(True)
        self.assertTrue(self.page._source_is_enabled(FUEL_SOURCE_ID))

        self.assertIn(row, self.page._fuel_rows)
        self.assertEqual(row.activity.text(), precise_activity)
        self.assertEqual(row.source_reference.text(), source_reference)
        self.assertEqual(row.direct_carbon_source.currentData(), "MEASURED")
        self.assertTrue(row.isVisible())
        self.assertGreater(row.sizeHint().height(), 0)

    def test_compact_status_area_remains_visible_and_reachable(self) -> None:
        page = self.page
        status_bar = page.findChild(QFrame, "calculationStatusBar")
        self.assertIsNotNone(status_bar)
        assert status_bar is not None
        self.assertTrue(status_bar.isVisible())
        self.assertGreater(status_bar.sizeHint().height(), 0)

        status_layout = status_bar.layout()
        self.assertIsInstance(status_layout, QGridLayout)
        assert isinstance(status_layout, QGridLayout)
        self.assertIsNotNone(status_layout.itemAtPosition(1, 0))
        self.assertIs(status_layout.itemAtPosition(0, 4).widget(), page.calculate_button)
        self.assertTrue(page.calculation_status_hint.wordWrap())
        self.assertTrue(page.calculate_button.isVisible())

        scroll_area = self.shell.findChild(QScrollArea, "mainScrollArea")
        self.assertIsNotNone(scroll_area)
        assert scroll_area is not None
        self.shell.update_content_geometry()
        self._settle()
        scroll_area.ensureWidgetVisible(status_bar)
        self._settle()

        status_top_left = status_bar.mapTo(scroll_area.viewport(), QPoint(0, 0))
        status_rect = status_bar.rect().translated(status_top_left)
        self.assertTrue(scroll_area.viewport().rect().intersects(status_rect))
