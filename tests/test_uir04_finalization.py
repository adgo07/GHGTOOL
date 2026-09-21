from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import (
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    EmissionSourceSelection,
)
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    EmissionSourceStatus,
    InMemoryRecordRepository,
)
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard, SourceCardPresentationState
from packages.ui.view_models import AppRoute


I01 = "CAR-SRC-PURCHASED-ELECTRICITY-001"
I02 = "CAR-SRC-PURCHASED-HEAT-001"
P01 = "CAR-SRC-CALCINATION-001"
F01 = "CAR-SRC-FUEL-001"


class UIR04FinalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(cls.catalog_path),
            as_of=date(2026, 9, 12),
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
        self.application.processEvents()
        shell = self.window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.page = shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(self.page, CarbonMaterialAccountingPage)
        assert isinstance(self.page, CarbonMaterialAccountingPage)
        self.shell = shell

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def _status(self, source_id: str) -> QComboBox:
        combo = self.page.findChild(QComboBox, f"sourceStatus_{source_id}")
        self.assertIsNotNone(combo)
        assert combo is not None
        return combo

    def _involve(self, source_id: str) -> None:
        combo = self._status(source_id)
        combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))

    def _set_received_calcination(self) -> None:
        self._involve(P01)
        for field, value in {
            "gc": "100",
            "wfc": "50",
            "cc": "70",
            "ucc": "5",
            "du": "1",
            "wfc_c": "25",
            "wvar": "10",
            "wvar_c": "2",
        }.items():
            self.page._fields[f"calcination.{field}"].setText(value)

    def test_uncomputed_page_uses_compact_status_and_hides_empty_sections(self) -> None:
        self.assertFalse(self.page.result_card.isVisible())
        self.assertFalse(self.page.process_card.isVisible())
        self.assertFalse(self.page.quality_card.isVisible())
        self.assertTrue(self.page.findChild(QWidget, "calculationStatusBar").isVisible())
        self.assertTrue(self.page.calculate_button.isVisible())
        self.assertFalse(self.page.check_button.isVisible())
        self.assertIn("已确认排放源：0", self.page.confirmed_source_count.text())
        self.assertIn("错误：2", self.page.error_count.text())

    def test_basic_feedback_updates_without_calculation(self) -> None:
        self.page.enterprise_name.setText("实时检查企业")
        self.page.boundary_confirmed.setChecked(True)
        self.application.processEvents()
        self.assertIn("错误：0", self.page.error_count.text())

        self._involve(P01)
        self.application.processEvents()
        self.assertIn("已确认排放源：1", self.page.confirmed_source_count.text())
        self.assertIn("提醒：1", self.page.reminder_count.text())
        self.page._fields["calcination.gc"].setText("10")
        self.application.processEvents()
        self.assertIs(
            self.page._source_cards[P01].presentation_state,
            SourceCardPresentationState.NEEDS_ATTENTION,
        )
        self.assertIn("错误：1", self.page.error_count.text())

    def test_business_error_is_clickable_and_expands_own_source_card(self) -> None:
        self._involve(I02)
        self.page.enterprise_name.setText("错误定位企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        self.page._fields["heat_amount"].setText("1000")
        self.page._run_calculation()
        self.application.processEvents()

        items = [
            self.page.validation_list.item(index)
            for index in range(self.page.validation_list.count())
        ]
        target = next(
            (item for item in items if item.data(Qt.ItemDataRole.UserRole) == I02),
            None,
        )
        self.assertIsNotNone(target)
        assert target is not None
        self.assertIn("蒸汽状态资料不完整", target.text())
        self.assertNotIn("CAR-VAL-", target.text())
        self.page._source_cards[I02].set_expanded(False)
        self.page.validation_list.setCurrentItem(target)
        self.page.validation_list.itemClicked.emit(target)
        self.application.processEvents()
        self.assertTrue(self.page._source_cards[I02].is_expanded)

    def test_success_shows_business_result_and_details_on_demand(self) -> None:
        self.page.enterprise_name.setText("结果展示企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page._run_calculation()
        self.application.processEvents()

        self.assertTrue(self.page.result_card.isVisible())
        self.assertFalse(self.page.process_card.isVisible())
        self.assertFalse(self.page.quality_card.isVisible())
        self.assertIn("总排放量 ET：", self.page.result_total.text())
        self.assertIn("已完成", self.page.result_status.text())
        self.assertIn("直接排放 ES：", self.page.result_breakdown.text())
        self.assertIn("间接排放 EI：", self.page.result_breakdown.text())
        self.assertFalse(self.page.result_line_details.isVisible())

        self.page.view_breakdown_button.click()
        self.assertTrue(self.page.result_line_details.isVisible())
        self.assertNotIn("CAR-FLD-", self.page.result_line_details.text())
        self.page.view_process_button.click()
        self.assertTrue(self.page.process_card.isVisible())
        self.assertIn("计算过程已完成", self.page.trace_output.text())

    def test_fatal_error_keeps_result_hidden_and_creates_no_record(self) -> None:
        self.page.boundary_confirmed.setChecked(True)
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isVisible())
        self.assertTrue(self.page.quality_card.isVisible())
        self.assertIn("企业名称为必填项", self.page.validation_list.item(0).text())
        self.assertNotIn("GEN-VAL-", self.page.validation_list.item(0).text())
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

    def test_domain_error_keeps_result_hidden_even_when_result_object_exists(self) -> None:
        self.page.enterprise_name.setText("阻断结果企业")
        self.page.boundary_confirmed.setChecked(True)
        self._involve(P01)
        self.page._fields["calcination.gc"].setText("10")
        self.page._run_calculation()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isVisible())
        self.assertTrue(self.page.quality_card.isVisible())
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

    def test_ui_result_matches_independent_domain_calculation_and_record(self) -> None:
        self.page.enterprise_name.setText("结果等价企业")
        self.page.boundary_confirmed.setChecked(True)
        self._involve(F01)
        for key, value in (
            ("fuel_id", "natural-gas"),
            ("fuel_activity", "10"),
            ("fuel_carbon", "0.2"),
            ("fuel_oxidation", "98"),
        ):
            self.page._fields[key].setText(value)
        self._involve(I01)
        row = self.page._electricity_rows[0]
        row.detail_id.setText("grid-ordinary")
        row.amount.setText("20")
        row.acquisition.setCurrentIndex(row.acquisition.findData(ElectricityAcquisitionMode.PURCHASED))
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.ORDINARY))
        self.application.processEvents()

        before_input = self.page._input()
        independent = CarbonMaterialCalculator(
            parameter_resolver=self.page._parameter_resolver,
            record_repository=InMemoryRecordRepository(),
            standard_version=self.page.calculator.standard_version,
        )
        before_outcome = independent.calculate(before_input)
        self.assertTrue(before_outcome.successful, before_outcome.problems)

        self.page._run_calculation()
        self.application.processEvents()
        records = self.page.calculator.record_repository.list_all()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.input_snapshot.enterprise_name, before_input.enterprise_name)
        self.assertEqual(record.input_snapshot.period, before_input.period)
        self.assertEqual(
            record.input_snapshot.emission_sources,
            tuple(
                EmissionSourceSelection(
                    item.source_id,
                    item.status is EmissionSourceStatus.INVOLVED,
                )
                for item in before_input.source_states
            ),
        )
        self.assertEqual(record.calculation_result.total_amount, before_outcome.result.total_amount)
        self.assertEqual(record.calculation_result.lines, before_outcome.result.lines)
        self.assertEqual(
            [
                (item.parameter_id, item.factor_id, item.value_used, item.unit_used, item.detail_id)
                for item in record.parameter_snapshots
            ],
            [
                (item.parameter_id, item.factor_id, item.value_used, item.unit_used, item.detail_id)
                for item in before_outcome.parameter_snapshots
            ],
        )

    def test_common_window_sizes_keep_controls_visible_without_horizontal_scroll(self) -> None:
        for width, height in ((1920, 1080), (1366, 768)):
            self.window.resize(width, height)
            self.application.processEvents()
            self.assertEqual(
                self.shell.main_scroll_area.horizontalScrollBarPolicy(),
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
            self.assertFalse(self.shell.main_scroll_area.horizontalScrollBar().isVisible())
            self.assertTrue(self.page.calculate_button.isVisible())
            self.assertLessEqual(
                self.page.width(),
                self.shell.main_scroll_area.viewport().width(),
            )


if __name__ == "__main__":
    unittest.main()
