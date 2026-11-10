"""Real-Qt regression tests for the standard-library visual pilot.

Run inside the real repository/runtime. These tests do not calculate, import a
workbook, open external URLs, or write user project/record databases.
"""
from __future__ import annotations
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from datetime import date
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget, QHeaderView
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute


class StandardLibraryPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        cls.temp = tempfile.TemporaryDirectory(prefix="ghg-standard-pilot-")
        cls.catalog_path = Path(cls.temp.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.service = CatalogQueryService(SQLiteCatalogRepository(cls.catalog_path), as_of=date(2026, 9, 12))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.service,
            record_repository=InMemoryRecordRepository(),
        )
        self.window.resize(1180, 720)
        self.window.show()
        self.shell = self.window.centralWidget()
        self.shell.navigate(AppRoute.STANDARDS)
        self.page = self.shell.pages[AppRoute.STANDARDS]
        self.flush()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.flush()

    def flush(self):
        for _ in range(6):
            self.application.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.application.processEvents()

    def open_standard(self, standard_id):
        self.page.search_input.clear()
        self.flush()
        row = next(i for i in range(self.page.standard_table.rowCount())
                   if self.page.standard_table.item(i, 0).data(Qt.ItemDataRole.UserRole) == standard_id)
        self.page.standard_table.cellActivated.emit(row, 0)
        self.flush()

    def test_five_columns_keep_full_data_and_compact_badges(self):
        table = self.page.standard_table
        self.assertEqual(table.columnCount(), 5)
        self.assertEqual(self.page.status_filter.count(), 5)
        self.assertEqual(table.verticalHeader().defaultSectionSize(), 48)
        self.assertEqual(table.columnWidth(4), 160)
        self.assertIn("font-size: 14px", table.styleSheet())
        for row in range(table.rowCount()):
            for column in range(5):
                self.assertIsNotNone(table.item(row, column))
            badge_host = table.cellWidget(row, 2)
            self.assertIsNotNone(badge_host)
            badge = badge_host.findChild(QLabel, "standardStatusBadge")
            self.assertIsNotNone(badge)
            self.assertEqual(badge.text(), table.item(row, 2).text())
            self.assertLessEqual(badge.height(), table.rowHeight(row))

    def test_detail_has_one_copy_of_title_number_and_separate_statuses(self):
        self.open_standard("gbt_32151_34_2024")
        detail = self.service.get_standard_detail("gbt_32151_34_2024")
        visible = [x.text() for x in self.page.detail_host.findChildren(QLabel) if x.isVisible()]
        self.assertEqual(visible.count(detail.standard.standard_number), 1)
        self.assertEqual(visible.count(detail.standard.standard_name), 1)
        for object_name in ("standardDetailNumber", "standardDetailName", "standardDetailStatus",
                            "standardSoftwareSupport", "standardDetailVersion", "standardPublicationDate",
                            "standardImplementationDate", "standardAbolitionDate"):
            self.assertIsNotNone(self.page.findChild(QLabel, object_name), object_name)
        self.assertEqual(self.page.findChild(QLabel, "standardSoftwareSupport").text(), "已实现，待验收")
        self.assertIsNone(self.page.detail_host.findChild(QTabWidget))
        self.assertFalse(any("不设置详情页签" in text for text in visible))

    def test_filter_no_result_then_restore_and_return(self):
        self.page.search_input.setText("不存在的标准名称")
        self.flush()
        self.assertEqual(self.page.standard_table.rowCount(), 0)
        self.assertEqual(self.page.result_summary.text(), "没有找到匹配的标准。")
        self.page.search_input.setText("32151.34")
        self.flush()
        self.assertEqual(self.page.standard_table.rowCount(), 1)
        self.page.standard_table.cellActivated.emit(0, 1)
        self.flush()
        self.page.findChild(QPushButton, "backToStandardListButton").click()
        self.flush()
        self.assertEqual(self.page.search_input.text(), "32151.34")
        self.assertIs(self.page.view_stack.currentWidget(), self.page.list_view)

    def test_detail_navigation_does_not_accumulate_old_action_widgets(self):
        for standard_id in ("gbt_32151_34_2024", "gbt_32150_2025", "gbt_32151_1_2015"):
            if self.page.view_stack.currentWidget() is self.page.detail_host:
                self.page.findChild(QPushButton, "backToStandardListButton").click()
                self.flush()
            self.open_standard(standard_id)
            self.assertEqual(len(self.page.findChildren(QPushButton, "startAccountingButton")), 1)
            self.assertEqual(len(self.page.findChildren(QPushButton, "viewOfficialSourceButton")), 1)
            self.assertEqual(self.page.findChild(QPushButton, "startAccountingButton").property("standardId"), standard_id)

    def test_styles_stay_page_local_and_do_not_modify_home(self):
        home = self.shell.pages[AppRoute.HOME]
        before = (self.window.styleSheet(), self.shell.styleSheet(), home.styleSheet())
        self.open_standard("gbt_32151_34_2024")
        self.shell.navigate(AppRoute.HOME)
        self.flush()
        self.assertEqual(before, (self.window.styleSheet(), self.shell.styleSheet(), home.styleSheet()))

    def test_metadata_and_actions_fit_supported_window_sizes(self):
        self.open_standard("gbt_32151_34_2024")
        for width, height in ((1180, 720), (1440, 1000)):
            self.window.resize(width, height)
            self.flush()
            for object_name in ("backToStandardListButton", "startAccountingButton", "viewOfficialSourceButton"):
                button = self.page.findChild(QPushButton, object_name)
                self.assertGreaterEqual(button.width(), button.fontMetrics().horizontalAdvance(button.text()) + 16)
            title = self.page.findChild(QLabel, "standardDetailName")
            self.assertTrue(title.wordWrap())
            self.assertLessEqual(title.geometry().right(), title.parentWidget().width())

    def test_narrow_name_width_scroll_and_wide_restore_preserve_standard_navigation(self):
        table = self.page.standard_table
        self.page.search_input.setText("32151.34")
        self.flush()
        selected_status = self.page.status_filter.currentIndex()
        fixed_widths = tuple(table.columnWidth(i) for i in (0, 2, 3, 4))
        for width, height in ((960, 600), (1440, 900), (960, 600)):
            self.window.resize(width, height)
            self.flush()
            with self.subTest(width=width):
                self.assertEqual(table.columnCount(), 5)
                self.assertGreaterEqual(table.columnWidth(1), 240)
                self.assertGreaterEqual(table.columnWidth(1), table.fontMetrics().horizontalAdvance("标准名称") + 24)
                self.assertLessEqual(table.rowHeight(0), 120)
                self.assertEqual(tuple(table.columnWidth(i) for i in (0, 2, 3, 4)), fixed_widths)
                self.assertEqual(table.columnWidth(4), 160)
                self.assertEqual(self.page.search_input.text(), "32151.34")
                self.assertEqual(self.page.status_filter.currentIndex(), selected_status)
                self.assertEqual(table.rowCount(), 1)
                self.assertEqual(self.shell.main_scroll_area.horizontalScrollBar().maximum(), 0)
                if width == 960:
                    self.assertEqual(table.horizontalHeader().sectionResizeMode(1), QHeaderView.ResizeMode.Fixed)
                    bar = table.horizontalScrollBar()
                    self.assertGreater(bar.maximum(), 0)
                    bar.setValue(bar.maximum())
                    self.flush()
                    support_rect = table.visualItemRect(table.item(0, 4))
                    self.assertTrue(table.viewport().rect().contains(support_rect.center()))
                    self.assertEqual(table.item(0, 4).text(), "已实现，待验收")
                    bar.setValue(0)
                    self.flush()
                else:
                    self.assertEqual(table.horizontalHeader().sectionResizeMode(1), QHeaderView.ResizeMode.Stretch)
                    self.assertEqual(table.horizontalScrollBar().maximum(), 0)
                    self.assertGreater(table.columnWidth(1), 240)
                # Both number and name remain real entry points after each resize.
                for column in (0, 1):
                    rect = table.visualItemRect(table.item(0, column))
                    QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
                    self.flush()
                    self.assertIs(self.page.view_stack.currentWidget(), self.page.detail_host)
                    self.assertEqual(self.page.selected_standard_id, "gbt_32151_34_2024")
                    self.page.findChild(QPushButton, "backToStandardListButton").click()
                    self.flush()
                    self.assertEqual(self.page.search_input.text(), "32151.34")
                    self.assertEqual(self.page.status_filter.currentIndex(), selected_status)


if __name__ == "__main__":
    unittest.main()
