from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import ReviewStatus
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.catalog import CatalogStatus, ParameterViewMode
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


def _standard_action_button(page: object, standard_id: str) -> QPushButton:
    buttons = page.findChildren(QPushButton, "startAccountingButton")  # type: ignore[attr-defined]
    for button in buttons:
        if button.property("standardId") == standard_id:
            return button
    raise AssertionError(f"no accounting button for {standard_id}")


class G04CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.repository = SQLiteCatalogRepository(cls.catalog_path)
        cls.service = CatalogQueryService(cls.repository, as_of=date(2026, 9, 12))
        cls.missing_url_path = Path(cls.temp_directory.name) / "catalog-missing-source-url.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.missing_url_path)
        with sqlite3.connect(cls.missing_url_path) as connection:
            connection.execute("UPDATE source_documents SET official_url=NULL")
            connection.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_directory.cleanup()

    def setUp(self) -> None:
        self.window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.service,
        )
        self.window.show()
        self.application.processEvents()
        shell = self.window.centralWidget()
        self.assertIsInstance(shell, AppShell)
        assert isinstance(shell, AppShell)
        self.shell = shell

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.application.processEvents()

    def test_standard_search_status_year_and_date_derived_status(self) -> None:
        self.assertEqual(len(self.service.search_standards()), 9)
        result = self.service.search_standards("32151.34")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0].standard_id, "gbt_32151_34_2024")
        self.assertIs(result[0][1], CatalogStatus.CURRENT)

        upcoming = self.service.search_standards(status=CatalogStatus.UPCOMING)
        self.assertEqual(
            [item[0].standard_id for item in upcoming],
            ["gbt_32151_5_2026"],
        )
        self.assertEqual(
            [item[0].standard_id for item in self.service.search_standards(publication_year=2023)],
            [
                "gbt_32151_13_2023",
                "gbt_32151_7_2023",
                "gbt_32151_8_2023",
            ],
        )

        before_implementation = CatalogQueryService(
            self.repository,
            as_of=date(2026, 1, 1),
        ).search_standards("32150")
        self.assertEqual(len(before_implementation), 1)
        self.assertIs(before_implementation[0][1], CatalogStatus.UPCOMING)

    def test_standard_detail_has_source_relationships_and_only_current_implemented_entry_can_start(self) -> None:
        detail = self.service.get_standard_detail("gbt_32151_34_2024")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.standard.standard_number, "GB/T 32151.34—2024")
        self.assertEqual(detail.source.document_no, "GB/T 32151.34—2024")
        self.assertEqual(detail.base_standards[0].standard_id, "gbt_32150_2025")
        self.assertEqual(
            {parameter.parameter_id for parameter in detail.parameters},
            {
                "natural_gas_lhv",
                "natural_gas_carbon_content",
                "natural_gas_oxidation_rate",
            },
        )
        self.assertEqual(len(detail.factors), 3)

        upcoming_detail = self.service.get_standard_detail("gbt_32151_5_2026")
        self.assertIsNotNone(upcoming_detail)
        assert upcoming_detail is not None
        self.assertIs(upcoming_detail.status, CatalogStatus.UPCOMING)

    def test_parameter_factor_search_supports_subject_source_and_source_trace(self) -> None:
        natural_gas = self.service.search_parameter_factors("天然气")
        self.assertEqual(
            {item.factor.factor_id for item in natural_gas if item.factor is not None},
            {
                "natural_gas_lhv_gbt32151_34_c1",
                "natural_gas_carbon_content_gbt32151_34_c1",
                "natural_gas_oxidation_rate_gbt32151_34_c1",
            },
        )

        by_source = self.service.search_parameter_factors(
            "GB/T 32151.34",
            view_mode=ParameterViewMode.BY_SOURCE,
        )
        self.assertEqual(len(by_source), 6)
        self.assertTrue(all(item.source is not None for item in by_source))
        source_specific = self.service.search_parameter_factors(
            view_mode=ParameterViewMode.BY_SOURCE,
            source_id="SRC-32151-34-2024",
        )
        self.assertEqual(len(source_specific), 3)
        self.assertTrue(
            all(item.source is not None and item.source.source_id == "SRC-32151-34-2024" for item in source_specific)
        )
        notice = self.service.search_parameter_factors("公告2025年第47号")
        self.assertEqual(
            {item.factor.factor_id for item in notice if item.factor is not None},
            {"electricity_national_average_2023"},
        )

        electricity = self.service.get_factor_detail("electricity_national_average_2023")
        self.assertIsNotNone(electricity)
        assert electricity is not None
        self.assertIsNotNone(electricity.source)
        assert electricity.source is not None
        self.assertEqual(electricity.source.publisher, "生态环境部、国家统计局")
        self.assertTrue(electricity.factor.source_location)
        self.assertIn("gbt_32151_34_2024", electricity.factor.applicable_standard_ids)

    def test_parameter_filters_and_labels_use_domain_enums(self) -> None:
        result = self.service.search_parameter_factors(
            parameter_type=None,
            review_status=ReviewStatus.VERIFIED,
            factor_year=2024,
        )
        self.assertEqual(len(result), 3)
        self.assertTrue(all(item.factor is not None for item in result))
        self.assertEqual(self.service.review_status_label(ReviewStatus.VERIFIED), "已核对")

    def test_standard_page_searches_and_routes_only_the_opened_standard(self) -> None:
        page = self.shell.pages[AppRoute.STANDARDS]
        table = page.findChild(QTableWidget, "catalogTable")
        search = page.findChild(type(page.search_input), "standardSearch")
        source_button = page.findChild(QPushButton, "viewOfficialSourceButton")
        self.assertIsNotNone(table)
        self.assertIsNotNone(search)
        self.assertIsNotNone(source_button)
        assert table is not None
        assert search is not None
        assert source_button is not None
        self.assertEqual(table.rowCount(), 9)

        search.setText("32151.34")
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 1)
        source_button = page.findChild(QPushButton, "viewOfficialSourceButton")
        assert source_button is not None
        accounting_button = _standard_action_button(page, "gbt_32151_34_2024")
        self.assertTrue(source_button.isEnabled())
        self.assertTrue(accounting_button.isEnabled())
        accounting_button.click()
        self.application.processEvents()
        self.assertEqual(self.shell.current_route, AppRoute.NEW_ACCOUNTING)
        self.assertEqual(self.shell.selected_standard_id, "gbt_32151_34_2024")

        self.shell.navigate(AppRoute.STANDARDS)
        page.search_input.clear()
        page.status_filter.setCurrentIndex(page.status_filter.findData(CatalogStatus.UPCOMING))
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 1)
        accounting_button = _standard_action_button(page, "gbt_32151_5_2026")
        self.assertFalse(accounting_button.isEnabled())
        self.assertEqual(accounting_button.text(), "核算模块待开发")

        page.status_filter.setCurrentIndex(0)
        page.year_filter.setCurrentIndex(page.year_filter.findData(2023))
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 3)

    def test_parameter_factor_page_switches_views_and_hides_internal_ids(self) -> None:
        self.shell.navigate(AppRoute.FACTORS)
        self.application.processEvents()
        page = self.shell.pages[AppRoute.FACTORS]
        table = page.findChild(QTableWidget, "catalogTable")
        self.assertIsNotNone(table)
        assert table is not None

        page.search_input.setText("天然气")
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 3)
        page.view_mode_filter.setCurrentIndex(1)
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 3)
        detail_text = "\n".join(
            label.text() for label in page.factor_detail_host.findChildren(QLabel)
        )
        self.assertIn("GB/T 32151.34—2024", detail_text)
        source_button = page.findChild(QPushButton, "viewFactorSourceButton")
        self.assertIsNotNone(source_button)
        assert source_button is not None
        self.assertTrue(source_button.isEnabled())
        visible_text = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertNotIn("natural_gas", visible_text)

    def test_missing_catalog_degrades_to_safe_empty_pages(self) -> None:
        missing = Path(self.temp_directory.name) / "not-installed.sqlite"
        window = create_main_window(AppConfig(catalog_database=missing))
        window.show()
        self.application.processEvents()
        try:
            shell = window.centralWidget()
            self.assertIsInstance(shell, AppShell)
            assert isinstance(shell, AppShell)
            standard_page = shell.pages[AppRoute.STANDARDS]
            factor_page = shell.pages[AppRoute.FACTORS]
            self.assertEqual(standard_page.findChild(QTableWidget, "catalogTable").rowCount(), 0)
            shell.navigate(AppRoute.FACTORS)
            self.application.processEvents()
            self.assertEqual(factor_page.findChild(QTableWidget, "catalogTable").rowCount(), 0)
        finally:
            window.close()
            window.deleteLater()
            self.application.processEvents()

    def test_missing_optional_source_url_disables_external_link_safely(self) -> None:
        service = CatalogQueryService(
            SQLiteCatalogRepository(self.missing_url_path),
            as_of=date(2026, 9, 12),
        )
        window = create_main_window(
            AppConfig(catalog_database=self.missing_url_path),
            catalog_service=service,
        )
        window.show()
        self.application.processEvents()
        try:
            shell = window.centralWidget()
            self.assertIsInstance(shell, AppShell)
            assert isinstance(shell, AppShell)
            shell.navigate(AppRoute.FACTORS)
            self.application.processEvents()
            page = shell.pages[AppRoute.FACTORS]
            buttons = page.findChildren(QPushButton, "viewFactorSourceButton")
            self.assertTrue(buttons)
            self.assertTrue(all(not button.isEnabled() for button in buttons))
        finally:
            window.close()
            window.deleteLater()
            self.application.processEvents()


if __name__ == "__main__":
    unittest.main()
