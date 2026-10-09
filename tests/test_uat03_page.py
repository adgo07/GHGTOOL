from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from packages.application.catalog_queries import CatalogQueryService
from packages.core import (
    ElectricityAttribute,
    ElectricityAcquisitionMode,
    ElectricityProofStatus,
    ElectricityProofType,
    ValueType,
)
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    CalcinationInput,
    EmissionSourceStatus,
    FuelPath,
    FuelType,
    MaterialBasis,
    MaterialComponentKind,
    ParameterSourceKind,
)
from packages.standards.carbon_material_normalization import MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.responsive_fields import ResponsiveFieldGrid


class UAT03AccountingPageV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.catalog_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = build_catalog_database(
            DEFAULT_SOURCE_PATH, Path(cls.catalog_directory.name) / "catalog.sqlite"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.catalog_directory.cleanup()

    def setUp(self) -> None:
        self.page = CarbonMaterialAccountingPage()

    def tearDown(self) -> None:
        self.page.close()
        self.app.processEvents()

    def _set_source(self, source_id: str, value: EmissionSourceStatus) -> None:
        combo = self.page._source_statuses[source_id]
        index = combo.findData(value)
        self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)

    def test_eight_source_toggles_use_business_labels_and_toggle_as_a_group(self) -> None:
        labels = [button.accessibleName() for button in self.page._source_toggle_buttons.values()]
        self.assertEqual(
            labels,
            ["化石燃料", "原料煅烧", "焙烧/炭化", "石墨化", "烟气焚烧", "烟气脱硫", "购入/输出电力", "购入/输出热力"],
        )
        purchase = self.page._source_statuses["CAR-SRC-PURCHASED-ELECTRICITY-001"]
        exported = self.page._source_statuses["CAR-SRC-EXPORTED-ELECTRICITY-001"]
        self.page._toggle_source_group("electricity")
        self.assertIs(self.page._source_is_enabled(purchase.objectName().removeprefix("sourceStatus_")), True)
        self.assertIs(self.page._source_is_enabled(exported.objectName().removeprefix("sourceStatus_")), True)
        self.page._toggle_source_group("electricity")
        self.assertIs(self.page._source_is_enabled("CAR-SRC-PURCHASED-ELECTRICITY-001"), False)
        self.assertIs(self.page._source_is_enabled("CAR-SRC-EXPORTED-ELECTRICITY-001"), False)

    def test_energy_families_have_separate_direction_lists_and_filter_disabled_sources(self) -> None:
        self.assertEqual(len(self.page._energy_family_rows["electricity"]), 1)
        self.assertEqual(len(self.page._energy_family_rows["heat"]), 1)
        purchased = self.page._energy_family_rows["electricity"][0]
        heat = self.page._energy_family_rows["heat"][0]
        self.assertEqual([purchased.kind.itemData(i) for i in range(purchased.kind.count())], ["purchased_electricity", "exported_electricity"])
        self.assertEqual([heat.kind.itemData(i) for i in range(heat.kind.count())], ["purchased_heat", "exported_heat"])
        self.assertIs(purchased.remove_button.isVisible(), False)
        self.assertIs(heat.remove_button.isVisible(), False)
        purchased.amount.setText("12.3456789")
        purchased.attribute.setCurrentIndex(purchased.attribute.findData(ElectricityAttribute.ORDINARY))
        purchased.factor_mode.setCurrentIndex(purchased.factor_mode.findData("MANUAL"))
        purchased.manual_factor.setText("0.522123456789")
        self._set_source("CAR-SRC-PURCHASED-ELECTRICITY-001", EmissionSourceStatus.NOT_INVOLVED)
        disabled = self.page._input(increment=False, render_electricity=False)
        self.assertEqual(disabled.electricity_details, ())
        self.assertEqual(purchased.amount.text(), "12.3456789")

        self._set_source("CAR-SRC-PURCHASED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)
        enabled = self.page._input(increment=False, render_electricity=False)
        self.assertEqual(len(enabled.electricity_details), 1)
        detail = enabled.electricity_details[0]
        self.assertIs(detail.acquisition_mode, ElectricityAcquisitionMode.PURCHASED)
        self.assertEqual(detail.electricity_amount, Decimal("12.3456789"))
        self.assertEqual(detail.factor_override.value, Decimal("0.522123456789"))
        self.assertIsNone(detail.selected_factor_id)

        output = self.page._add_unified_energy_row(kind="exported_electricity", line_id="output-line-1")
        output.amount.setText("3.25")
        output.factor_mode.setCurrentIndex(output.factor_mode.findData("MANUAL"))
        output.manual_factor.setText("0.522")
        output.electricity_source.setText("企业台账 2025-01")
        self._set_source("CAR-SRC-EXPORTED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)
        with patch.object(
            self.page,
            "_energy_electricity_parameter_unit",
            return_value=("electricity_emission_factor", "tCO₂/MWh"),
        ):
            result = self.page._input(increment=False, render_electricity=False)
        self.assertEqual(len(result.exported_electricity), 1)
        output_factor = result.exported_electricity[0].factor
        self.assertEqual(output_factor.unit, "tCO2/MWh")
        self.assertEqual(result.electricity_details[0].factor_override.unit, "tCO₂/MWh")
        self.assertIs(output_factor.source_kind, ParameterSourceKind.USER_DEFINED)
        self.assertIsNone(output_factor.factor_id)
        self.assertIsNone(output_factor.source_id)
        self.assertEqual(result.exported_electricity[0].region, output.region.currentData())

    def test_self_consumed_electricity_is_retained_and_excluded_from_formal_input(self) -> None:
        row = self.page._energy_family_rows["electricity"][0]
        row.amount.setText("2.5")
        row.attribute.setCurrentIndex(row.attribute.findData("SELF_CONSUMED_EXCLUDED"))
        self._set_source("CAR-SRC-PURCHASED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)
        self.assertEqual(self.page._electricity("enterprise.current", self.page._period(), render=False), ())
        self.assertEqual(row.amount.text(), "2.5")
        self.assertEqual(self.page._energy_row_state(row)["attribute"], "SELF_CONSUMED_EXCLUDED")

    def test_legacy_mixed_electricity_statuses_survive_state_restore(self) -> None:
        self._set_source("CAR-SRC-PURCHASED-ELECTRICITY-001", EmissionSourceStatus.NOT_INVOLVED)
        self._set_source("CAR-SRC-EXPORTED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)
        row = self.page._add_unified_energy_row(kind="exported_heat", line_id="heat-out-existing")
        row.amount.setText("1.75")
        state = self.page._capture_form_state()
        self.page._restore_form_state(state)
        self.assertFalse(self.page._source_is_enabled("CAR-SRC-PURCHASED-ELECTRICITY-001"))
        self.assertTrue(self.page._source_is_enabled("CAR-SRC-EXPORTED-ELECTRICITY-001"))
        restored = next(item for item in self.page._energy_rows if item.kind.currentData() == "exported_heat")
        self.assertEqual(restored.line_id.text(), "heat-out-existing")
        self.assertEqual(restored.amount.text(), "1.75")

    def test_first_fuel_row_cannot_be_removed_even_when_secondary_rows_exist(self) -> None:
        first = self.page._fuel_rows[0]
        self.page._add_fuel_row()
        self.assertEqual(len(self.page._fuel_rows), 2)
        self.page._remove_fuel_row(first)
        self.assertEqual(len(self.page._fuel_rows), 2)
        self.assertIs(self.page._fuel_rows[0], first)
        self.assertFalse(first.remove_button.isVisible())

    def test_direct_carbon_path_keeps_heat_defaults_and_full_decimal_precision(self) -> None:
        def factor(parameter_id: str, value: str, unit: str, suffix: str):
            return SimpleNamespace(
                parameter_id=parameter_id,
                value=Decimal(value),
                unit=unit,
                value_type=ValueType.STANDARD_DEFAULT,
                source_id=f"SOURCE-{suffix}",
                version="2025",
                source_location=f"Appendix C.1 {suffix}",
                factor_id=f"FACTOR-{suffix}",
                factor_year=2025,
            )

        resolved = (
            factor("LOWER_HEATING_VALUE", "389.31", "GJ/t", "LHV"),
            factor("CARBON_CONTENT_PER_HEAT", "0.0153", "tC/GJ", "C"),
            factor("OXIDATION_RATE", "0.94", "ratio", "OX"),
        )
        row = self.page._fuel_rows[0]
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        with patch.object(self.page, "_fuel_default_factors", return_value=resolved):
            self.page._refresh_fuel_row(row, initialize_defaults=True)
            self.assertEqual(row.lower_heating_value.text(), "389.31")
            self.assertEqual(row.carbon.text(), "0.0153")
            self.assertIn("5.96", row.calculated_carbon_label.text())
            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
            row.carbon_direct.setText("0.001234567890123")
            self.page._refresh_fuel_row(row)
            self.assertEqual(row.lower_heating_value.text(), "389.31")
            self.assertEqual(row.carbon.text(), "0.0153")
            self.assertEqual(row.lhv_source.currentData(), "STANDARD_DEFAULT")
            self.assertEqual(row.direct_carbon_source.currentData(), "MEASURED")
            direct = self.page._fuel()[0]
            self.assertIsNone(direct.lower_heating_value)
            self.assertEqual(direct.carbon_content.value, Decimal("0.001234567890123"))
            self.assertEqual(direct.carbon_content.unit, "tC/t")
            self.assertIs(direct.carbon_content.source_kind, ParameterSourceKind.MEASURED)

            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("HEAT_CONTENT"))
            self.page._refresh_fuel_row(row)
            calculation = self.page._fuel()[0]
            self.assertEqual(calculation.lower_heating_value.value, Decimal("389.31"))
            self.assertEqual(calculation.carbon_content.value, Decimal("0.0153"))
            self.assertEqual(row.lower_heating_value.text(), "389.31")
            self.assertEqual(row.carbon.text(), "0.0153")


    def test_project_unit_controls_are_attached_and_folded_by_default(self) -> None:
        self.assertTrue(self.page.project_unit_card.isHidden())
        self.page.project_unit_toggle.click()
        self.assertFalse(self.page.project_unit_card.isHidden())
        for widget in (
            self.page.project_name,
            self.page.save_project_button,
            self.page.unit_selector,
            self.page.manage_process_button,
        ):
            self.assertFalse(widget.isHidden())

    def test_fume_inputs_use_the_responsive_two_or_three_column_grid(self) -> None:
        row = self.page._process_rows["fume"][0]
        grid = row.get("responsive_fields")
        self.assertIsInstance(grid, ResponsiveFieldGrid)
        self.assertEqual(len(row["fields"]), 6)
        probe = ResponsiveFieldGrid(three_column_width=900)
        try:
            for index in range(6):
                probe.add_field(f"字段{index + 1}", QLineEdit(probe))
            probe.show()
            probe.resize(850, 240)
            self.app.processEvents()
            self.assertEqual(probe._columns, 2)
            probe.resize(900, 240)
            self.app.processEvents()
            self.assertEqual(probe._columns, 3)
        finally:
            probe.close()

    def test_source_status_uses_effective_directions_and_keeps_partial_entries(self) -> None:
        self.page._toggle_source_group("electricity")
        empty = {item.source_id: item.status for item in self.page._source_states()}
        self.assertIs(empty["CAR-SRC-PURCHASED-ELECTRICITY-001"], EmissionSourceStatus.NOT_INVOLVED)
        self.assertIs(empty["CAR-SRC-EXPORTED-ELECTRICITY-001"], EmissionSourceStatus.NOT_INVOLVED)

        row = self.page._energy_family_rows["electricity"][0]
        row.amount.setText("2.5")
        with_activity = {item.source_id: item.status for item in self.page._source_states()}
        self.assertIs(with_activity["CAR-SRC-PURCHASED-ELECTRICITY-001"], EmissionSourceStatus.INVOLVED)
        self.assertIs(with_activity["CAR-SRC-EXPORTED-ELECTRICITY-001"], EmissionSourceStatus.NOT_INVOLVED)

        row.amount.clear()
        row.factor_mode.setCurrentIndex(row.factor_mode.findData("MANUAL"))
        row.manual_factor.setText("0.5234567890123")
        partial = {item.source_id: item.status for item in self.page._source_states()}
        self.assertIs(partial["CAR-SRC-PURCHASED-ELECTRICITY-001"], EmissionSourceStatus.INVOLVED)
        self.assertEqual(self.page._electricity("enterprise.current", self.page._period(), render=False), ())

        row.attribute.setCurrentIndex(row.attribute.findData("SELF_CONSUMED_EXCLUDED"))
        row.amount.setText("2.5")
        excluded = {item.source_id: item.status for item in self.page._source_states()}
        self.assertIs(excluded["CAR-SRC-PURCHASED-ELECTRICITY-001"], EmissionSourceStatus.NOT_INVOLVED)
        self.assertIs(excluded["CAR-SRC-EXPORTED-ELECTRICITY-001"], EmissionSourceStatus.NOT_INVOLVED)

    def test_legacy_fossil_attribute_and_electricity_proof_survive_family_roundtrip(self) -> None:
        self.page._restore_unified_energy_rows([
            {
                "kind": "purchased_electricity",
                "line_id": "legacy-fossil-line",
                "amount": "1.25",
                "attribute": "FOSSIL",
                "legacy_attribute": "FOSSIL",
                "proof_type": "GEC",
                "proof_status": "VALID",
            },
            {"kind": "purchased_heat", "line_id": "heat-line-1"},
        ])
        first = self.page._energy_family_rows["electricity"][0]
        self.assertIs(first.legacy_attribute, ElectricityAttribute.FOSSIL)
        self.assertEqual(first.attribute.findData(ElectricityAttribute.FOSSIL), -1)
        self.assertEqual(first.legacy_proof_type.value, "GEC")
        self.assertEqual(first.legacy_proof_status.value, "VALID")
        self.page._restore_unified_energy_rows(self.page._capture_form_state()["energy_rows"])
        restored = self.page._energy_family_rows["electricity"][0]
        state = self.page._energy_row_state(restored)
        self.assertEqual(state["legacy_attribute"], "FOSSIL")
        self.assertEqual(state["proof_type"], "GEC")
        self.assertEqual(state["proof_status"], "VALID")
        self.assertEqual(state["line_id"], "legacy-fossil-line")

    def test_real_catalog_fuel_defaults_and_direct_measurement_keep_provenance(self) -> None:
        page = CarbonMaterialAccountingPage(
            catalog_service=CatalogQueryService(SQLiteCatalogRepository(self.catalog_path))
        )
        try:
            row = page._fuel_rows[0]
            option = next(item for item in page._fuel_catalog_options() if item.fuel_type is FuelType.NATURAL_GAS)
            row.fuel_type.setEditText(option.label)
            row.activity.setText("12.3456789012345")
            self.assertIs(FuelPath(row.path.currentData()), FuelPath.VOLUME)
            selected = page._fuel()[0]
            self.assertEqual(selected.activity.value, Decimal("12.3456789012345"))
            self.assertEqual(selected.lower_heating_value.value, Decimal("389.31"))
            self.assertEqual(selected.lower_heating_value.unit, "GJ/10⁴Nm³")
            self.assertIs(selected.lower_heating_value.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
            self.assertIsNotNone(selected.lower_heating_value.factor_id)
            self.assertEqual(selected.carbon_content.value, Decimal("0.0153"))
            self.assertEqual(selected.carbon_content.unit, "tC/GJ")
            self.assertEqual(selected.oxidation_rate.value, Decimal("0.99"))
            self.assertTrue(row.oxidation_source.isHidden())
            self.assertTrue(row.source_reference.isHidden())
            self.assertTrue(row.source_reference_label.isHidden())

            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
            row.carbon_direct.setText("0.001234567890123")
            direct = page._fuel()[0]
            self.assertIsNone(direct.lower_heating_value)
            self.assertEqual(direct.lower_heating_value, None)
            self.assertEqual(direct.carbon_content.value, Decimal("0.001234567890123"))
            self.assertEqual(direct.carbon_content.unit, "tC/10^4Nm3")
            self.assertIs(direct.carbon_content.source_kind, ParameterSourceKind.MEASURED)
            self.assertIsNone(direct.carbon_content.source_id)
            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("HEAT_CONTENT"))
            self.assertEqual(row.lower_heating_value.text(), "389.31")
            self.assertEqual(row.carbon.text(), "0.0153")
        finally:
            page.close()
            self.app.processEvents()


    def test_legacy_fuel_values_and_source_kinds_roundtrip_without_v2_overwrite(self) -> None:
        page = CarbonMaterialAccountingPage(
            catalog_service=CatalogQueryService(SQLiteCatalogRepository(self.catalog_path))
        )
        try:
            option = next(item for item in page._fuel_catalog_options() if item.fuel_type is FuelType.NATURAL_GAS)
            state = page._capture_form_state()
            state["fuel_rows"] = [{
                "row_key": "legacy-gas",
                "id": "legacy-gas-id",
                "type_value": FuelType.NATURAL_GAS.value,
                "fuel_name": option.label,
                "fuel_label": "",
                "path": 0,
                "carbon_basis": 1,
                "activity": "10.123456789",
                "lower_heating_value": "380",
                "carbon": "0.0153",
                "carbon_direct": "0.123456",
                "oxidation": "97.1234",
                "source_reference": "旧检测资料",
                # Previous four-choice source controls used 0=default, 1=calculated,
                # 2=measured, and 3=user-defined.
                "lhv_source": 2,
                "carbon_source": 2,
                "direct_carbon_source": 3,
                "oxidation_source": 2,
                "parameter_source": "MEASURED",
            }]
            page._restore_form_state(state)
            row = page._fuel_rows[0]
            self.assertEqual(row.lower_heating_value.text(), "380")
            self.assertEqual(row.oxidation.text(), "97.1234")
            self.assertEqual(row.carbon_direct.text(), "0.123456")
            self.assertEqual(page._fuel_source_mode(row, "lhv"), "MEASURED")
            self.assertEqual(page._fuel_source_mode(row, "carbon"), "MEASURED")
            self.assertEqual(page._fuel_source_mode(row, "direct_carbon"), "USER_DEFINED")
            self.assertEqual(page._fuel_source_mode(row, "oxidation"), "MEASURED")

            direct = page._fuel()[0]
            self.assertEqual(direct.path, FuelPath.VOLUME)
            self.assertIsNone(direct.lower_heating_value)
            self.assertEqual(row.lower_heating_value.text(), "380")
            self.assertEqual(direct.carbon_content.value, Decimal("0.123456"))
            self.assertIs(direct.carbon_content.source_kind, ParameterSourceKind.USER_DEFINED)
            self.assertEqual(direct.oxidation_rate.value, Decimal("0.971234"))
            self.assertIs(direct.oxidation_rate.source_kind, ParameterSourceKind.MEASURED)

            saved = page._capture_form_state()
            page._restore_form_state(saved)
            roundtrip = page._fuel()[0]
            self.assertIsNone(roundtrip.lower_heating_value)
            self.assertEqual(roundtrip.carbon_content.value, direct.carbon_content.value)
            self.assertEqual(roundtrip.oxidation_rate.value, direct.oxidation_rate.value)
            self.assertIs(roundtrip.carbon_content.source_kind, ParameterSourceKind.USER_DEFINED)

            row = page._fuel_rows[0]
            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("HEAT_CONTENT"))
            calculated = page._fuel()[0]
            self.assertEqual(calculated.lower_heating_value.value, Decimal("380"))
            self.assertIs(calculated.lower_heating_value.source_kind, ParameterSourceKind.MEASURED)
            self.assertEqual(calculated.carbon_content.value, Decimal("0.0153"))
            self.assertIs(calculated.carbon_content.source_kind, ParameterSourceKind.MEASURED)
            self.assertEqual(calculated.oxidation_rate.value, Decimal("0.971234"))
            row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))

            # A historical heat-activity path stays hidden in the chooser but
            # remains calculable with its saved C/GJ carbon content and sources.
            state = page._capture_form_state()
            state["fuel_rows"][0]["path"] = 2
            state["fuel_rows"][0]["carbon_basis"] = 0
            page._restore_form_state(state)
            legacy_heat = page._fuel()[0]
            self.assertEqual(legacy_heat.path, FuelPath.HEAT)
            self.assertEqual(page._fuel_rows[0].lower_heating_value.text(), "380")
            self.assertIsNone(legacy_heat.lower_heating_value)
            self.assertEqual(legacy_heat.carbon_content.value, Decimal("0.0153"))
            self.assertIs(legacy_heat.carbon_content.source_kind, ParameterSourceKind.MEASURED)
            self.assertEqual(legacy_heat.oxidation_rate.value, Decimal("0.971234"))
            self.assertIs(legacy_heat.oxidation_rate.source_kind, ParameterSourceKind.MEASURED)
            self.assertTrue(page._fuel_rows[0].path.view().isRowHidden(2))
        finally:
            page.close()
            self.app.processEvents()


    def test_new_accounting_reset_keeps_one_row_per_energy_family(self) -> None:
        self.page._add_unified_energy_row(kind="exported_electricity", line_id="extra-power")
        self.page._add_unified_energy_row(kind="exported_heat", line_id="extra-heat")
        self.page._energy_family_rows["electricity"][0].amount.setText("99")
        self.page._energy_family_rows["heat"][0].amount.setText("88")
        self.page._reset_for_new_accounting()
        self.assertEqual(len(self.page._energy_family_rows["electricity"]), 1)
        self.assertEqual(len(self.page._energy_family_rows["heat"]), 1)
        self.assertEqual(self.page._energy_family_rows["electricity"][0].amount.text(), "")
        self.assertEqual(self.page._energy_family_rows["heat"][0].amount.text(), "")

    def test_source_toggle_host_width_covers_all_business_labels(self) -> None:
        buttons = tuple(self.page._source_toggle_buttons.values())
        expected_width = sum(button.minimumWidth() for button in buttons)
        layout = self.page.source_toggle_host.layout()
        expected_width += max(0, len(buttons) - 1) * max(0, layout.spacing())
        margins = layout.contentsMargins()
        expected_width += margins.left() + margins.right()
        self.assertGreaterEqual(self.page.source_toggle_host.minimumWidth(), expected_width)
        self.assertGreater(self.page.source_toggle_host.minimumWidth(), self.page.source_toggle_scroll.width())
        self.assertIn("购入/输出热力", buttons[-1].text())
        self.assertIn("未启用", buttons[-1].accessibleDescription())


    def test_resolver_lhv_unit_recommends_each_fuel_path_without_changing_entered_units(self) -> None:
        page = CarbonMaterialAccountingPage(
            catalog_service=CatalogQueryService(SQLiteCatalogRepository(self.catalog_path))
        )
        try:
            row = page._fuel_rows[0]
            options = page._fuel_catalog_options()
            anthracite = next(item for item in options if item.label == "无烟煤")
            natural_gas = next(item for item in options if item.label == "天然气")
            row.fuel_type.setEditText(anthracite.label)
            self.assertEqual(FuelPath(row.path.currentData()), FuelPath.MASS)
            row.activity.setText("10")
            row.fuel_type.setEditText(natural_gas.label)
            self.assertEqual(FuelPath(row.path.currentData()), FuelPath.MASS)
            self.assertIn("计量单位与该燃料", row.activity.toolTip())
            row.activity.clear()
            row.fuel_type.setEditText(anthracite.label)
            row.fuel_type.setEditText(natural_gas.label)
            self.assertEqual(FuelPath(row.path.currentData()), FuelPath.VOLUME)
        finally:
            page.close()
            self.app.processEvents()

    def test_direct_carbon_validation_target_uses_the_active_measured_field(self) -> None:
        row = self.page._fuel_rows[0]
        row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
        field_id = f"CAR-FLD-F01-{row.internal_id.text()}-CARBON"
        self.assertEqual(self.page._validation_target_name(field_id, "CAR-SRC-FUEL-001"), "fuelMeasuredCarbonInput1")

    def test_process_input_preserves_historical_basis_component_and_evidence_controls(self) -> None:
        row = self.page._process_rows["calcination"][0]
        controls = self.page._material_controls[str(row["controls_key"])]
        for key, value in (
            ("mass_basis", MaterialBasis.DRY),
            ("composition_basis", MaterialBasis.DRY),
            ("normalized_basis", MaterialBasis.RECEIVED),
            ("fixed_carbon_component_kind", MaterialComponentKind.TOTAL_CARBON),
            ("volatile_matter_component_kind", MaterialComponentKind.VOLATILE_MATTER),
        ):
            widget = controls[key]
            widget.setCurrentIndex(widget.findData(value))
        controls["moisture_evidence"].setChecked(True)
        controls["conversion_evidence"].setChecked(True)
        controls["evidence_reference"].setText("旧工作区检测报告 2025-01")
        state = self.page._capture_form_state()
        self.page._restore_form_state(state)
        self._set_source("CAR-SRC-CALCINATION-001", EmissionSourceStatus.INVOLVED)

        calculation_input = self.page._input(increment=False, render_electricity=False)
        restored = calculation_input.calcinations[0]
        self.assertIs(restored.mass_basis, MaterialBasis.DRY)
        self.assertIs(restored.composition_basis, MaterialBasis.DRY)
        self.assertIs(restored.normalized_basis, MaterialBasis.RECEIVED)
        self.assertIs(restored.fixed_carbon_component_kind, MaterialComponentKind.TOTAL_CARBON)
        self.assertTrue(restored.moisture_evidence)
        self.assertTrue(restored.conversion_evidence)
        restored_controls = self.page._material_controls[str(self.page._process_rows["calcination"][0]["controls_key"])]
        self.assertEqual(restored_controls["evidence_reference"].text(), "旧工作区检测报告 2025-01")

    def test_legacy_v1_self_consumed_fossil_electricity_keeps_canonical_semantics(self) -> None:
        legacy = self.page._electricity_rows[0]
        legacy.amount.setText("15")
        legacy.acquisition.setCurrentIndex(legacy.acquisition.findData(ElectricityAcquisitionMode.SELF_CONSUMED))
        legacy.attribute.setCurrentIndex(legacy.attribute.findData(ElectricityAttribute.FOSSIL))
        legacy.proof_type.setCurrentIndex(legacy.proof_type.findData(ElectricityProofType.GEC))
        legacy.proof_status.setCurrentIndex(legacy.proof_status.findData(ElectricityProofStatus.VALID))
        self._set_source("CAR-SRC-PURCHASED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)

        self.page._migrate_legacy_energy_rows()
        saved_state = self.page._capture_form_state()
        self.page._restore_form_state(saved_state)
        restored_input = self.page._input(increment=False, render_electricity=False)
        self.assertEqual(len(restored_input.electricity_details), 1)
        detail = restored_input.electricity_details[0]
        self.assertIs(detail.acquisition_mode, ElectricityAcquisitionMode.SELF_CONSUMED)
        self.assertIs(detail.attribute, ElectricityAttribute.FOSSIL)
        self.assertIs(detail.proof_type, ElectricityProofType.GEC)
        self.assertIs(detail.proof_status, ElectricityProofStatus.VALID)

    def test_legacy_output_electricity_measurement_keeps_measured_provenance(self) -> None:
        row = self.page._output_electricity_rows[0]
        row["id"].setText("old-output-line")
        row["amount"].setText("2")
        row["measured"].setText("0.6")
        row["source"].setText("LAB-OUT-01")
        self._set_source("CAR-SRC-EXPORTED-ELECTRICITY-001", EmissionSourceStatus.INVOLVED)

        self.page._migrate_legacy_energy_rows()
        self.page._restore_form_state(self.page._capture_form_state())
        output = self.page._input(increment=False, render_electricity=False).exported_electricity[0]
        self.assertEqual(output.factor.value, Decimal("0.6"))
        self.assertIs(output.factor.source_kind, ParameterSourceKind.MEASURED)
        self.assertEqual(output.factor.source_id, "USER-EXPORTED-ELECTRICITY-SOURCE")
        self.assertEqual(output.factor.source_version, "user-input")
        self.assertEqual(output.factor.source_location, "企业实测/检测资料编号：LAB-OUT-01")

    def test_search_completers_use_case_insensitive_contains(self) -> None:
        fuel = self.page._fuel_rows[0].fuel_type.completer()
        enterprise = self.page.enterprise_name.completer()
        for completer in (fuel, enterprise):
            self.assertEqual(completer.caseSensitivity(), Qt.CaseSensitivity.CaseInsensitive)
            self.assertEqual(completer.filterMode(), Qt.MatchFlag.MatchContains)


if __name__ == "__main__":
    unittest.main()
