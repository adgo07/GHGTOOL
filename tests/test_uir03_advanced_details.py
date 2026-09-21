from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import ElectricityAcquisitionMode, ElectricityAttribute
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    EmissionSourceStatus,
    InMemoryRecordRepository,
    MaterialBasis,
    MaterialComponentKind,
)
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard
from packages.ui.view_models import AppRoute


CALCINATION_SOURCE = "CAR-SRC-CALCINATION-001"
ELECTRICITY_SOURCE = "CAR-SRC-PURCHASED-ELECTRICITY-001"


class UIR03AdvancedDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.catalog_repository = SQLiteCatalogRepository(cls.catalog_path)
        cls.catalog_service = CatalogQueryService(cls.catalog_repository, as_of=date(2026, 9, 12))

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
        self.page = shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(self.page, CarbonMaterialAccountingPage)
        assert isinstance(self.page, CarbonMaterialAccountingPage)
        self.shell = shell
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def _set_involved(self, source_id: str) -> None:
        combo = self.page._source_statuses[source_id]
        combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))
        self.application.processEvents()

    def _fill_calcination(self) -> None:
        self.page.enterprise_name.setText("UIR03 测试企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_involved(CALCINATION_SOURCE)
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

    def _set_basis(self, mass: str, composition: str, normalized: str = "RECEIVED") -> None:
        controls = self.page._material_controls["calcination"]
        for key, value in (
            ("mass_basis", mass),
            ("composition_basis", composition),
            ("normalized_basis", normalized),
        ):
            controls[key].setCurrentIndex(controls[key].findData(value))
        self.application.processEvents()

    def test_received_basis_hides_advanced_fields_and_technical_terms(self) -> None:
        self._set_involved(CALCINATION_SOURCE)
        controls = self.page._material_controls["calcination"]
        self.assertEqual(controls["basis_summary"].text(), "数据口径：收到基")
        self.assertFalse(controls["basis_editor"].isVisible())
        for key in (
            "normalized_basis",
            "fixed_carbon_component_kind",
            "volatile_matter_component_kind",
        ):
            self.assertFalse(controls[key].isVisible())
        self.assertFalse(self.page.show_professional_details.isChecked())

        visible_widgets = [
            *self.page.findChildren(QLabel),
            *self.page.findChildren(QPushButton),
            *self.page.findChildren(QCheckBox),
        ]
        visible_text = "\n".join(widget.text() for widget in visible_widgets if widget.isVisible())
        for forbidden in (
            "物料质量基准",
            "成分含量基准",
            "归一化基准",
            "固定碳字段性质",
            "挥发分字段性质",
            "证据",
            "resolver",
            "candidate",
            "G05",
        ):
            self.assertNotIn(forbidden, visible_text)

    def test_process_cards_show_standard_default_parameter_summary(self) -> None:
        process_sources = (
            ("CAR-SRC-CALCINATION-001", "calcination", "CAR-PAR-K1"),
            ("CAR-SRC-BAKING-001", "baking", "CAR-PAR-K2"),
            ("CAR-SRC-GRAPHITIZATION-001", "graphitization", "CAR-PAR-K3"),
        )
        for source_id, prefix, parameter_id in process_sources:
            self._set_involved(source_id)
            summary = self.page._material_controls[prefix]["parameter_summary"]
            self.assertTrue(summary.isVisible())
            self.assertIn("默认排放参数：0.35（比例）· 标准默认", summary.text())
            self.assertNotIn(parameter_id, summary.text())

        self.page.show_professional_details.setChecked(True)
        self.application.processEvents()
        for _, prefix, parameter_id in process_sources:
            details = self.page._material_controls[prefix]["professional_details"]
            self.assertIn("标准默认参数：0.35（比例）", details.text())
            self.assertIn(f"参数 ID：{parameter_id}", details.text())

    def test_basis_mismatch_expands_and_explains_required_action(self) -> None:
        self._set_involved(CALCINATION_SOURCE)
        self._set_basis("DRY", "RECEIVED")
        controls = self.page._material_controls["calcination"]
        self.assertTrue(controls["basis_editor"].isVisible())
        self.assertIn("不一致", controls["basis_summary"].text())
        warning = controls["basis_warning"].text()
        self.assertIn("干燥基", warning)
        self.assertIn("收到基", warning)
        self.assertIn("不能直接计算", warning)
        self.assertIn("换算依据", warning)
        self.assertIn("报告/台账编号或来源说明", warning)

        self._set_basis("OTHER_DOCUMENTED", "OTHER_DOCUMENTED")
        self.assertIn("其他有证基准", controls["basis_summary"].text())
        self.assertIn("不能静默换算", controls["basis_warning"].text())

    def test_documented_conversion_maps_domain_basis_and_calculates(self) -> None:
        self._fill_calcination()
        self._set_basis("DRY", "DRY")
        controls = self.page._material_controls["calcination"]
        controls["moisture_evidence"].setChecked(True)
        controls["conversion_evidence"].setChecked(True)
        controls["evidence_reference"].setText("台账-UIR03-001")
        self.application.processEvents()

        value = self.page._input()
        assert value.calcination is not None
        self.assertIs(value.calcination.mass_basis, MaterialBasis.DRY)
        self.assertIs(value.calcination.composition_basis, MaterialBasis.DRY)
        self.assertIs(value.calcination.normalized_basis, MaterialBasis.RECEIVED)
        self.assertTrue(value.calcination.moisture_evidence)
        self.assertTrue(value.calcination.conversion_evidence)
        outcome = self.page.calculator.calculate(value)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertFalse(any(problem.code == "CAR-VAL-MATERIAL-BASIS-CONVERSION" for problem in outcome.problems))

    def test_component_kinds_are_automatic_and_domain_values_remain_explicit(self) -> None:
        self._set_involved(CALCINATION_SOURCE)
        self.page.enterprise_name.setText("字段性质自动识别企业")
        self.page._fields["calcination.gc"].setText("10")
        controls = self.page._material_controls["calcination"]
        value = self.page._input()
        assert value.calcination is not None
        self.assertIs(value.calcination.fixed_carbon_component_kind, MaterialComponentKind.FIXED_CARBON)
        self.assertIs(value.calcination.volatile_matter_component_kind, MaterialComponentKind.VOLATILE_MATTER)
        self.assertFalse(controls["fixed_carbon_component_kind"].isVisible())
        self.assertFalse(controls["volatile_matter_component_kind"].isVisible())

    def test_professional_details_toggle_reveals_audit_information_only(self) -> None:
        self._set_involved(CALCINATION_SOURCE)
        self._set_involved("CAR-SRC-PURCHASED-HEAT-001")
        controls = self.page._material_controls["calcination"]
        self.assertFalse(controls["professional_details"].isVisible())
        self.assertFalse(self.page.heat_factor_professional_details.isVisible())
        self.page.show_professional_details.setChecked(True)
        self.application.processEvents()
        self.assertTrue(controls["professional_details"].isVisible())
        self.assertIn("标准默认参数：0.35（比例）", controls["professional_details"].text())
        self.assertIn("参数 ID：CAR-PAR-K1", controls["professional_details"].text())
        self.assertIn("标准条款", controls["professional_details"].text())
        self.assertTrue(self.page.heat_factor_professional_details.isVisible())
        self.assertIn("因子 ID", self.page.heat_factor_professional_details.text())
        self.assertNotIn("resolver", controls["professional_details"].text())
        self.assertNotIn("candidate", self.page.heat_factor_professional_details.text())

    def test_power_and_heat_use_business_summary_with_optional_advanced_selection(self) -> None:
        self._set_involved(ELECTRICITY_SOURCE)
        row = self.page._electricity_rows[0]
        row.amount.setText("10")
        row.acquisition.setCurrentIndex(row.acquisition.findData(ElectricityAcquisitionMode.PURCHASED))
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.ORDINARY))
        self.page._electricity("enterprise.current", self.page._period())
        for text in (row.parameter_status.text(), row.parameter_factor.text(), row.parameter_source.text(), row.parameter_reason.text()):
            self.assertNotIn("CAR-", text)
            self.assertNotIn("resolver", text)
            self.assertNotIn("candidate", text)
        self._set_involved("CAR-SRC-PURCHASED-HEAT-001")
        self.assertIn("推荐热力因子", self.page.heat_factor_metadata.text())
        self.assertNotIn("heat_default_2025", self.page.heat_factor_metadata.text())
        self.assertFalse(self.page._heat_factor_advanced_panel.isVisible())
        self.page.heat_factor_edit_button.click()
        self.application.processEvents()
        self.assertTrue(self.page._heat_factor_advanced_panel.isVisible())

    def test_default_and_explicit_received_input_have_equal_domain_and_result(self) -> None:
        self._fill_calcination()
        controls = self.page._material_controls["calcination"]
        default_value = self.page._input()
        default_outcome = self.page.calculator.calculate(default_value)
        self.assertTrue(default_outcome.successful, default_outcome.problems)

        self._set_basis("RECEIVED", "RECEIVED", "RECEIVED")
        controls["fixed_carbon_component_kind"].setCurrentIndex(
            controls["fixed_carbon_component_kind"].findData("FIXED_CARBON")
        )
        controls["volatile_matter_component_kind"].setCurrentIndex(
            controls["volatile_matter_component_kind"].findData("VOLATILE_MATTER")
        )
        explicit_value = self.page._input()
        explicit_outcome = self.page.calculator.calculate(explicit_value)
        self.assertTrue(explicit_outcome.successful, explicit_outcome.problems)
        self.assertEqual(replace(default_value, input_id=explicit_value.input_id), explicit_value)
        assert default_outcome.result is not None
        assert explicit_outcome.result is not None
        self.assertEqual(default_outcome.result.total_amount, explicit_outcome.result.total_amount)
        self.assertEqual(default_outcome.result.lines, explicit_outcome.result.lines)
        snapshot_signature = lambda snapshot: (
            snapshot.parameter_id,
            snapshot.factor_id,
            snapshot.value_used,
            snapshot.unit_used,
            snapshot.source_id,
            snapshot.source_version,
            snapshot.selection_method,
            snapshot.selection_reason,
            snapshot.standard_id,
            snapshot.factor_version,
            snapshot.source_location,
            snapshot.factor_year,
            snapshot.detail_id,
        )
        self.assertEqual(
            [snapshot_signature(snapshot) for snapshot in default_outcome.parameter_snapshots],
            [snapshot_signature(snapshot) for snapshot in explicit_outcome.parameter_snapshots],
        )

    def test_validation_errors_are_business_facing_until_professional_details_open(self) -> None:
        self._fill_calcination()
        self._set_basis("DRY", "DRY")
        self.page._run_calculation()
        self.application.processEvents()

        ordinary_text = "\n".join(
            self.page.validation_list.item(index).text()
            for index in range(self.page.validation_list.count())
        )
        self.assertIn("不能直接计算", ordinary_text)
        self.assertIn("换算依据", ordinary_text)
        self.assertNotIn("证据", ordinary_text)
        self.assertNotIn("CAR-VAL-", ordinary_text)
        self.assertNotIn("G05", ordinary_text)
        self.assertNotIn("resolver", ordinary_text)
        self.assertFalse(self.page.validation_professional_details.isVisible())

        self.page.show_professional_details.setChecked(True)
        self.application.processEvents()
        professional_text = self.page.validation_professional_details.text()
        self.assertIn("CAR-VAL-MATERIAL-BASIS-CONVERSION", professional_text)
        self.assertIn("证据", professional_text)

    def test_parameter_service_error_is_business_facing_until_professional_details_open(self) -> None:
        self._set_involved("CAR-SRC-PURCHASED-HEAT-001")
        self.page.enterprise_name.setText("参数服务异常企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        self.page._fields["heat_amount"].setText("1000")
        self.page.calculator.parameter_resolver = None
        self.page._parameter_resolver = None
        self.page._run_calculation()
        self.application.processEvents()

        ordinary_text = "\n".join(
            self.page.validation_list.item(index).text()
            for index in range(self.page.validation_list.count())
        )
        self.assertIn("暂时无法取得标准参数", ordinary_text)
        self.assertNotIn("CAR-VAL-", ordinary_text)
        self.assertNotIn("G05", ordinary_text)
        self.assertNotIn("resolver", ordinary_text)

        self.page.show_professional_details.setChecked(True)
        self.application.processEvents()
        self.assertIn("CAR-VAL-PARAMETER-RESOLVER-MISSING", self.page.validation_professional_details.text())


if __name__ == "__main__":
    unittest.main()
