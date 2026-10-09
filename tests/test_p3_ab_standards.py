from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.catalog import CatalogStatus, StandardCatalogRecord
from packages.ui.catalog_pages import StandardLibraryPage
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


class _StandardOverrideRepository:
    def __init__(
        self,
        repository: SQLiteCatalogRepository,
        overrides: dict[str, dict[str, object]],
    ) -> None:
        self._repository = repository
        self._standards = tuple(
            replace(standard, **overrides[standard.standard_id])
            if standard.standard_id in overrides
            else standard
            for standard in repository.list_standards()
        )

    def __getattr__(self, name: str):
        return getattr(self._repository, name)

    def list_standards(self) -> tuple[StandardCatalogRecord, ...]:
        return self._standards


class P3ABStandardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.repository = SQLiteCatalogRepository(cls.catalog_path)
        cls.service = CatalogQueryService(cls.repository, as_of=date(2026, 9, 12))
        cls.missing_url_repository = _StandardOverrideRepository(
            cls.repository,
            {"gbt_32151_34_2024": {"official_source_url": None}},
        )
        cls.missing_url_service = CatalogQueryService(
            cls.missing_url_repository,
            as_of=date(2026, 9, 12),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_directory.cleanup()

    def setUp(self) -> None:
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.service,
            record_repository=InMemoryRecordRepository(),
        )
        self.window.resize(1180, 720)
        self.window.show()
        self.application.processEvents()
        shell = self.window.centralWidget()
        self.assertIsInstance(shell, AppShell)
        assert isinstance(shell, AppShell)
        self.shell = shell
        self.page = shell.pages[AppRoute.STANDARDS]
        shell.navigate(AppRoute.STANDARDS)
        self._process_events()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.application.processEvents()

    def _process_events(self) -> None:
        for _ in range(5):
            self.application.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.application.processEvents()

    def _row_for_standard(self, page: StandardLibraryPage, standard_id: str) -> int:
        for row in range(page.standard_table.rowCount()):
            item = page.standard_table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == standard_id:
                return row
        raise AssertionError(f"standard row not found: {standard_id}")

    def _open_by_mouse(self, page: StandardLibraryPage, standard_id: str, column: int) -> None:
        row = self._row_for_standard(page, standard_id)
        item_rect = page.standard_table.visualItemRect(page.standard_table.item(row, column))
        QTest.mouseClick(
            page.standard_table.viewport(),
            Qt.MouseButton.LeftButton,
            pos=item_rect.center(),
        )
        self._process_events()

    def _open_by_keyboard(self, page: StandardLibraryPage, standard_id: str, column: int) -> None:
        row = self._row_for_standard(page, standard_id)
        page.standard_table.setCurrentCell(row, column)
        page.standard_table.setFocus()
        QTest.keyClick(page.standard_table, Qt.Key.Key_Return)
        self._process_events()

    def _back_to_list(self, page: StandardLibraryPage) -> None:
        button = page.findChild(QPushButton, "backToStandardListButton")
        self.assertIsNotNone(button)
        assert button is not None
        button.click()
        self._process_events()
        self.assertIs(page.view_stack.currentWidget(), page.list_view)

    def test_search_controls_headers_and_support_are_limited_to_the_standard_catalog(self) -> None:
        page = self.page
        table = page.findChild(QTableWidget, "catalogTable")
        self.assertIsNotNone(table)
        assert table is not None
        self.assertEqual(
            [table.horizontalHeaderItem(column).text() for column in range(table.columnCount())],
            ["标准编号", "标准名称", "标准状态", "实施日期", "软件支持"],
        )
        self.assertIsNone(page.findChild(type(page.status_filter), "standardIndustryFilter"))
        self.assertIsNone(page.findChild(type(page.status_filter), "standardYearFilter"))
        self.assertEqual(page.status_filter.count(), 5)
        self.assertEqual(table.rowCount(), 9)

        page.search_input.setText("炭素材料生产企业")
        self._process_events()
        self.assertEqual(table.rowCount(), 1)
        self.assertEqual(table.item(0, 4).text(), "已实现核算（未正式支持）")
        for column in (0, 1):
            item = table.item(0, column)
            assert item is not None
            self.assertTrue(item.font().underline())
            self.assertEqual(item.foreground().color().name().upper(), "#12618D")
            self.assertIn("打开标准详情", item.toolTip())

        item_rect = table.visualItemRect(table.item(0, 4))
        QTest.mouseClick(table.viewport(), Qt.MouseButton.LeftButton, pos=item_rect.center())
        self._process_events()
        self.assertIs(page.view_stack.currentWidget(), page.list_view)
        self.assertIsNone(page.selected_standard_id)

    def test_number_and_name_cells_open_the_same_detail_by_mouse_and_keyboard(self) -> None:
        page = self.page
        page.search_input.setText("32151.34")
        self._process_events()

        self._open_by_mouse(page, "gbt_32151_34_2024", 0)
        self.assertEqual(page.selected_standard_id, "gbt_32151_34_2024")
        self.assertIs(page.view_stack.currentWidget(), page.detail_host)
        self._back_to_list(page)
        self.assertEqual(page.search_input.text(), "32151.34")
        self.assertEqual(page.standard_table.currentRow(), 0)

        self._open_by_keyboard(page, "gbt_32151_34_2024", 1)
        self.assertEqual(page.selected_standard_id, "gbt_32151_34_2024")
        self.assertIs(page.view_stack.currentWidget(), page.detail_host)
        self.assertEqual(
            page.findChild(QLabel, "standardDetailNumber").text(),
            "GB/T 32151.34—2024",
        )

    def test_detail_has_exactly_three_sections_and_uses_verified_scope_or_precise_placeholder(self) -> None:
        page = self.page
        page.search_input.setText("32151.34")
        self._process_events()
        self._open_by_mouse(page, "gbt_32151_34_2024", 1)

        titles = [
            label.text()
            for label in page.detail_host.findChildren(QLabel, "cardTitle")
            if label.isVisible()
        ]
        self.assertEqual(titles, ["基本信息", "适用范围", "标准要求"])
        detail_text = "\n".join(
            label.text()
            for label in page.detail_host.findChildren(QLabel)
            if label.isVisible()
        )
        self.assertIn("适用于炭素材料生产企业温室气体排放量的核算。", detail_text)
        self.assertIn("当前目录尚未录入可核验的结构化标准要求。", detail_text)
        for forbidden in (
            "发布单位",
            "标准关系",
            "替代关系",
            "规范性引用文件",
            "软件支持范围",
            "参数与因子",
            "天然气低位发热量",
            "参数/因子",
        ):
            self.assertNotIn(forbidden, detail_text)

        self._back_to_list(page)
        page.search_input.setText("32150")
        self._process_events()
        self._open_by_mouse(page, "gbt_32150_2025", 0)
        detail_text = "\n".join(
            label.text()
            for label in page.detail_host.findChildren(QLabel)
            if label.isVisible()
        )
        self.assertIn("当前目录尚未录入可核验的适用范围信息。", detail_text)

    def test_list_state_and_both_scroll_positions_return_after_detail(self) -> None:
        page = self.page
        page.view_stack.setMinimumHeight(1000)
        self.shell.update_content_geometry()
        page.search_input.setText("32151")
        page.status_filter.setCurrentIndex(page.status_filter.findData(CatalogStatus.CURRENT))
        page.standard_table.setFixedHeight(150)
        page.standard_table.setFixedWidth(420)
        self._process_events()
        self.assertGreater(page.standard_table.verticalScrollBar().maximum(), 0)

        row = self._row_for_standard(page, "gbt_32151_8_2023")
        page.standard_table.setCurrentCell(row, 0)
        page.standard_table.setFocus()
        self._process_events()
        table_bar = page.standard_table.verticalScrollBar()
        table_bar.setValue(table_bar.maximum())
        main_bar = self.shell.main_scroll_area.verticalScrollBar()
        main_bar.setValue(main_bar.maximum())
        self._process_events()

        expected_main = main_bar.value()
        expected_table = table_bar.value()
        expected_horizontal = page.standard_table.horizontalScrollBar().value()
        expected_row = page.standard_table.currentRow()
        expected_query = page.search_input.text()
        expected_status = page.status_filter.currentData()
        self.assertGreater(expected_table, 0)
        self.assertGreater(expected_main, 0)

        page.standard_table.cellActivated.emit(row, 0)
        self._process_events()
        self.assertEqual(main_bar.value(), main_bar.minimum())
        self.assertIs(page.view_stack.currentWidget(), page.detail_host)

        self._back_to_list(page)
        self.assertEqual(page.search_input.text(), expected_query)
        self.assertEqual(page.status_filter.currentData(), expected_status)
        self.assertEqual(page.standard_table.currentRow(), expected_row)
        self.assertEqual(page.standard_table.verticalScrollBar().value(), expected_table)
        self.assertEqual(page.standard_table.horizontalScrollBar().value(), expected_horizontal)
        self.assertEqual(main_bar.value(), expected_main)

    def test_reopening_detail_replaces_actions_and_keeps_current_standard_identity(self) -> None:
        page = self.page
        page.search_input.setText("32151.34")
        self._process_events()
        self._open_by_mouse(page, "gbt_32151_34_2024", 0)

        source_buttons = page.findChildren(QPushButton, "viewOfficialSourceButton")
        accounting_buttons = page.findChildren(QPushButton, "startAccountingButton")
        self.assertEqual(len(source_buttons), 1)
        self.assertEqual(len(accounting_buttons), 1)
        source_button = source_buttons[0]
        accounting_button = accounting_buttons[0]
        self.assertEqual(accounting_button.property("standardId"), "gbt_32151_34_2024")
        primary_url = source_button.property("officialSourceUrl")
        self.assertTrue(source_button.isEnabled())
        spy = QSignalSpy(page.accounting_requested)
        accounting_button.click()
        self.assertEqual(spy.count(), 1)
        self.assertEqual(spy.at(0)[0], "gbt_32151_34_2024")

        self.shell.navigate(AppRoute.STANDARDS)
        self._process_events()
        self._back_to_list(page)
        page.search_input.setText("32150")
        self._process_events()
        self._open_by_mouse(page, "gbt_32150_2025", 0)

        current_standard = next(
            standard
            for standard in self.repository.list_standards()
            if standard.standard_id == "gbt_32150_2025"
        )
        source_buttons = page.findChildren(QPushButton, "viewOfficialSourceButton")
        accounting_buttons = page.findChildren(QPushButton, "startAccountingButton")
        self.assertEqual(len(source_buttons), 1)
        self.assertEqual(len(accounting_buttons), 1)
        self.assertTrue(source_buttons[0].isVisible())
        self.assertEqual(source_buttons[0].property("officialSourceUrl"), current_standard.official_source_url)
        self.assertNotEqual(source_buttons[0].property("officialSourceUrl"), primary_url)
        self.assertEqual(accounting_buttons[0].property("standardId"), "gbt_32150_2025")
        self.assertFalse(accounting_buttons[0].isEnabled())
        self.assertEqual(spy.count(), 1)

    def test_source_action_and_existing_status_gate_use_configured_data(self) -> None:
        page = self.page
        page.search_input.setText("32151.34")
        self._process_events()
        self._open_by_mouse(page, "gbt_32151_34_2024", 0)
        source_button = page.findChild(QPushButton, "viewOfficialSourceButton")
        self.assertIsNotNone(source_button)
        assert source_button is not None
        self.assertTrue(source_button.isEnabled())
        self.assertIn("E32D6CB8AF14D795CC640F8BBC85538D", source_button.property("officialSourceUrl"))
        with patch("packages.ui.catalog_pages.QDesktopServices.openUrl", return_value=True) as open_url:
            source_button.click()
            open_url.assert_called_once()

        self.assertTrue(page.findChild(QPushButton, "startAccountingButton").isEnabled())
        self._back_to_list(page)
        page.search_input.setText("32150")
        self._process_events()
        self._open_by_mouse(page, "gbt_32150_2025", 0)
        self.assertEqual(page.standard_table.item(self._row_for_standard(page, "gbt_32150_2025"), 4).text(), "配套通则")
        accounting_button = page.findChild(QPushButton, "startAccountingButton")
        self.assertIsNotNone(accounting_button)
        assert accounting_button is not None
        self.assertFalse(accounting_button.isEnabled())
        self.assertEqual(accounting_button.text(), "配套通则，不单独核算")

        historical_service = CatalogQueryService(self.repository, as_of=date(2025, 1, 1))
        historical_page = StandardLibraryPage(historical_service, lambda _route: None)
        historical_page.show()
        self._process_events()
        self._open_by_keyboard(historical_page, "gbt_32151_34_2024", 0)
        historical_row = self._row_for_standard(historical_page, "gbt_32151_34_2024")
        self.assertEqual(historical_page.standard_table.item(historical_row, 4).text(), "已实现核算（未正式支持）")
        historical_accounting = historical_page.findChild(QPushButton, "startAccountingButton")
        self.assertIsNotNone(historical_accounting)
        assert historical_accounting is not None
        self.assertFalse(historical_accounting.isEnabled())
        self.assertEqual(historical_accounting.text(), "当前状态下不可新建核算")
        historical_page.close()
        historical_page.deleteLater()
        self._process_events()

    def test_long_standard_name_remains_reachable_at_large_text_scale(self) -> None:
        long_name = (
            "温室气体排放核算与报告要求 "
            "炭素材料生产企业及其适用边界、排放活动与数据核验说明 " * 4
        ).strip()
        repository = _StandardOverrideRepository(
            self.repository,
            {"gbt_32151_34_2024": {"standard_name": long_name}},
        )
        service = CatalogQueryService(repository, as_of=date(2026, 9, 12))
        page = StandardLibraryPage(service, lambda _route: None)
        page.resize(780, 720)
        page.show()
        page.search_input.setText("32151.34")
        font = QFont(page.standard_table.font())
        font.setPointSize(max(font.pointSize() + 4, 14))
        page.standard_table.setFont(font)
        page.standard_table.setFixedWidth(640)
        self._process_events()

        row = self._row_for_standard(page, "gbt_32151_34_2024")
        name_item = page.standard_table.item(row, 1)
        self.assertIsNotNone(name_item)
        assert name_item is not None
        self.assertEqual(name_item.text(), long_name)
        horizontal_bar = page.standard_table.horizontalScrollBar()
        self.assertGreater(horizontal_bar.maximum(), 0)
        horizontal_bar.setValue(horizontal_bar.maximum())
        self._process_events()
        self.assertEqual(horizontal_bar.value(), horizontal_bar.maximum())
        self.assertTrue(
            page.standard_table.visualItemRect(name_item).intersects(
                page.standard_table.viewport().rect()
            )
        )
        page.close()
        page.deleteLater()
        self._process_events()

    def test_missing_official_url_has_visible_explanation_and_disabled_action(self) -> None:
        window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.missing_url_service,
            record_repository=InMemoryRecordRepository(),
        )
        window.show()
        self._process_events()
        shell = window.centralWidget()
        self.assertIsInstance(shell, AppShell)
        assert isinstance(shell, AppShell)
        page = shell.pages[AppRoute.STANDARDS]
        shell.navigate(AppRoute.STANDARDS)
        page.search_input.setText("32151.34")
        self._process_events()
        self._open_by_mouse(page, "gbt_32151_34_2024", 0)

        source_button = page.findChild(QPushButton, "viewOfficialSourceButton")
        explanation = page.findChild(QLabel, "officialSourceUnavailable")
        self.assertIsNotNone(source_button)
        self.assertIsNotNone(explanation)
        assert source_button is not None
        assert explanation is not None
        self.assertFalse(source_button.isEnabled())
        self.assertTrue(explanation.isVisible())
        self.assertIn("未配置标准官方页面", explanation.text())
        window.close()
        window.deleteLater()
        self._process_events()


if __name__ == "__main__":
    unittest.main()