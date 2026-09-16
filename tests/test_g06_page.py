from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import (
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
)
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    STANDARD_ID,
    MaterialBasis,
    MaterialComponentKind,
    EmissionSourceStatus,
)
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


class G06PageTests(unittest.TestCase):
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
            AppConfig(catalog_database=self.catalog_path), catalog_service=self.catalog_service
        )
        self.window.show()
        self.application.processEvents()
        shell = self.window.centralWidget()
        self.assertIsInstance(shell, AppShell)
        assert isinstance(shell, AppShell)
        self.shell = shell
        self.page = shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(self.page, CarbonMaterialAccountingPage)
        assert isinstance(self.page, CarbonMaterialAccountingPage)

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def test_page_exposes_g06_sections_and_all_ten_source_statuses(self) -> None:
        self.assertEqual(self.page.standard_id, STANDARD_ID)
        self.assertEqual(len(self.page._source_statuses), 10)
        self.assertEqual(len(self.page._electricity_rows), 1)
        for object_name in (
            "boundaryConfirmedCheckBox",
            "accountingStandardId",
            "addElectricityButton",
            "calculateAccountingButton",
            "calculationTrace",
            "calculationTotal",
            "calculationValidationList",
        ):
            self.assertIsNotNone(self.page.findChild(QWidget, object_name))

    def test_electricity_rows_keep_acquisition_and_attribute_independent(self) -> None:
        self.page.findChild(QWidget, "addElectricityButton").click()
        self.page.findChild(QWidget, "addElectricityButton").click()
        self.assertEqual(len(self.page._electricity_rows), 3)
        values = (
            ("10", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
            ("20", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.NONFOSSIL),
            ("30", ElectricityAcquisitionMode.SELF_CONSUMED, ElectricityAttribute.NONFOSSIL),
        )
        for row, (amount, acquisition, attribute) in zip(self.page._electricity_rows, values):
            row.amount.setText(amount)
            row.acquisition.setCurrentIndex(row.acquisition.findData(acquisition))
            row.attribute.setCurrentIndex(row.attribute.findData(attribute))

        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual(len(details), 3)
        self.assertEqual(
            [(item.acquisition_mode, item.attribute) for item in details],
            [
                (ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
                (ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.NONFOSSIL),
                (ElectricityAcquisitionMode.SELF_CONSUMED, ElectricityAttribute.NONFOSSIL),
            ],
        )
        self.assertEqual({item.detail_id for item in details}, {
            "electricity-detail-1",
            "electricity-detail-2",
            "electricity-detail-3",
        })

    def _set_source_involved(self, source_id: str) -> None:
        combo = self.page.findChild(QComboBox, f"sourceStatus_{source_id}")
        self.assertIsNotNone(combo)
        assert combo is not None
        combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))

    def test_electricity_rows_show_independent_factor_source_status_and_reason(self) -> None:
        self.page.period_year.setValue(2026)
        self.page.findChild(QWidget, "addElectricityButton").click()
        self.page.findChild(QWidget, "addElectricityButton").click()
        values = (
            ("10", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY, None),
            ("20", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.NONFOSSIL, ElectricityProofType.CONTRACT_AND_SETTLEMENT),
            ("30", ElectricityAcquisitionMode.SELF_CONSUMED, ElectricityAttribute.NONFOSSIL, ElectricityProofType.MONTHLY_ORIGINAL_RECORD),
        )
        for row, (amount, acquisition, attribute, proof_type) in zip(self.page._electricity_rows, values):
            row.amount.setText(amount)
            row.acquisition.setCurrentIndex(row.acquisition.findData(acquisition))
            row.attribute.setCurrentIndex(row.attribute.findData(attribute))
            if proof_type is not None:
                row.proof_type.setCurrentIndex(row.proof_type.findData(proof_type))
                row.proof_status.setCurrentIndex(row.proof_status.findData(ElectricityProofStatus.VALID))

        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual(len(details), 3)
        expected_factor_ids = (
            "electricity_national_average_2023",
            "electricity_nonfossil_zero_gbt32151_34_2024",
            "electricity_nonfossil_zero_gbt32151_34_2024",
        )
        for row, factor_id in zip(self.page._electricity_rows, expected_factor_ids):
            self.assertIn("已采用", row.parameter_status.text())
            self.assertIn(factor_id, row.parameter_factor.text())
            self.assertIn("来源", row.parameter_source.text())
            self.assertIn("审核状态", row.parameter_source.text())
            self.assertTrue(row.parameter_reason.text().strip())
            for object_name in (
                row.parameter_status.objectName(),
                row.parameter_factor.objectName(),
                row.parameter_source.objectName(),
                row.parameter_reason.objectName(),
            ):
                self.assertIsNotNone(self.page.findChild(QLabel, object_name))

    def test_page_declares_other_activity_and_transport_and_blocks(self) -> None:
        self.page.enterprise_name.setText("范围阻断企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.other_activity_present.setChecked(True)
        self.page.transport_present.setChecked(True)
        value = self.page._input()
        self.assertTrue(value.other_activity_present)
        self.assertTrue(value.transport_present)
        outcome = self.page.calculator.calculate(value)
        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-OTHER-STANDARD" for problem in outcome.problems))

    def test_page_has_independent_component_selectors_and_wrong_kind_blocks(self) -> None:
        self.page.enterprise_name.setText("成分字段企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        self.page._fields["calcination.gc"].setText("10")
        controls = self.page._material_controls["calcination"]
        controls["mass_basis"].setCurrentIndex(controls["mass_basis"].findData(MaterialBasis.RECEIVED))
        controls["composition_basis"].setCurrentIndex(controls["composition_basis"].findData(MaterialBasis.RECEIVED))
        controls["normalized_basis"].setCurrentIndex(controls["normalized_basis"].findData(MaterialBasis.RECEIVED))
        controls["fixed_carbon_component_kind"].setCurrentIndex(
            controls["fixed_carbon_component_kind"].findData(MaterialComponentKind.VOLATILE_MATTER)
        )
        controls["volatile_matter_component_kind"].setCurrentIndex(
            controls["volatile_matter_component_kind"].findData(MaterialComponentKind.VOLATILE_MATTER)
        )
        outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(any(
            problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
            and problem.field_id.endswith(".fixed-carbon")
            for problem in outcome.problems
        ))

        controls["fixed_carbon_component_kind"].setCurrentIndex(
            controls["fixed_carbon_component_kind"].findData(MaterialComponentKind.FIXED_CARBON)
        )
        controls["volatile_matter_component_kind"].setCurrentIndex(
            controls["volatile_matter_component_kind"].findData(MaterialComponentKind.FIXED_CARBON)
        )
        outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(any(
            problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
            and problem.field_id.endswith(".volatile-matter")
            for problem in outcome.problems
        ))

    def test_page_exposes_output_energy_and_explicit_material_basis_controls(self) -> None:
        for object_name in (
            "exportedElectricityAmountInput",
            "exportedHeatAmountInput",
            "exportedHeatSteamKindSelector",
            "heatFactorSelector",
        ):
            self.assertIsNotNone(self.page.findChild(QWidget, object_name))
        for prefix in ("calcination", "baking", "graphitization"):
            for suffix in (
                "massBasisSelector",
                "compositionBasisSelector",
                "normalizedBasisSelector",
                "fixedCarbonComponentKindSelector",
                "volatileMatterComponentKindSelector",
                "moistureEvidenceCheckBox",
                "conversionEvidenceCheckBox",
                "basisEvidenceReferenceInput",
            ):
                self.assertIsNotNone(self.page.findChild(QWidget, f"{prefix}_{suffix}"))
            mass_basis = self.page.findChild(QComboBox, f"{prefix}_massBasisSelector")
            fixed_component_kind = self.page.findChild(QComboBox, f"{prefix}_fixedCarbonComponentKindSelector")
            volatile_component_kind = self.page.findChild(QComboBox, f"{prefix}_volatileMatterComponentKindSelector")
            self.assertEqual(mass_basis.currentData(), MaterialBasis.UNKNOWN)
            self.assertEqual(fixed_component_kind.currentData(), MaterialComponentKind.UNKNOWN)
            self.assertEqual(volatile_component_kind.currentData(), MaterialComponentKind.UNKNOWN)

        self.page.enterprise_name.setText("输出能源控件企业")
        self.page.period_year.setValue(2026)
        self.page._fields["exported_electricity_amount"].setText("2")
        self.page._fields["exported_heat_amount"].setText("100")
        self.page._fields["exported_heat_enthalpy"].setText("2800")
        value = self.page._input()
        self.assertEqual(len(value.exported_electricity), 1)
        self.assertEqual(value.exported_electricity[0].amount.value, 2)
        self.assertEqual(len(value.exported_heat), 1)
        self.assertEqual(value.exported_heat[0].amount.value, 100)
        self.assertIsNotNone(value.exported_heat[0].factor)

    def test_empty_enterprise_name_is_required_and_does_not_create_record(self) -> None:
        self.page.boundary_confirmed.setChecked(True)
        self.page.calculate_button.click()
        self.application.processEvents()
        validation_text = "\n".join(
            self.page.validation_list.item(index).text()
            for index in range(self.page.validation_list.count())
        )
        self.assertIn("GEN-VAL-REQUIRED-MISSING", validation_text)
        self.assertNotIn("未填写企业", validation_text)
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

    def test_heat_parameter_selector_displays_source_review_and_selection_reason(self) -> None:
        self.page.enterprise_name.setText("热力参数选择企业")
        self.page.period_year.setValue(2026)
        self.application.processEvents()
        selector = self.page.findChild(QComboBox, "heatFactorSelector")
        metadata = self.page.findChild(QLabel, "heatFactorMetadata")
        reason = self.page.findChild(QLineEdit, "heatFactorSelectionReasonInput")
        self.assertIsNotNone(selector)
        self.assertGreater(selector.count(), 0)
        self.assertIn("heat_default_2025", [selector.itemData(index) for index in range(selector.count())])
        self.assertIn("来源", metadata.text())
        self.assertIn("审核", metadata.text())
        self.assertTrue(reason.text().strip())
        self.page._fields["heat_amount"].setText("1000")
        self.page._fields["heat_enthalpy"].setText("2800")
        value = self.page._input()
        selected = value.purchased_heat[0].factor
        self.assertIsNotNone(selected)
        self.assertEqual(selected.factor_id, selector.currentData())
        self.assertTrue(selected.source_id)
        self.assertTrue(selected.selection_reason.strip())

    def test_material_basis_without_conversion_evidence_is_blocked(self) -> None:
        self.page.enterprise_name.setText("基准证明企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        self.page._fields["calcination.gc"].setText("10")
        controls = self.page._material_controls["calcination"]
        for key, value in (
            ("mass_basis", MaterialBasis.DRY),
            ("composition_basis", MaterialBasis.DRY),
            ("normalized_basis", MaterialBasis.RECEIVED),
        ):
            combo = controls[key]
            combo.setCurrentIndex(combo.findData(value))
        fixed_component = controls["fixed_carbon_component_kind"]
        fixed_component.setCurrentIndex(fixed_component.findData(MaterialComponentKind.FIXED_CARBON))
        volatile_component = controls["volatile_matter_component_kind"]
        volatile_component.setCurrentIndex(volatile_component.findData(MaterialComponentKind.VOLATILE_MATTER))
        outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(any(problem.code == "CAR-VAL-MATERIAL-BASIS-CONVERSION" for problem in outcome.problems))
        self.assertTrue(outcome.blocked)

    def test_standard_entry_updates_the_g06_page_and_route(self) -> None:
        self.shell._request_standard_accounting(STANDARD_ID)
        self.application.processEvents()
        self.assertEqual(self.shell.current_route, AppRoute.NEW_ACCOUNTING)
        self.assertEqual(self.shell.selected_standard_id, STANDARD_ID)
        self.assertEqual(self.page.standard_id_label.text(), STANDARD_ID)

    def test_calculation_renders_result_and_boundary_error_without_persistence(self) -> None:
        self.page.enterprise_name.setText("UI 测试企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertIn("总排放量 ET：", self.page.result_total.text())
        self.assertIn("已形成 0 条参数快照", self.page.parameter_snapshot_summary.text())
        calculator_repository = self.page.calculator.record_repository
        self.assertEqual(len(calculator_repository.list_all()), 1)

        self.page.boundary_confirmed.setChecked(False)
        self.page.calculate_button.click()
        self.application.processEvents()
        validation_text = "\n".join(
            self.page.validation_list.item(index).text()
            for index in range(self.page.validation_list.count())
        )
        self.assertIn("CAR-VAL-BOUNDARY-UNCONFIRMED", validation_text)
        self.assertEqual(len(calculator_repository.list_all()), 1)


if __name__ == "__main__":
    unittest.main()
