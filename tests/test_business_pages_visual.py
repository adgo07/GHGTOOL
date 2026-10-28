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
from PySide6.QtCore import QCoreApplication, QEvent, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QFontMetrics, QFontDatabase
from PySide6.QtWidgets import QApplication, QAbstractItemView, QLabel, QPushButton, QToolButton, QWidget
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
        # Offscreen Qt on Windows can enumerate no fonts and measure every
        # Latin digit as a missing-glyph square. Keep visual assertions intact;
        # register existing host fonts in this QA process only, as capture does.
        if not QFontDatabase.families():
            windows = os.environ.get("WINDIR")
            if windows:
                for name in ("msyh.ttc", "msyhbd.ttc", "seguisym.ttf", "segoeui.ttf"):
                    path = Path(windows) / "Fonts" / name
                    if path.is_file():
                        QFontDatabase.addApplicationFont(str(path))
            if not QFontDatabase.families():
                raise RuntimeError("视觉测试需要可用字体；未安装或打包新字体，当前离屏进程无法加载系统字体。")

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


    def test_standard_numbers_and_wrapped_names_fit_after_window_resize(self):
        page = self.page(AppRoute.STANDARDS)
        table = page.standard_table
        expected = tuple(tuple(table.item(row, column).text() for column in range(5))
                         for row in range(table.rowCount()))
        for width in (1440, 1180):
            self.window.resize(width, 800)
            self.flush()
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                metrics = QFontMetrics(item.font().resolve(table.font()))
                self.assertGreaterEqual(table.columnWidth(0), metrics.horizontalAdvance(item.text()) + 28)
                self.assertGreaterEqual(table.rowHeight(row), table.sizeHintForRow(row))
                # Visible badges must not be implemented by erasing model text.
                self.assertTrue(table.item(row, 2).text())
            self.assertEqual(expected, tuple(tuple(table.item(row, column).text() for column in range(5))
                                             for row in range(table.rowCount())))

    def test_parameter_rows_and_trace_label_remain_readable_after_resize(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        page.search_input.setText("0.11")
        for width in (1440, 1180):
            self.window.resize(width, 800)
            self.flush()
            for row in range(page.search_result_table.rowCount()):
                table = page.search_result_table
                self.assertGreaterEqual(table.rowHeight(row), table.sizeHintForRow(row))
                item = table.item(row, 0)
                metrics = QFontMetrics(item.font().resolve(table.font()))
                wrapped = metrics.boundingRect(QRect(0, 0, table.columnWidth(0) - 20, 10000),
                    int(Qt.TextFlag.TextWordWrap), item.text()).height()
                self.assertGreaterEqual(table.rowHeight(row), wrapped + 16)
        for query in ("7.5.6", "0.11"):
            page.search_input.setText(query)
            self.flush()
            self.assertGreater(page.search_result_table.rowCount(), 0)
            for row in range(page.search_result_table.rowCount()):
                table = page.search_result_table
                item = table.item(row, 0)
                metrics = QFontMetrics(item.font().resolve(table.font()))
                wrapped = metrics.boundingRect(QRect(0, 0, table.columnWidth(0) - 20, 10000),
                    int(Qt.TextFlag.TextWordWrap), item.text()).height()
                self.assertGreaterEqual(table.rowHeight(row), wrapped + 16)
        asset_row = next(index for index, result in enumerate(page._search_results) if result.asset is not None)
        page.search_result_table.selectRow(asset_row)
        self.flush()
        toggle = page.findChild(QToolButton, "parameterDetailTraceToggle")
        self.assertIn("查看完整来源", toggle.text())
        self.assertNotEqual(toggle.toolButtonStyle(), Qt.ToolButtonStyle.ToolButtonIconOnly)
        toggle.setChecked(True)
        self.flush()
        trace = page.findChild(QWidget, "parameterDetailTrace")
        self.assertTrue(trace.isVisible())
        self.assertIn("来源定位", "\n".join(label.text() for label in trace.findChildren(QLabel)))
        self.assertEqual(len(self.records.list_all()), 2)

    def test_long_record_list_keeps_full_badges_and_reachable_identity(self):
        sample = _record("ui.long-company", warning=True)
        self.records.create(replace(sample, input_snapshot=replace(sample.input_snapshot,
            enterprise_name="合成界面验证企业·长中文名称用于检查列表换行与完整历史身份")))
        page = self.page(AppRoute.RECORDS)
        for width in (1440, 1180):
            self.window.resize(width, 800)
            self.flush()
            for row in range(page.record_list.rowCount()):
                self.assertGreaterEqual(page.record_list.rowHeight(row), page.record_list.sizeHintForRow(row))
                host = page.record_list.cellWidget(row, 4)
                badge = host.findChild(QLabel, "recordStatusBadge")
                self.assertIsNotNone(badge)
                self.assertLessEqual(badge.height(), 44)
                self.assertGreaterEqual(badge.width(), badge.fontMetrics().horizontalAdvance(badge.text()) + 12)
                self.assertTrue(page.record_list.item(row, 4).text())
        for row in range(page.record_list.rowCount()):
            item = page.record_list.item(row, 0)
            self.assertIn(item.text(), item.toolTip())
            self.assertNotIn("记录编号：", item.toolTip())
            # Full Chinese identity now wraps to all required lines. Keep a
            # bounded paint allowance over Qt's native wrapped-content hint.
            self.assertLessEqual(page.record_list.rowHeight(row), max(48, page.record_list.sizeHintForRow(row) + 8))
        self.assertEqual(len(self.records.list_all()), 3)

        for row in range(page.record_list.rowCount()):
            host = page.record_list.cellWidget(row, 4)
            badge = host.findChild(QLabel, "recordStatusBadge")
            self.assertGreaterEqual(host.width(), badge.minimumWidth() + 8)
            date_item = page.record_list.item(row, 5)
            self.assertGreaterEqual(page.record_list.columnWidth(5), page.record_list.fontMetrics().horizontalAdvance(date_item.text()) + 20)

    def test_frozen_report_header_displays_complete_enthalpy_unit(self):
        page = self.page(AppRoute.RECORDS)
        self.assertTrue(page.open_record("ui.sample.one"))
        page.detail_tabs.setCurrentIndex(1)
        self.flush()
        found = []
        for card in page.input_basis_view.report_table_cards:
            table = card.table_widget
            for row in range(table.rowCount()):
                for column in range(table.columnCount()):
                    item = table.item(row, column)
                    if item is not None and "kJ/kg" in item.text():
                        found.append(item.text())
                        unit_line = item.text().splitlines()[-1]
                        self.assertGreaterEqual(table.columnWidth(column), table.fontMetrics().horizontalAdvance(unit_line) + 32)
        self.assertTrue(found, "Frozen B.9 header must remain present")
        self.assertEqual(len(self.records.list_all()), 2)



    def test_wide_frozen_table_scrolls_locally_without_widening_record_tabs(self):
        page = self.page(AppRoute.RECORDS)
        self.assertTrue(page.open_record("ui.sample.one"))
        page.detail_tabs.setCurrentIndex(1)
        self.flush()
        pane = page.input_basis_view
        self.assertEqual(pane.scroll_area.horizontalScrollBar().maximum(), 0)
        wide = [card.table_widget for card in pane.report_table_cards
                if card.table_widget.horizontalScrollBar().maximum() > 0]
        self.assertTrue(wide)
        table = max(wide, key=lambda value: value.columnCount())
        frozen = tuple(tuple(table.item(row, column).text() if table.item(row, column) else ""
                            for column in range(table.columnCount())) for row in range(table.rowCount()))
        table.horizontalScrollBar().setValue(table.horizontalScrollBar().maximum())
        self.flush()
        self.assertLessEqual(table.columnViewportPosition(table.columnCount() - 1) + table.columnWidth(table.columnCount() - 1),
                             table.viewport().width() + 2)
        self.assertEqual(frozen, tuple(tuple(table.item(row, column).text() if table.item(row, column) else ""
                                           for column in range(table.columnCount())) for row in range(table.rowCount())))
        self.assertEqual(len(self.records.list_all()), 2)

    def test_long_settings_path_starts_at_drive_and_remains_complete(self):
        page = self.page(AppRoute.SETTINGS)
        target = self.root / ("长路径辨认验证" * 12)
        page.export_location_service.set_preferred_directory(target)
        page._refresh_export_directory_display()
        self.flush()
        field = page.export_directory_path
        self.assertTrue(field.isReadOnly())
        self.assertEqual(field.cursorPosition(), 0)
        self.assertEqual(field.toolTip(), field.text())
        field.selectAll()
        self.assertEqual(field.selectedText(), str(target))
        self.assertEqual(page.export_location_service.display_directory(), target)

    def test_full_source_names_wrap_and_short_search_gives_detail_space(self):
        page = self.page(AppRoute.FACTORS)
        page.view_mode_filter.setCurrentIndex(1)
        self.flush()
        self.assertTrue(page.search_source_list.wordWrap())
        self.assertEqual(page.search_source_list.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sources = {source.source_id: source for source in self.catalog.list_sources()}
        for index in range(1, page.search_source_list.count()):
            item = page.search_source_list.item(index)
            source = sources[item.data(Qt.ItemDataRole.UserRole)]
            self.assertIn(source.document_name, item.text())
            self.assertIn(source.document_name, item.toolTip())
        page.search_input.setText("没有对应的资料词条")
        self.flush()
        self.assertEqual(len(page._search_results), 0)
        self.assertLessEqual(page.search_result_table.height(), 100)
        self.assertGreaterEqual(page.factor_detail_scroll.height(), 280)
        for row in range(page.search_source_list.count()):
            item = page.search_source_list.item(row)
            width = max(24, page.search_source_list.viewport().width() - 20)
            text_height = page.search_source_list.fontMetrics().boundingRect(
                QRect(0, 0, width, 10000), Qt.TextFlag.TextWordWrap, item.text()).height()
            self.assertGreaterEqual(item.sizeHint().height(), text_height + 12, item.text())


if __name__ == "__main__":unittest.main()
