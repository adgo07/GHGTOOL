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

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QAbstractItemView, QApplication, QLabel, QPushButton, QTableWidget

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
from packages.persistence.in_memory_records import InMemoryRecordRepository


def _standard_action_button(page: object, standard_id: str) -> QPushButton:
    buttons = page.findChildren(QPushButton, "startAccountingButton")  # type: ignore[attr-defined]
    for button in buttons:
        if button.property("standardId") == standard_id:
            return button
    raise AssertionError(f"no accounting button for {standard_id}")


class _MultiVersionRepository:
    """In-memory G04 fixture with three source-declared values for one parameter."""

    def __init__(self, repository: SQLiteCatalogRepository) -> None:
        self._repository = repository
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
        base_asset = next(
            asset for asset in repository.list_reference_data_assets()
            if asset.parameter_id == base_factor.parameter_id and asset.subject_id == base_factor.subject_id
        )
        self._assets = repository.list_reference_data_assets() + (
            replace(base_asset, asset_id="asset-natural-gas-lhv-other-2023", asset_version="2023",
                    value=Decimal("400"), source_value=Decimal("400"), normalized_value=Decimal("400"),
                    value_type=ValueType.GOVERNMENT_PUBLISHED, notes="测试夹具：其他适用值"),
            replace(base_asset, asset_id="asset-natural-gas-lhv-historical-2020", asset_version="2020",
                    value=Decimal("380"), source_value=Decimal("380"), normalized_value=Decimal("380"),
                    value_type=ValueType.HISTORICAL, notes="测试夹具：历史值"),
        )
        base_binding = next(
            binding for binding in repository.list_reference_data_bindings()
            if binding.factor_id == base_factor.factor_id
        )
        self._bindings = repository.list_reference_data_bindings() + (
            replace(base_binding, binding_id="binding-natural-gas-lhv-other-2023",
                    asset_id="asset-natural-gas-lhv-other-2023", factor_id=other_factor.factor_id,
                    factor_year=2023),
            replace(base_binding, binding_id="binding-natural-gas-lhv-historical-2020",
                    asset_id="asset-natural-gas-lhv-historical-2020", factor_id=historical_factor.factor_id,
                    factor_year=2020),
        )

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

    def list_source_tables(self):
        return self._repository.list_source_tables()

    def list_reference_data_assets(self):
        return self._assets

    def list_reference_data_bindings(self):
        return self._bindings

    def list_conversion_rules(self):
        return self._repository.list_conversion_rules()


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
            record_repository=InMemoryRecordRepository(),
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

    def test_industry_filter_does_not_infer_from_standard_titles(self) -> None:
        self.assertEqual(self.service.industry_options(), ("全部",))
        self.assertEqual(self.service.search_standards(industry="钢铁"), ())
        self.assertEqual(self.service.search_standards("有色"), ())
        self.assertTrue(
            all(industry == "—" for _, _, industry in self.service.search_standards())
        )

    def test_standard_detail_has_source_relationships_and_only_current_implemented_entry_can_start(self) -> None:
        detail = self.service.get_standard_detail("gbt_32151_34_2024")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.standard.standard_number, "GB/T 32151.34—2024")
        self.assertEqual(detail.standard.notes, "适用于炭素材料生产企业温室气体排放量的核算。")
        self.assertEqual(detail.standard.calculation_status, "IMPLEMENTED")
        self.assertEqual(detail.source.document_no, "GB/T 32151.34—2024")
        self.assertEqual(detail.base_standards[0].standard_id, "gbt_32150_2025")
        self.assertEqual(len(detail.parameters), 95)
        self.assertEqual(len(detail.factors), 95)
        self.assertTrue({
            "natural_gas_lhv",
            "natural_gas_carbon_content",
            "natural_gas_oxidation_rate",
            "electricity_emission_factor_nonfossil",
            "car-par-c2-caco3",
            "car-par-k1",
        }.issubset({parameter.parameter_id for parameter in detail.parameters}))

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
                "liquefied_natural_gas_lhv_gbt32151_34_c1",
                "liquefied_natural_gas_carbon_content_gbt32151_34_c1",
                "liquefied_natural_gas_oxidation_rate_gbt32151_34_c1",
            },
        )

        by_source = self.service.search_parameter_factors(
            "GB/T 32151.34",
            view_mode=ParameterViewMode.BY_SOURCE,
        )
        self.assertEqual(len(by_source), 99)
        self.assertTrue(all(item.source is not None for item in by_source))
        source_specific = self.service.search_parameter_factors(
            view_mode=ParameterViewMode.BY_SOURCE,
            source_id="SRC-32151-34-2024",
        )
        self.assertEqual(len(source_specific), 96)
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
        self.assertEqual(len(result), 96)
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

    def test_standard_detail_has_only_compact_verified_sections(self) -> None:
        self.shell.navigate(AppRoute.STANDARDS)
        self.application.processEvents()
        page = self.shell.pages[AppRoute.STANDARDS]
        page.search_input.setText("32151.34")
        self.application.processEvents()
        card_titles = [
            label.text()
            for label in page.detail_host.findChildren(QLabel, "cardTitle")
            if label.isVisible()
        ]
        self.assertEqual(
            card_titles,
            ["基本信息与官方来源", "标准关系", "适用范围", "参数与因子"],
        )
        detail_text = "\n".join(
            label.text()
            for label in page.detail_host.findChildren(QLabel)
            if label.isVisible()
        )
        self.assertIn("适用于炭素材料生产企业温室气体排放量的核算。", detail_text)
        self.assertIn("基础标准 / 通则", detail_text)
        self.assertIn("替代关系", detail_text)
        self.assertIn("规范性引用文件", detail_text)
        self.assertIn("暂无已核对的结构化数据。", detail_text)
        for forbidden in (
            "主管部门",
            "归口部门",
            "ICS",
            "CCS",
            "来源审核",
            "备注",
            "标准范围",
            "适用行业",
            "适用企业",
            "不适用情况",
            "核算边界",
            "排放源与温室气体",
            "核算方法",
            "数据质量与报告要求",
            "附录与标准依据",
            "基于标准名称的目录分类",
        ):
            self.assertNotIn(forbidden, card_titles)
            self.assertNotIn(forbidden, detail_text)

    def test_deep_catalog_scroll_covers_continuous_route_path(self) -> None:
        shell = self.shell
        self.window.resize(1180, 720)
        scrollbar = shell.main_scroll_area.verticalScrollBar()

        def assert_route_at_top(route: AppRoute) -> None:
            for _ in range(4):
                self.application.processEvents()
            self.assertEqual(shell.current_route, route)
            self.assertIs(shell.page_stack.currentWidget(), shell.pages[route])
            self.assertEqual(scrollbar.value(), scrollbar.minimum())
            title = shell.pages[route].findChild(QLabel, "pageTitle")
            self.assertIsNotNone(title)
            assert title is not None
            title_rect = title.rect()
            title_rect.moveTopLeft(title.mapTo(shell.main_scroll_area.viewport(), QPoint(0, 0)))
            self.assertTrue(shell.main_scroll_area.viewport().rect().intersects(title_rect))

        # Scenario C: 首页 → 标准库 → 参数库 → 新建核算 → 首页.
        shell.navigate(AppRoute.HOME)
        assert_route_at_top(AppRoute.HOME)
        self.assertEqual(scrollbar.maximum(), 0)

        shell.navigate(AppRoute.STANDARDS)
        assert_route_at_top(AppRoute.STANDARDS)
        self.assertGreater(scrollbar.maximum(), 0)
        standards_height = shell.page_stack.sizeHint().height()

        scrollbar.setValue(scrollbar.maximum())
        self.application.processEvents()
        self.assertEqual(scrollbar.value(), scrollbar.maximum())

        standards_page = shell.pages[AppRoute.STANDARDS]
        factors_button = standards_page.findChild(QPushButton, "viewFactorsButton")
        self.assertIsNotNone(factors_button)
        assert factors_button is not None
        factors_button.click()
        assert_route_at_top(AppRoute.FACTORS)

        shell.navigate(AppRoute.NEW_ACCOUNTING)
        assert_route_at_top(AppRoute.NEW_ACCOUNTING)

        shell.navigate(AppRoute.HOME)
        assert_route_at_top(AppRoute.HOME)
        self.assertEqual(scrollbar.maximum(), 0)
        home_height = shell.page_stack.sizeHint().height()
        self.assertLess(home_height, standards_height)

    def test_parameter_factor_page_browses_sources_and_aggregates_shared_assets(self) -> None:
        self.shell.navigate(AppRoute.FACTORS)
        self.application.processEvents()
        page = self.shell.pages[AppRoute.FACTORS]
        self.assertEqual(page.view_mode_filter.itemText(0), "按标准/文件查看")
        self.assertEqual(page.view_mode_filter.itemText(1), "全库搜索")
        self.assertEqual(page.source_filter.currentData(), "SRC-32151-34-2024")
        self.assertEqual(page.factor_table.rowCount(), 26)
        self.assertEqual(page.factor_table.columnCount(), 5)
        self.assertIn("天然气", [page.factor_table.item(row, 0).text() for row in range(page.factor_table.rowCount())])

        page.view_mode_filter.setCurrentIndex(1)
        page.search_input.setText("0.11")
        self.application.processEvents()
        heat_row = next(
            row for row in range(page.search_result_table.rowCount())
            if page.search_result_table.item(row, 0).text() == "参数值"
            and "外购热力" in page.search_result_table.item(row, 1).text()
        )
        page.search_result_table.selectRow(heat_row)
        self.application.processEvents()
        self.assertIn("2 处依据", page.search_result_table.item(heat_row, 4).text())
        detail_text = "\n".join(label.text() for label in page.factor_detail_host.findChildren(QLabel))
        self.assertIn("GB/T 32150—2025", detail_text)
        self.assertIn("GB/T 32151.34—2024", detail_text)
        self.assertIn("7.5.6", detail_text)
        self.assertIn("表C.3", detail_text)
        visible_text = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertNotIn("asset-heat_default", visible_text)
        self.assertNotIn("heat_default_gbt", visible_text)

        page.search_input.setText("饱和蒸汽")
        self.application.processEvents()
        self.assertTrue(any(
            page.search_result_table.item(row, 0).text() == "标准表"
            and "C.4" in page.search_result_table.item(row, 1).text()
            for row in range(page.search_result_table.rowCount())
        ))
        self.assertTrue(any(
            page.search_result_table.item(row, 0).text() == "来源文件"
            for row in range(page.search_result_table.rowCount())
        ))

        page.search_input.setText("GB/T 32151.34")
        self.application.processEvents()
        self.assertTrue(any(
            page.search_result_table.item(row, 0).text() == "标准"
            for row in range(page.search_result_table.rowCount())
        ))
        standard_row = next(
            row for row in range(page.search_result_table.rowCount())
            if page.search_result_table.item(row, 0).text() == "标准"
        )
        page.search_result_table.selectRow(standard_row)
        self.application.processEvents()
        detail_text = "\n".join(label.text() for label in page.factor_detail_host.findChildren(QLabel))
        self.assertIn("GB/T 32151.34—2024", detail_text)
        self.assertIn("实施日期", detail_text)
        self.assertNotIn("狀態", detail_text)
        self.assertTrue(page.findChild(QPushButton, "openOfficialReferenceButton"))

    def test_registered_source_tables_keep_dynamic_layout_and_calculator_providers(self) -> None:
        tables = self.service.list_source_tables("SRC-32151-34-2024")
        self.assertEqual({item.display_number for item in tables if item.display_number.startswith("C.")},
                         {"C.1", "C.2", "C.3", "C.4", "C.5"})
        c1 = next(item for item in tables if item.display_number == "C.1")
        c1_headers, c1_rows, _ = self.service.get_source_table_view(c1.source_table_id)
        self.assertEqual(len(c1_headers), 5)
        self.assertEqual(len(c1_rows), 26)
        self.assertEqual(c1_headers, ("燃料", "计量单位", "低位发热量", "单位热值含碳量", "碳氧化率"))
        c2 = next(item for item in tables if item.display_number == "C.2")
        self.assertEqual(len(self.service.get_source_table_view(c2.source_table_id)[1]), 11)

        for table in tables:
            if table.display_number in {"C.4", "C.5"}:
                headers, rows, note = self.service.get_source_table_view(table.source_table_id)
                self.assertGreater(len(rows), 0)
                self.assertGreaterEqual(len(headers), 2)
                self.assertIn("版本化计算器", note)
                if table.display_number == "C.4":
                    self.assertIn("1.70", note)
                    self.assertIn("1.80", note)

        page = self.shell.pages[AppRoute.FACTORS]
        self.assertGreater(page.table_filter.count(), 0)
        page.table_filter.setCurrentIndex(page.table_filter.findData(c2.source_table_id))
        self.application.processEvents()
        self.assertEqual(page.factor_table.rowCount(), 11)
        self.assertIn("C.2", page.browse_table_title.text())

    def test_multi_version_values_have_explicit_categories_in_service_and_page(self) -> None:
        service = CatalogQueryService(
            _MultiVersionRepository(self.repository),
            as_of=date(2026, 9, 12),
        )
        results = service.search_parameter_factors("天然气低位发热量")
        self.assertEqual(len(results), 4)
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
                "liquefied_natural_gas_lhv_gbt32151_34_c1": CatalogValueCategory.RECOMMENDED,
            },
        )
        page = ParameterFactorLibraryPage(service, lambda _route: None)
        page.show()
        self.application.processEvents()
        try:
            page.view_mode_filter.setCurrentIndex(1)
            page.search_input.setText("天然气低位发热量")
            self.application.processEvents()
            self.assertEqual(page.search_result_table.rowCount(), 4)
            visible_text = "\n".join(label.text() for label in page.findChildren(QLabel))
            self.assertNotIn("natural_gas", visible_text)
            self.assertNotIn("natural_gas_lhv_gbt32151_34_c1", visible_text)
            detail_heading = page.factor_detail_layout.itemAt(0).widget()
            self.assertIsInstance(detail_heading, QLabel)
            assert isinstance(detail_heading, QLabel)
            self.assertIn("天然气低位发热量", detail_heading.text())
        finally:
            page.close()
            page.deleteLater()
            self.application.processEvents()

    def test_reference_search_deduplicates_shared_assets_and_finds_steam_tables(self) -> None:
        heat = [item for item in self.service.search_reference_library("0.11")
                if item.result_type == "asset" and item.asset is not None
                and item.asset.parameter_id == "heat_emission_factor_default"]
        self.assertEqual(len(heat), 1)
        self.assertEqual(heat[0].asset.asset_id, "asset-heat_default_2025")
        self.assertEqual(len(heat[0].bindings), 2)
        locators = {binding.source_location for binding in heat[0].bindings}
        self.assertEqual(len(locators), 2)

        steam_tables = [item for item in self.service.search_reference_library("蒸汽")
                        if item.result_type == "table" and item.table is not None]
        self.assertEqual({item.table.display_number for item in steam_tables}, {"C.4", "C.5"})

        conversion_tables = [item for item in self.service.search_reference_library("kWh")
                             if item.result_type == "table" and item.table is not None]
        self.assertTrue(any(item.table.source_table_id == "tab-qz-unit-policy" for item in conversion_tables))

        source_results = [item for item in self.service.search_reference_library("QZ-UNIT-POLICY")
                          if item.result_type == "source" and item.source is not None]
        self.assertTrue(any(item.source.document_no == "QZ-UNIT-POLICY" for item in source_results))
        standard_results = [item for item in self.service.search_reference_library("GB/T 32151.34")
                            if item.result_type == "standard" and item.standard is not None]
        self.assertTrue(any(item.standard.standard_id == "gbt_32151_34_2024" for item in standard_results))

    def test_missing_catalog_degrades_to_safe_empty_pages(self) -> None:
        missing = Path(self.temp_directory.name) / "not-installed.sqlite"
        window = create_main_window(AppConfig(catalog_database=missing), record_repository=InMemoryRecordRepository())
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
            record_repository=InMemoryRecordRepository(),
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
            page.view_mode_filter.setCurrentIndex(1)
            page.search_input.setText("0.11")
            self.application.processEvents()
            heat_row = next(
                row for row in range(page.search_result_table.rowCount())
                if page.search_result_table.item(row, 0).text() == "参数值"
                and "外购热力" in page.search_result_table.item(row, 1).text()
            )
            page.search_result_table.selectRow(heat_row)
            self.application.processEvents()
            buttons = page.findChildren(QPushButton, "viewFactorSourceButton")
            self.assertTrue(buttons)
            self.assertTrue(all(not button.isEnabled() for button in buttons))
        finally:
            window.close()
            window.deleteLater()
            self.application.processEvents()


if __name__ == "__main__":
    unittest.main()
