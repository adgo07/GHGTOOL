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
    CalcinationInput,
    EmissionSourceStatus,
    HeatFactorMode,
    MaterialBasis,
    MaterialComponentKind,
)
from packages.standards.carbon_material_normalization import MaterialRole
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import tree_texts


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
        groups = {
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
        group = groups[source_id]
        if not self.page._source_is_enabled(source_id):
            self.page._source_toggle_buttons[group].click()
        self.application.processEvents()
    def _fill_calcination(self) -> None:
        self.page.enterprise_name.setText("UIR03 测试企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_involved(CALCINATION_SOURCE)
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
        self.assertFalse(controls["basis_summary"].isVisible())
        self.assertFalse(controls["basis_editor"].isVisible())
        for key in (
            "mass_basis",
            "composition_basis",
            "normalized_basis",
            "fixed_carbon_component_kind",
            "volatile_matter_component_kind",
        ):
            self.assertFalse(controls[key].isVisible())
        value = self.page._process("calcination", CalcinationInput)
        self.assertIsNotNone(value)
        assert value is not None
        self.assertIs(value.mass_basis, MaterialBasis.RECEIVED)
        self.assertIs(value.composition_basis, MaterialBasis.RECEIVED)
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))

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
            self.assertFalse(summary.isVisible())

        visible_text = "\n".join(
            widget.text()
            for widget in self.page.findChildren(QLabel)
            if widget.isVisible()
        )
        self.assertNotIn("挥发分折算系数", visible_text)
        self.assertNotIn("0.35", visible_text)
        for _, prefix, parameter_id in process_sources:
            details = self.page._material_controls[prefix]["professional_details"]
            self.assertIn(f"参数 ID：{parameter_id}", details.text())
            self.assertFalse(details.isVisible())

    def test_legacy_basis_rows_remain_blocked_without_conversion_evidence(self) -> None:
        self._fill_calcination()
        self._set_basis("DRY", "DRY")
        controls = self.page._material_controls["calcination"]
        current_input = self.page._input()
        current_process = current_input.calcinations[0]
        self.assertIs(current_process.mass_basis, MaterialBasis.DRY)
        self.assertIs(current_process.composition_basis, MaterialBasis.DRY)
        self.assertIs(current_process.normalized_basis, MaterialBasis.RECEIVED)
        self.assertFalse(current_process.moisture_evidence)
        self.assertFalse(current_process.conversion_evidence)
        self.assertIsNotNone(current_process.material_rows)
        self.assertTrue(controls["basis_warning"].text())

        outcome = self.page.calculator.calculate(current_input)
        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-MATERIAL-BASIS-CONVERSION" for problem in outcome.problems))
        self.assertIsNone(outcome.record)

    def test_documented_legacy_conversion_remains_supported_through_ui_mapping(self) -> None:
        self._fill_calcination()
        self._set_basis("DRY", "DRY")
        controls = self.page._material_controls["calcination"]
        controls["moisture_evidence"].setChecked(True)
        controls["conversion_evidence"].setChecked(True)
        controls["evidence_reference"].setText("历史项目换算依据")
        current_input = self.page._input()
        current_process = current_input.calcinations[0]
        self.assertIs(current_process.mass_basis, MaterialBasis.DRY)
        self.assertIs(current_process.composition_basis, MaterialBasis.DRY)
        self.assertIs(current_process.normalized_basis, MaterialBasis.RECEIVED)
        self.assertTrue(current_process.moisture_evidence)
        self.assertTrue(current_process.conversion_evidence)
        self.assertIsNotNone(current_process.material_rows)
        self.assertEqual(
            current_process.fixed_carbon_component_kind,
            MaterialComponentKind.FIXED_CARBON,
        )
        self.assertEqual(
            current_process.volatile_matter_component_kind,
            MaterialComponentKind.VOLATILE_MATTER,
        )

        outcome = self.page.calculator.calculate(current_input)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertFalse(any(problem.code == "CAR-VAL-MATERIAL-BASIS-CONVERSION" for problem in outcome.problems))
    def test_component_kinds_are_automatic_and_domain_values_remain_explicit(self) -> None:
        self._fill_calcination()
        controls = self.page._material_controls["calcination"]
        value = self.page._input()
        assert value.calcination is not None
        self.assertIs(value.calcination.fixed_carbon_component_kind, MaterialComponentKind.FIXED_CARBON)
        self.assertIs(value.calcination.volatile_matter_component_kind, MaterialComponentKind.VOLATILE_MATTER)
        self.assertFalse(controls["fixed_carbon_component_kind"].isVisible())
        self.assertFalse(controls["volatile_matter_component_kind"].isVisible())
    def test_ordinary_page_has_no_professional_details_toggle_or_visible_internal_ids(self) -> None:
        self._set_involved(CALCINATION_SOURCE)
        self._set_involved("CAR-SRC-PURCHASED-HEAT-001")
        controls = self.page._material_controls["calcination"]
        self.assertFalse(controls["professional_details"].isVisible())
        self.assertFalse(self.page.heat_factor_professional_details.isVisible())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
        visible_text = "\n".join(
            widget.text()
            for widget in self.page.findChildren(QLabel)
            if widget.isVisible()
        )
        self.assertNotIn("CAR-PAR-K1", visible_text)
        self.assertNotIn("因子 ID", visible_text)

    def test_power_and_heat_use_business_summary_with_simple_measured_factor_selection(self) -> None:
        self._set_involved(ELECTRICITY_SOURCE)
        row = self.page._energy_family_rows["electricity"][0]
        row.amount.setText("10")
        self.page._electricity("enterprise.current", self.page._period())
        for text in (row.status.text(),):
            self.assertNotIn("CAR-", text)
            self.assertNotIn("resolver", text)
            self.assertNotIn("candidate", text)

        self._set_involved("CAR-SRC-PURCHASED-HEAT-001")
        heat_row = self.page._energy_family_rows["heat"][0]
        factor_mode = heat_row.heat_factor_mode
        self.assertEqual(factor_mode.currentData(), HeatFactorMode.STANDARD_DEFAULT)
        self.assertFalse(heat_row.measured_heat_factor.isVisible())
        self.assertFalse(heat_row.heat_source.isVisible())
        factor_mode.setCurrentIndex(factor_mode.findData(HeatFactorMode.MEASURED))
        self.application.processEvents()
        self.assertTrue(heat_row.measured_heat_factor.isVisible())
        self.assertTrue(heat_row.heat_source.isVisible())
    def test_default_received_material_rows_ignore_legacy_hidden_basis_state(self) -> None:
        self._fill_calcination()
        default_value = self.page._input()
        default_outcome = self.page.calculator.calculate(default_value)
        self.assertTrue(default_outcome.successful, default_outcome.problems)

        self._set_basis("RECEIVED", "RECEIVED", "RECEIVED")
        controls = self.page._material_controls["calcination"]
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
    def test_material_row_validation_is_business_facing_without_technical_detail_panel(self) -> None:
        self._fill_calcination()
        self.page._process_rows["calcination"][0]["materials"][0]["name"].clear()
        self.page._run_calculation()
        self.application.processEvents()

        ordinary_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("必填信息不完整", ordinary_text)
        self.assertIn("物料名称", ordinary_text)
        self.assertNotIn("换算依据", ordinary_text)
        self.assertNotIn("CAR-VAL-", ordinary_text)
        self.assertNotIn("G05", ordinary_text)
        self.assertNotIn("resolver", ordinary_text)
        self.assertIsNone(self.page.findChild(QWidget, "calculationValidationProfessionalDetails"))
    def test_parameter_service_error_is_business_facing_without_technical_detail_panel(self) -> None:
        self._set_involved(ELECTRICITY_SOURCE)
        self.page.enterprise_name.setText("参数服务异常企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        row = self.page._energy_family_rows["electricity"][0]
        row.amount.setText("10")
        self.page.calculator.parameter_resolver = None
        self.page._parameter_resolver = None
        self.page._run_calculation()
        self.application.processEvents()

        ordinary_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("暂时无法取得适用的标准参数", ordinary_text)
        self.assertIn("必须修正", ordinary_text)
        roots = [
            self.page.validation_list.topLevelItem(index).text(0).split("（", 1)[0]
            for index in range(self.page.validation_list.topLevelItemCount())
        ]
        self.assertEqual(roots, ["提醒", "必须修正"])
        self.assertNotIn("CAR-VAL-", ordinary_text)
        self.assertNotIn("G05", ordinary_text)
        self.assertNotIn("resolver", ordinary_text)
        self.assertIsNone(self.page.findChild(QWidget, "calculationValidationProfessionalDetails"))

if __name__ == "__main__":
    unittest.main()
