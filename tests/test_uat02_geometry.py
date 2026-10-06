"""Focused geometry regressions for dynamic accounting rows in UAT02."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import EmissionSourceStatus, InMemoryRecordRepository
from packages.ui.view_models import AppRoute


class UAT02GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(cls.catalog_path),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_directory.cleanup()

    def setUp(self) -> None:
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.catalog_service,
            record_repository=InMemoryRecordRepository(),
        )
        self.window.show()
        self.shell = self.window.centralWidget()
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.page = self.shell.pages[AppRoute.NEW_ACCOUNTING]

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def _process_layout_events(self) -> None:
        self.application.processEvents()
        QTest.qWait(5)
        self.application.processEvents()

    def _assert_scroll_geometry_matches_page(self) -> None:
        expected_height = max(
            self.shell.main_scroll_area.viewport().height(),
            self.shell.page_stack.sizeHint().height(),
        )
        self.assertEqual(self.shell.scroll_host.height(), expected_height)

    def test_dynamic_fuel_rows_resize_scroll_host_across_expand_collapse(self) -> None:
        status = self.page._source_statuses["CAR-SRC-FUEL-001"]
        status.setCurrentIndex(status.findData(EmissionSourceStatus.INVOLVED))
        self._process_layout_events()

        card = self.page._source_cards["CAR-SRC-FUEL-001"]
        scrollbar = self.shell.main_scroll_area.verticalScrollBar()
        self.assertTrue(card.is_expanded)
        self.assertEqual(len(self.page._fuel_rows), 1)
        self._assert_scroll_geometry_matches_page()

        previous_height = self.shell.scroll_host.height()
        for expected_count in (5, 20):
            while len(self.page._fuel_rows) < expected_count:
                self.page._add_fuel_row()
            self._process_layout_events()
            self.assertEqual(len(self.page._fuel_rows), expected_count)
            self._assert_scroll_geometry_matches_page()
            self.assertGreater(self.shell.scroll_host.height(), previous_height)
            self.assertGreater(scrollbar.maximum(), 0)
            previous_height = self.shell.scroll_host.height()

        expanded_height = self.shell.scroll_host.height()
        expanded_scroll_range = scrollbar.maximum()
        self.page._remove_fuel_row(self.page._fuel_rows[10])
        self._process_layout_events()
        self.assertEqual(len(self.page._fuel_rows), 19)
        self._assert_scroll_geometry_matches_page()
        self.assertLess(self.shell.scroll_host.height(), expanded_height)
        self.assertGreater(scrollbar.maximum(), 0)

        card.set_expanded(False)
        self._process_layout_events()
        collapsed_height = self.shell.scroll_host.height()
        collapsed_scroll_range = scrollbar.maximum()
        self.assertLess(collapsed_height, expanded_height)
        self.assertLess(collapsed_scroll_range, expanded_scroll_range)

        card.set_expanded(True)
        self._process_layout_events()
        self._assert_scroll_geometry_matches_page()
        self.assertGreater(self.shell.scroll_host.height(), collapsed_height)
        self.assertGreater(scrollbar.maximum(), collapsed_scroll_range)

        scrollbar.setValue(scrollbar.maximum())
        self._process_layout_events()
        self.assertEqual(scrollbar.value(), scrollbar.maximum())
        self.assertLessEqual(self.shell.scroll_host.y(), -scrollbar.maximum())


if __name__ == "__main__":
    unittest.main()
