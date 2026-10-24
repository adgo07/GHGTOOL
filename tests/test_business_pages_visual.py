"""Real Qt regressions for the five-page draft. Run in the project environment.

Not executed by the artifact author where PySide6 is unavailable. All stores are
isolated; existing application business entrypoints are used without live data.
"""
from __future__ import annotations
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from dataclasses import asdict, replace
from decimal import Decimal
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QAbstractItemView, QLabel, QPushButton
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.application.project_workspaces import ProjectWorkspaceService
from packages.persistence import (SQLiteCatalogRepository, SQLiteRecordRepository,
    SQLiteProjectWorkspaceRepository, SQLiteSettingsRepository, build_catalog_database)
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.export_location import ExportLocationService
from packages.ui.view_models import AppRoute
from tests.test_g07_records import _record


class BusinessPageVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ghg-five-page-")
        self.root = Path(self.temp.name)
        catalog = self.root / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, catalog)
        self.catalog = CatalogQueryService(SQLiteCatalogRepository(catalog), as_of=date(2026, 9, 12))
        self.records = SQLiteRecordRepository(self.root / "records.sqlite")
        self.records.create(_record("ui.sample.one"))
        self.records.create(_record("ui.sample.two", warning=True))
        self.projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(self.root / "projects.sqlite"))
        self.exports = ExportLocationService(SQLiteSettingsRepository(self.root / "user.sqlite"))
        self.window = create_main_window(AppConfig(catalog_database=catalog), catalog_service=self.catalog,
            record_repository=self.records, project_service=self.projects, export_location_service=self.exports)
        self.window.resize(1180, 800)
        self.window.show()
        self.shell = self.window.centralWidget()
        self.flush()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.flush()
        self.temp.cleanup()

    def flush(self):
        for _ in range(5):self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def page(self, route):
        self.shell.navigate(route)
        self.flush()
        return self.shell.pages[route]

    def test_factor_mode_owns_only_its_visible_controls(self):
        page = self.page(AppRoute.FACTORS)
        self.assertFalse(page.search_input.isVisible())
        self.assertFalse(page.search_category_filter.isVisible())
        self.assertTrue(page.browse_card.isVisible())
        page.view_mode_filter.setCurrentIndex(1)
        page.search_input.setText("0.11")
        self.flush()
        before = [(page.search_result_table.item(i, j).text() if page.search_result_table.item(i, j) else "")
                  for i in range(page.search_result_table.rowCount()) for j in range(4)]
        self.assertTrue(page.search_input.isVisible())
        page.view_mode_filter.setCurrentIndex(0)
        self.flush()
        self.assertEqual(page.search_input.text(), "0.11")
        self.assertFalse(page.search_input.isVisible())
        page.view_mode_filter.setCurrentIndex(1)
        self.flush()
        after = [(page.search_result_table.item(i, j).text() if page.search_result_table.item(i, j) else "")
                 for i in range(page.search_result_table.rowCount()) for j in range(4)]
        self.assertEqual(before, after)

    def test_factor_values_are_readonly_and_not_formatted_again(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        page.search_input.setText("0.11")
        self.flush()
        self.assertEqual(page.search_result_table.editTriggers(), QAbstractItemView.EditTrigger.NoEditTriggers)
        for i, result in enumerate(page._search_results):
            self.assertEqual(page.search_result_table.item(i, 1).text(), result.value_text or "—")
            self.assertEqual(page.search_result_table.item(i, 2).text(), result.unit or "—")

    def test_factor_standard_detail_uses_simplified_labels(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        result = next(r for r in self.catalog.search_reference_library("32151.34") if r.result_type == "standard")
        page._render_search_detail(result)
        text = "\n".join(x.text() for x in page.factor_detail_host.findChildren(QLabel))
        self.assertNotIn("發布部門", text)
        self.assertNotIn("官方資料", text)
        self.assertIn("发布部门", text)
        self.assertIn("官方资料", text)

    def test_import_controls_and_preview_are_original_business_objects(self):
        page = self.page(AppRoute.EXCEL_IMPORT)
        self.assertEqual([page.import_period_type.itemData(i) for i in range(page.import_period_type.count())],
                         [None, "ANNUAL", "MONTHLY", "CUSTOM"])
        self.assertGreaterEqual(page.preview_text.minimumHeight(), 160)
        self.assertTrue(page.preview_text.isReadOnly())
        self.assertFalse(page.calculate_button.isEnabled())
        page._select_workbook(Path("synthetic.xlsx"))
        with patch.object(page, "_preview_workbook") as preview:
            page.preview_button.click()
            preview.assert_called_once_with(Path("synthetic.xlsx"))
        self.assertFalse(page.calculate_button.isEnabled())
        self.assertEqual(len(self.records.list_all()), 2)

    def test_record_empty_search_then_restore_does_not_leave_column_span(self):
        page = self.page(AppRoute.RECORDS)
        page.search_input.setText("不存在的记录")
        self.flush()
        self.assertEqual(len(page._records), 0)
        self.assertEqual(page.record_list.columnSpan(0, 0), 7)
        page.search_input.clear()
        self.flush()
        self.assertEqual(len(page._records), 2)
        self.assertEqual(page.record_list.columnSpan(0, 0), 1)
        for i in range(2):
            self.assertEqual(page.record_list.item(i, 3).textAlignment() & Qt.AlignmentFlag.AlignRight,
                             Qt.AlignmentFlag.AlignRight)

    def test_record_details_are_frozen_and_no_new_record_is_created(self):
        before = [asdict(r) for r in self.records.list_all()]
        page = self.page(AppRoute.RECORDS)
        with patch("packages.standards.carbon_material.CarbonMaterialCalculator.calculate",
                   side_effect=AssertionError("no historical recalculation")):
            self.assertTrue(page.open_record("ui.sample.one"))
            self.flush()
            self.assertEqual(page.detail_tabs.count(), 2)
            self.assertTrue(page.summary_view.isReadOnly())
            self.assertTrue(page.input_basis_view.isReadOnly())
            self.assertEqual(len(page.findChildren(QPushButton, "exportWordReportButton")), 1)
            page.back_to_records_button.click()
        self.assertEqual(before, [asdict(r) for r in self.records.list_all()])

    def test_setting_cancel_keeps_original_directory(self):
        page = self.page(AppRoute.SETTINGS)
        before = page.export_directory_path.text()
        self.assertTrue(page.export_directory_path.isReadOnly())
        with patch("packages.ui.pages.QFileDialog.getExistingDirectory", return_value=""), \
             patch.object(page.export_location_service, "set_preferred_directory") as save:
            page.choose_export_directory_button.click()
            save.assert_not_called()
        self.assertEqual(before, page.export_directory_path.text())

    def test_page_styles_do_not_change_home_or_application_styles(self):
        home = self.page(AppRoute.HOME)
        before = (self.app.styleSheet(), self.window.styleSheet(), self.shell.styleSheet(), home.styleSheet())
        for route in (AppRoute.STANDARDS, AppRoute.FACTORS, AppRoute.EXCEL_IMPORT, AppRoute.RECORDS, AppRoute.SETTINGS):
            self.page(route)
        self.page(AppRoute.HOME)
        self.assertEqual(before, (self.app.styleSheet(), self.window.styleSheet(), self.shell.styleSheet(), home.styleSheet()))

    def test_mode_switch_retains_all_filters_and_skips_hidden_search_focus(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        page.search_input.setText("0.11")
        page.search_category_filter.setCurrentIndex(page.search_category_filter.findData("factor"))
        if page.search_source_filter.count() > 1:
            page.search_source_filter.setCurrentIndex(1)
        expected = (page.search_input.text(), page.search_category_filter.currentData(),
                    page.search_source_filter.currentData(), tuple(page._search_results))
        page.search_input.setFocus()
        page.view_mode_filter.setCurrentIndex(0)
        self.flush()
        self.assertFalse(page.search_tools.isVisible())
        page.browse_mode_button.setFocus()
        for _ in range(12):
            QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Tab)
            self.assertNotIn(self.app.focusWidget(), (page.search_input, page.search_category_filter))
        page.view_mode_filter.setCurrentIndex(1)
        self.flush()
        self.assertEqual(expected, (page.search_input.text(), page.search_category_filter.currentData(),
                                   page.search_source_filter.currentData(), tuple(page._search_results)))

    def test_longest_registered_value_and_unit_are_exact_in_detail(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        result = max((item for item in self.catalog.search_reference_library("") if item.asset is not None),
                     key=lambda item: len(item.value_text or ""))
        page._render_search_detail(result)
        self.flush()
        self.assertEqual(page.findChild(QLabel, "parameterReferenceValue").text(), format(result.asset.value, "f"))
        self.assertEqual(page.findChild(QLabel, "parameterReferenceUnit").text(), result.asset.unit)
        self.assertGreaterEqual(page.factor_detail_scroll.height(), 280)

    def test_import_tab_order_follows_visible_business_grid(self):
        page = self.page(AppRoute.EXCEL_IMPORT)
        ordered = (page.import_enterprise_name, page.import_period_type, page.import_period_start,
                   page.import_period_end, page.import_region, page.import_boundary_confirmed)
        ordered[0].setFocus()
        self.flush()
        for current, following in zip(ordered, ordered[1:]):
            self.assertIs(self.app.focusWidget(), current)
            QTest.keyClick(current, Qt.Key.Key_Tab)
            self.assertIs(self.app.focusWidget(), following)
            self.assertTrue(following.isVisible())

    def test_settings_failure_keeps_path_and_reports_failure(self):
        page = self.page(AppRoute.SETTINGS)
        before = page.export_directory_path.text()
        with patch("packages.ui.pages.QFileDialog.getExistingDirectory", return_value=str(self.root / "other")), \
             patch.object(page.export_location_service, "set_preferred_directory", side_effect=OSError("synthetic failure")), \
             patch("packages.ui.pages.QMessageBox.critical") as error:
            page.choose_export_directory_button.click()
        self.assertEqual(page.export_directory_path.text(), before)
        self.assertEqual(page.export_location_service.display_directory(), Path(before))
        self.assertEqual(error.call_count, 1)
        self.assertIn("未更改", error.call_args.args[1])

    def test_missing_frozen_summary_is_not_rendered_as_zero(self):
        page = self.page(AppRoute.RECORDS)
        # Fault-injected historical read model; no stored Record is modified.
        original = page._records[0]
        page._records = (replace(original, total_amount=None), *page._records[1:])
        page._show_selected_record(0)
        self.assertIn("未保存", page.record_total_value.text())
        self.assertIn("原标准核算总量 ET", page.record_total_caption.text())
        self.assertNotIn("0.00", page.record_total_value.text())
        page._records = (replace(original, total_amount=Decimal("0")), *page._records[1:])
        page._show_selected_record(0)
        self.assertIn("0.00", page.record_total_value.text())

    def test_standard_software_note_and_official_action_are_separate(self):
        page = self.page(AppRoute.STANDARDS)
        page.search_input.setText("32151.34")
        page.standard_table.cellActivated.emit(0, 0)
        self.flush()
        note = page.findChild(QLabel, "standardImplementationNote")
        self.assertIn("不是标准原文要求", note.text())
        action = page.findChild(QPushButton, "viewOfficialSourceButton")
        self.assertEqual(action.parent().objectName(), "standardDetailActions")
        self.assertTrue(action.property("officialSourceUrl").startswith("https://"))
        self.assertIsNone(page.findChild(QLabel, "standardSourceNote"))

if __name__ == "__main__":unittest.main()
