from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import EmissionSourceSelection
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import CarbonMaterialCalculator, EmissionSourceStatus, FuelPath
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material_normalization import MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard, SourceCardPresentationState
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import tree_items, tree_texts


I01 = "CAR-SRC-PURCHASED-ELECTRICITY-001"
I02 = "CAR-SRC-PURCHASED-HEAT-001"
P01 = "CAR-SRC-CALCINATION-001"
F01 = "CAR-SRC-FUEL-001"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


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

    def _involve(self, source_id: str) -> None:
        group_by_source = {
            "CAR-SRC-FUEL-001": "fuel",
            "CAR-SRC-CALCINATION-001": "calcination",
            "CAR-SRC-BAKING-001": "baking",
            "CAR-SRC-GRAPHITIZATION-001": "graphitization",
            "CAR-SRC-FUME-INCINERATION-001": "fume",
            "CAR-SRC-FGD-001": "fgd",
            "CAR-SRC-PURCHASED-ELECTRICITY-001": "electricity",
            "CAR-SRC-EXPORTED-ELECTRICITY-001": "electricity",
            "CAR-SRC-PURCHASED-HEAT-001": "heat",
            "CAR-SRC-EXPORTED-HEAT-001": "heat",
        }
        if not self.page._source_is_enabled(source_id):
            toggle = self.page.findChild(QWidget, f"sourceToggle_{group_by_source[source_id]}")
            self.assertIsNotNone(toggle)
            assert toggle is not None
            toggle.click()

    def _set_received_calcination(self) -> None:
        self._involve(P01)
        process = self.page._process_rows["calcination"][0]
        feed, = process["materials"]
        feed["role"].setCurrentIndex(feed["role"].findData(MaterialRole.CALCINATION_FEED))
        feed["name"].setText("煅烧原料")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("50")
        feed["volatile_matter"].setText("10")
        product = self.page._add_material_line(process)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("70")
        product["fixed_carbon"].setText("25")
        product["volatile_matter"].setText("2")

    def test_uncomputed_page_uses_compact_status_and_hides_empty_sections(self) -> None:
        self.assertFalse(self.page.result_card.isVisible())
        self.assertFalse(self.page.process_card.isVisible())
        self.assertFalse(self.page.quality_card.isVisible())
        self.assertTrue(self.page.findChild(QWidget, "calculationStatusBar").isVisible())
        self.assertTrue(self.page.calculate_button.isVisible())
        self.assertIsNotNone(self.page.findChild(QWidget, "calculateAccountingButton"))
        self.assertIsNone(self.page.findChild(QWidget, "checkAccountingButton"))
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
        self.assertIn("已确认排放源：0", self.page.confirmed_source_count.text())
        self.assertIn("错误：0", self.page.error_count.text())
        self.assertIn("点击“计算排放量”", self.page.calculation_status_hint.text())

    def test_error_count_comes_from_domain_validation_not_widget_heuristics(self) -> None:
        self.page.enterprise_name.setText("延后校验企业")
        self.page.boundary_confirmed.setChecked(True)
        self.application.processEvents()
        self.assertIn("错误：0", self.page.error_count.text())

        self._involve(P01)
        self.application.processEvents()
        self.assertIn("已确认排放源：1", self.page.confirmed_source_count.text())
        self.assertIn("错误：0", self.page.error_count.text())
        self.page._process_rows["calcination"][0]["materials"][0]["mass"].setText("100")
        self.application.processEvents()
        self.assertIs(
            self.page._source_cards[P01].presentation_state,
            SourceCardPresentationState.NEEDS_ATTENTION,
        )
        self.assertIn("错误：0", self.page.error_count.text())
        self.page._run_calculation()
        self.application.processEvents()
        self.assertGreater(int(self.page.error_count.text().split("：", 1)[1]), 0)

    def test_business_error_is_clickable_and_expands_own_source_card(self) -> None:
        self._involve(I02)
        self.page.enterprise_name.setText("错误定位企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        heat_row = self.page._energy_family_rows["heat"][0]
        heat_row.amount.setText("1")
        heat_row.pressure.clear()
        self.page._run_calculation()
        self.application.processEvents()

        items = tree_items(self.page.validation_list)
        target = next(
            (item for item in items if item.data(0, Qt.ItemDataRole.UserRole + 1) == I02
             and item.data(0, Qt.ItemDataRole.UserRole) is not None),
            None,
        )
        self.assertIsNotNone(target)
        assert target is not None
        self.assertIn("蒸汽状态资料不完整", target.text(0))
        self.assertNotIn("CAR-VAL-", target.text(0))
        self.page._source_cards[I02].set_expanded(False)
        self.page.validation_list.setCurrentItem(target)
        self.page.validation_list.itemClicked.emit(target, 0)
        self.application.processEvents()
        self.assertTrue(self.page._source_cards[I02].is_expanded)

    def test_success_shows_business_result_without_ordinary_trace_controls(self) -> None:
        self.page.enterprise_name.setText("结果展示企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page._run_calculation()
        self.application.processEvents()

        self.assertFalse(self.page.result_card.isHidden())
        self.assertFalse(self.page.process_card.isVisible())
        self.assertTrue(self.page.quality_card.isVisible())
        messages = tree_texts(self.page.validation_list)
        self.assertTrue(any("跨越所选标准的实施日期" in message for message in messages), messages)
        self.assertTrue(any("此提醒不阻断核算" in message for message in messages), messages)
        self.assertIn("温室气体排放总量：", self.page.result_total.text())
        self.assertIn("已完成", self.page.result_status.text())
        self.assertIn("直接排放量：", self.page.result_breakdown.text())
        self.assertIn("净间接排放量：", self.page.result_breakdown.text())
        self.assertIn("年度报告资格：符合年度报告周期要求", self.page.report_qualification_status.text())
        self.assertTrue(self.page.view_record_button.isEnabled())
        self.assertFalse(self.page.result_line_details.isVisible())

        self.page.view_breakdown_button.click()
        self.assertTrue(self.page.result_line_details.isVisible())
        self.assertNotIn("CAR-FLD-", self.page.result_line_details.text())
        self.assertIsNone(self.page.findChild(QWidget, "viewCalculationProcessButton"))
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
        self.assertTrue(self.page.process_card.isHidden())

    def test_empty_enterprise_name_is_optional_and_creates_a_record(self) -> None:
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isHidden())
        self.assertTrue(self.page.quality_card.isVisible())
        records = self.page.record_repository.list_all()
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].input_snapshot.enterprise_name)
        messages = tree_texts(self.page.validation_list)
        self.assertTrue(any("跨越所选标准的实施日期" in message for message in messages), messages)
        self.assertTrue(any("此提醒不阻断核算" in message for message in messages), messages)
        self.assertEqual(records[0].status.value, "COMPLETED_WITH_WARNINGS")

    def test_domain_error_keeps_result_hidden_even_when_result_object_exists(self) -> None:
        self.page.enterprise_name.setText("阻断结果企业")
        self.page.boundary_confirmed.setChecked(True)
        self._involve(P01)
        self.page._process_rows["calcination"][0]["materials"][0]["mass"].setText("100")
        self.page._run_calculation()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isVisible())
        self.assertTrue(self.page.quality_card.isVisible())
        self.assertEqual(self.page.record_repository.list_all(), ())

    def test_ui_result_matches_independent_domain_calculation_and_record(self) -> None:
        self.page.enterprise_name.setText("结果等价企业")
        self.page.boundary_confirmed.setChecked(True)
        self._involve(F01)
        fuel = self.page._fuel_rows[0]
        fuel.fuel_type.setCurrentIndex(fuel.fuel_type.findText("烟煤"))
        fuel.path.setCurrentIndex(fuel.path.findData(FuelPath.MASS))
        fuel.activity.setText("10")
        fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData("DIRECT"))
        fuel.carbon_direct.setText("0.2")
        fuel.source_reference.setText("燃料检测报告-1")
        self._involve(I01)
        row = self.page._energy_family_rows["electricity"][0]
        row.line_id.setText("grid-ordinary")
        row.amount.setText("20")
        row.attribute.setCurrentIndex(row.attribute.findData("ORDINARY"))
        self.application.processEvents()

        before_input = self.page._input()
        independent = CarbonMaterialCalculator(
            parameter_resolver=self.page._parameter_resolver,
            standard_version=self.page.calculator.standard_version,
        )
        before_outcome = independent.calculate(before_input)
        self.assertTrue(before_outcome.successful, before_outcome.problems)

        self.page._run_calculation()
        self.application.processEvents()
        records = self.page.record_repository.list_all()
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
        display_total = before_outcome.result.total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertIn(f"{display_total:.2f} tCO₂", self.page.result_total.text())
        self.assertNotIn(str(before_outcome.result.total_amount), self.page.result_total.text())
        self.assertEqual(record.calculation_result.total_amount, before_outcome.result.total_amount)
        self.page.view_breakdown_button.click()
        self.assertRegex(self.page.result_breakdown.text(), r"直接排放量：-?\d+\.\d{2} tCO₂")
        self.assertRegex(self.page.result_breakdown.text(), r"净间接排放量：-?\d+\.\d{2} tCO₂")
        self.assertNotIn("tCO2", self.page.result_breakdown.text())
        self.assertNotIn("ES", self.page.result_breakdown.text())
        self.assertNotIn("EI", self.page.result_breakdown.text())
        self.assertNotIn(str(before_outcome.result.total_amount), self.page.result_line_details.text())

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

    def test_common_windows_scale_factors_keep_controls_visible(self) -> None:
        for scale in ("1.0", "1.25", "1.5"):
            environment = os.environ.copy()
            environment.update(
                {
                    "QT_QPA_PLATFORM": "offscreen",
                    "QT_AUTO_SCREEN_SCALE_FACTOR": "0",
                    "QT_SCALE_FACTOR": scale,
                }
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "uir04_scale_acceptance.py"),
                    "--scale",
                    scale,
                ],
                cwd=PROJECT_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"scale={scale} failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )
            self.assertIn(f"scale={scale} PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
