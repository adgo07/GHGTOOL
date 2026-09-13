from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import ReviewStatus, ValueType
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.catalog import (
    CatalogStatus,
    CatalogValueCategory,
    ParameterViewMode,
)
from packages.ui.catalog_pages import ParameterFactorLibraryPage
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


def _standard_action_button(page: object, standard_id: str) -> QPushButton:
    buttons = page.findChildren(QPushButton, "startAccountingButton")  # type: ignore[attr-defined]
    for button in buttons:
        if button.property("standardId") == standard_id:
            return button
    raise AssertionError(f"no accounting button for {standard_id}")


class _MultiVersionRepository:
    """In-memory G04 fixture with three source-declared values for one parameter."""

    def __init__(self, repository: SQLiteCatalogRepository) -> None:
        self._standards = repository.list_standards()
        self._sources = repository.list_sources()
        self._subjects = repository.list_subjects()
        self._parameters = repository.list_parameters()
        base_factor = next(
            factor
            for factor in repository.list_factors()
            if factor.factor_id == "natural_gas_lhv_gbt32151_34_c1"
        )
        other_factor = replace(
            base_factor,
            factor_id="natural_gas_lhv_other_2023",
            value=Decimal("400"),
            source_value=Decimal("400"),
            normalized_value=Decimal("400"),
            factor_year=2023,
            value_type=ValueType.GOVERNMENT_PUBLISHED,
            notes="测试夹具：其他适用值",
        )
        historical_factor = replace(
            base_factor,
            factor_id="natural_gas_lhv_historical_2020",
            value=Decimal("380"),
            source_value=Decimal("380"),
            normalized_value=Decimal("380"),
            factor_year=2020,
            value_type=ValueType.HISTORICAL,
            review_status=ReviewStatus.DEPRECATED,
            notes="测试夹具：历史值",
        )
        self._factors = repository.list_factors() + (other_factor, historical_factor)

    def list_standards(self):
        return self._standards

    def list_sources(self):
        return self._sources

    def list_subjects(self):
        return self._subjects

    def list_parameters(self):
        return self._parameters

    def list_factors(self):
        return self._factors


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
                "electricity_emission_factor_nonfossil",
            },
        )
        self.assertEqual(len(detail.factors), 4)

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
        self.assertEqual(len(by_source), 7)
        self.assertTrue(all(item.source is not None for item in by_source))
        source_specific = self.service.search_parameter_factors(
            view_mode=ParameterViewMode.BY_SOURCE,
            source_id="SRC-32151-34-2024",
        )
        self.assertEqual(len(source_specific), 4)
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
        nonfossil = self.service.get_factor_detail("electricity_nonfossil_zero_gbt32151_34_2024")
        self.assertIsNotNone(nonfossil)
        assert nonfossil is not None
        self.assertEqual(nonfossil.factor.parameter_id, "electricity_emission_factor_nonfossil")
        self.assertEqual(nonfossil.factor.value, Decimal("0"))
        self.assertIn("PDF第30页；印刷页22", nonfossil.factor.source_location)

    def test_parameter_filters_and_labels_use_domain_enums(self) -> None:
        result = self.service.search_parameter_factors(
            parameter_type=None,
            review_status=ReviewStatus.VERIFIED,
            factor_year=2024,
        )
        self.assertEqual(len(result), 4)
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
        self.assertEqual(page.selected_standard_id, "gbt_32151_34_2024")
        detail_header = page.detail_layout.itemAt(0).widget()
        self.assertIsNotNone(detail_header)
        assert detail_header is not None
        detail_number = detail_header.findChild(QLabel, "standardDetailNumber")
        source_button = detail_header.findChild(QPushButton, "viewOfficialSourceButton")
        self.assertIsNotNone(detail_number)
        self.assertIsNotNone(source_button)
        assert detail_number is not None
        assert source_button is not None
        self.assertEqual(detail_number.text(), "GB/T 32151.34—2024")
        self.assertIn("E32D6CB8AF14D795CC640F8BBC85538D", source_button.property("officialSourceUrl"))
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

        page.search_input.setText("不存在的标准")
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 0)
        self.assertIsNone(page.selected_standard_id)

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
        self.assertIn(
            page.selected_factor_id,
            {
                "natural_gas_lhv_gbt32151_34_c1",
                "natural_gas_carbon_content_gbt32151_34_c1",
                "natural_gas_oxidation_rate_gbt32151_34_c1",
            },
        )
        detail_heading = page.factor_detail_layout.itemAt(0).widget()
        self.assertIsInstance(detail_heading, QLabel)
        assert isinstance(detail_heading, QLabel)
        self.assertIn("天然气", detail_heading.text())
        self.assertNotIn("全球变暖潜势", detail_heading.text())
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

        page.search_input.setText("不存在的参数")
        self.application.processEvents()
        self.assertEqual(table.rowCount(), 0)
        self.assertIsNone(page.selected_factor_id)

    def test_multi_version_values_have_explicit_categories_in_service_and_page(self) -> None:
        service = CatalogQueryService(
            _MultiVersionRepository(self.repository),
            as_of=date(2026, 9, 12),
        )
        results = service.search_parameter_factors("天然气低位发热量")
        self.assertEqual(len(results), 3)
        categories = {
            result.factor.factor_id: service.value_category(result.factor)
            for result in results
            if result.factor is not None
        }
        self.assertEqual(
            categories,
            {
                "natural_gas_lhv_gbt32151_34_c1": CatalogValueCategory.RECOMMENDED,
                "natural_gas_lhv_other_2023": CatalogValueCategory.OTHER_APPLICABLE,
                "natural_gas_lhv_historical_2020": CatalogValueCategory.HISTORICAL,
            },
        )
        page = ParameterFactorLibraryPage(service, lambda _route: None)
        page.show()
        self.application.processEvents()
        try:
            page.search_input.setText("天然气低位发热量")
            self.application.processEvents()
            self.assertEqual(page.factor_table.rowCount(), 3)
            state_values = {
                page.factor_table.item(row, 5).text()
                for row in range(page.factor_table.rowCount())
            }
            self.assertEqual(
                state_values,
                {
                    "推荐值（标准缺省） · 已核对",
                    "其他适用值 · 已核对",
                    "历史值 · 已弃用",
                },
            )
            self.assertEqual(page.selected_factor_id, "natural_gas_lhv_gbt32151_34_c1")
            heading = page.factor_detail_layout.itemAt(0).widget()
            self.assertIsInstance(heading, QLabel)
            assert isinstance(heading, QLabel)
            self.assertIn("天然气低位发热量", heading.text())
        finally:
            page.close()
            page.deleteLater()
            self.application.processEvents()

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
