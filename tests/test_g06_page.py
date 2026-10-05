from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
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
    FGDInput,
    HeatFactorMode,
    FuelPath,
    FuelType,
    MaterialBasis,
    MaterialComponentKind,
    EmissionSourceStatus,
    InMemoryRecordRepository,
    ParameterSourceKind,
    SteamKind,
)
from packages.standards.carbon_material_normalization import MaterialDataSource, MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.carbon_material_page import _C2_CARBONATES, _FUEL_C1_ACTIVITY_PATH, _FUEL_C1_SUBJECT_IDS
from packages.ui.field_specs import get_field_spec
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import tree_texts


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
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.catalog_service,
            record_repository=InMemoryRecordRepository(),
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

    def test_c1_specific_fuels_resolve_canonical_defaults_through_supported_paths(self) -> None:
        row = self.page._fuel_rows[0]
        self.assertEqual(row.lower_heating_value.property("fieldSpecKey"), "fuel_lhv")
        self.assertEqual(len(_FUEL_C1_SUBJECT_IDS), 26)
        for fuel_type, subject_id in _FUEL_C1_SUBJECT_IDS.items():
            with self.subTest(fuel_type=fuel_type):
                row.activity.clear()
                row.fuel_type.setCurrentIndex(row.fuel_type.findData(fuel_type))
                expected_path = _FUEL_C1_ACTIVITY_PATH.get(fuel_type, FuelPath.MASS)
                self.assertIs(FuelPath(row.path.currentData()), expected_path)
                row.activity.setText("1")
                fuel = self.page._fuel()[0]
                self.assertIs(fuel.path, expected_path)
                self.assertIs(fuel.carbon_content.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
                self.assertIs(fuel.oxidation_rate.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
                self.assertEqual(fuel.carbon_content.parameter_id, f"{subject_id}_carbon_content")
                self.assertEqual(fuel.oxidation_rate.parameter_id, f"{subject_id}_oxidation_rate")
                self.assertEqual(fuel.carbon_content.source_id, "SRC-32151-34-2024")
                self.assertEqual(fuel.oxidation_rate.source_id, "SRC-32151-34-2024")
                if expected_path is FuelPath.HEAT:
                    self.assertIsNone(fuel.lower_heating_value)
                else:
                    self.assertIsNotNone(fuel.lower_heating_value)
                    self.assertEqual(fuel.lower_heating_value.parameter_id, f"{subject_id}_lhv")
                    self.assertIs(fuel.lower_heating_value.source_kind, ParameterSourceKind.STANDARD_DEFAULT)

                row.path.setCurrentIndex(row.path.findData(FuelPath.HEAT))
                heat_fuel = self.page._fuel()[0]
                self.assertIs(heat_fuel.path, FuelPath.HEAT)
                self.assertIsNone(heat_fuel.lower_heating_value)
                self.assertEqual(heat_fuel.carbon_content.parameter_id, f"{subject_id}_carbon_content")
                self.assertIs(heat_fuel.carbon_content.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
                row.activity.clear()

        row.activity.clear()
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.COAL))
        self.assertIsNone(self.page._fuel_default_factors(row))
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.OTHER))
        self.assertIsNone(self.page._fuel_default_factors(row))

    def test_custom_fuel_requires_named_measured_parameters_and_source(self) -> None:
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-FUEL-001")
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.OTHER))
        row.custom_name.setText("工艺回收混合燃料")
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.activity.setText("1")
        self.page._run_calculation()
        missing = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("单位含碳量", missing)
        self.assertIn("碳氧化率", missing)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

        row.carbon.setText("0.02")
        row.oxidation.setText("98")
        row.source_reference.setText("燃料检测报告-UAT-01")
        for combo in (row.carbon_source, row.oxidation_source):
            combo.setCurrentIndex(combo.findData("MEASURED"))
        self.page._run_calculation()
        self.assertFalse(self.page.result_card.isHidden(), tree_texts(self.page.validation_list))
        self.assertEqual(self.page._fuel()[0].fuel_label, "工艺回收混合燃料")
        saved = self.page.calculator.record_repository.list_all()
        self.assertEqual(len(saved), 1)

    def test_blank_fuel_activity_is_distinct_from_explicit_zero(self) -> None:
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.DIESEL))
        row.activity.clear()
        blank = self.page._fuel()[0].activity
        self.assertIsNone(blank)
        row.activity.setText("0")
        zero = self.page._fuel()[0].activity
        self.assertEqual(zero.value, Decimal("0"))

    def test_fgd_ui_uses_each_c2_carbonate_factor_and_blocks_unknown_legacy_input(self) -> None:
        self.page.enterprise_name.setText("碳酸盐UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-FGD-001")
        self.page._fields["fgd.cal"].setText("10")
        expected = {
            "car-par-c2-caco3": "0.440",
            "car-par-c2-mgco3": "0.522",
            "car-par-c2-na2co3": "0.415",
            "car-par-c2-nahco3": "0.524",
            "car-par-c2-feco3": "0.380",
            "car-par-c2-mnco3": "0.383",
            "car-par-c2-baco3": "0.223",
            "car-par-c2-li2co3": "0.595",
            "car-par-c2-k2co3": "0.318",
            "car-par-c2-srco3": "0.298",
            "car-par-c2-camgco3-2": "0.477",
        }
        self.assertEqual({parameter_id for _, parameter_id in _C2_CARBONATES}, set(expected))
        for parameter_id, expected_factor in expected.items():
            with self.subTest(carbonate=parameter_id):
                selector = self.page._carbonate_type_selector
                selector.setCurrentIndex(selector.findData(parameter_id))
                fgd = self.page._process("fgd", FGDInput)
                self.assertIsNotNone(fgd)
                assert fgd is not None
                factor = fgd.components[0].emission_factor
                self.assertIsNotNone(factor)
                assert factor is not None
                self.assertEqual(factor.parameter_id, parameter_id)
                self.assertEqual(str(factor.value), expected_factor)
                self.assertIs(factor.source_kind, ParameterSourceKind.STANDARD_SPECIFIED)
                self.assertEqual(factor.source_id, "SRC-32151-34-2024")

        selector = self.page._carbonate_type_selector
        selector.setCurrentIndex(0)
        legacy_fgd = self.page._process("fgd", FGDInput)
        self.assertIsNotNone(legacy_fgd)
        assert legacy_fgd is not None
        self.assertIsNone(legacy_fgd.components[0].emission_factor)
        outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-CARBONATE-FACTOR-MISSING" for problem in outcome.problems))
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

        self.page._fields["fgd.ef1"].setText("0.500")
        self.page._fields["fgd.factor_source_reference"].setText("脱硫剂检测报告-UI-01")
        measured = self.page._process("fgd", FGDInput)
        self.assertIsNotNone(measured)
        assert measured is not None
        factor = measured.components[0].emission_factor
        self.assertIsNotNone(factor)
        assert factor is not None
        self.assertIs(factor.source_kind, ParameterSourceKind.MEASURED)
        self.assertEqual(factor.source_id, "USER-FGD-SOURCE")
        self.assertIn("脱硫剂检测报告-UI-01", factor.source_location)
        measured_outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(measured_outcome.successful, measured_outcome.problems)
        measured_snapshot = next(
            snapshot for snapshot in measured_outcome.parameter_snapshots
            if snapshot.parameter_id == "fgd_carbonate_emission_factor_measured"
        )
        self.assertEqual(measured_snapshot.source_id, "USER-FGD-SOURCE")
        self.assertIn("脱硫剂检测报告-UI-01", measured_snapshot.source_location)

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

    def test_process_instances_keep_identity_and_ui_domain_results_match(self) -> None:
        self.page.enterprise_name.setText("多工序UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        values = {
            "gc": "100", "wfc": "0.008", "cc": "70", "ucc": "5", "du": "1",
            "wfc_c": "0.002", "wvar": "0.10", "wvar_c": "0.02",
        }
        first = self.page._process_rows["calcination"][0]
        for key, value in values.items():
            first["fields"][key].setText(value)
        self.page._add_process_row("calcination")
        second = self.page._process_rows["calcination"][1]
        second_values = {**values, "gc": "240", "wfc": "0.015", "cc": "110", "ucc": "2"}
        for key, value in second_values.items():
            second["fields"][key].setText(value)
        input_value = self.page._input()
        self.assertEqual(len(input_value.calcinations), 2)
        first_id, second_id = (item.instance_id for item in input_value.calcinations)
        direct = self.page.calculator.calculate(input_value)
        self.assertTrue(direct.successful, direct.problems)
        self.assertEqual(
            {line.line_id for line in direct.result.lines if line.emission_source_id == "CAR-SRC-CALCINATION-001"},
            {f"CAR-FLD-P01-RESULT.{first_id}", f"CAR-FLD-P01-RESULT.{second_id}"},
        )
        reordered = replace(input_value, calcinations=tuple(reversed(input_value.calcinations)))
        reversed_result = self.page.calculator.calculate(reordered)
        self.assertEqual(direct.result.total_amount, reversed_result.result.total_amount)
        self.assertEqual(
            self.page._fingerprint_business_input(input_value),
            self.page._fingerprint_business_input(reordered),
        )
        before_delete = [str(row["instance_id"]) for row in self.page._process_rows["calcination"]]
        third = self.page._add_process_row("calcination")
        third_id = str(third["instance_id"])
        self.page._remove_process_row("calcination", second_id)
        self.assertEqual([str(row["instance_id"]) for row in self.page._process_rows["calcination"]], [before_delete[0], third_id])
        self.assertEqual(self.page._process_rows["calcination"][1]["title"].text(), "煅烧 2")
        self.assertNotIn(third_id, "\n".join(label.text() for label in self.page.findChildren(QLabel)))
        saved_state = self.page._capture_form_state()
        self.page._restore_form_state(saved_state)
        self.assertEqual(
            [str(row["instance_id"]) for row in self.page._process_rows["calcination"]],
            [before_delete[0], third_id],
        )

    def test_process_validation_names_the_invalid_instance_in_business_language(self) -> None:
        self.page.enterprise_name.setText("实例错误定位企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-GRAPHITIZATION-001")
        rows = self.page._process_rows["graphitization"]
        for index in range(2):
            row = rows[0] if index == 0 else self.page._add_process_row("graphitization")
            for field in ("gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar"):
                row["fields"][field].setText("0")
        invalid_row = self.page._add_process_row("graphitization")
        invalid_row["fields"]["gpm"].setText("1")
        instance_id = str(invalid_row["instance_id"])

        self.page._run_calculation()

        messages = tree_texts(self.page.validation_list)
        self.assertIn("石墨化过程 3", messages)
        self.assertTrue(any("固定碳" in message and "必填信息不完整" in message for message in messages), messages)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())
        self.assertNotIn(instance_id, "\n".join(messages))

    def test_one_calculation_collects_issues_from_multiple_source_cards(self) -> None:
        self.page.enterprise_name.setText("多排放源错误汇总企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        self._set_source_involved("CAR-SRC-GRAPHITIZATION-001")
        self.page._fields["calcination.gc"].setText("10")
        self.page._fields["graphitization.gpm"].setText("1")

        self.page.calculate_button.click()
        self.application.processEvents()

        messages = tree_texts(self.page.validation_list)
        joined = "\n".join(messages)
        self.assertTrue(any(text.startswith("必须修正（") for text in messages), messages)
        self.assertIn("煅烧过程 1", messages)
        self.assertIn("石墨化过程 1", messages)
        self.assertIn("煅烧", joined)
        self.assertIn("石墨化", joined)
        self.assertGreater(sum("必填信息不完整" in text for text in messages), 2)
        self.assertNotIn("CAR-VAL-", joined)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.calculator.record_repository.list_all(), ())

    def test_new_accounting_reset_removes_secondary_business_rows(self) -> None:
        for prefix in ("calcination", "baking", "graphitization", "fume", "fgd"):
            self.page._add_process_row(prefix)
        self.page._add_fgd_component(self.page._process_rows["fgd"][0])
        self.page._add_heat_row("heat")
        self.page._add_heat_row("exported_heat")
        self.page._add_output_electricity_row(line_id="exported-electricity-second")
        for prefix, rows in self.page._process_rows.items():
            for row in rows[1:]:
                fields = row.get("fields", {})
                if fields:
                    next(iter(fields.values())).setText("123")
        self.page._heat_rows["heat"][1]["amount"].setText("123")
        self.page._heat_rows["exported_heat"][1]["amount"].setText("456")
        self.page._output_electricity_rows[1]["amount"].setText("789")

        self.page._reset_for_new_accounting()

        self.assertTrue(all(len(rows) == 1 for rows in self.page._process_rows.values()))
        self.assertEqual(len(self.page._process_rows["fgd"][0]["components"]), 1)
        self.assertEqual(len(self.page._heat_rows["heat"]), 1)
        self.assertEqual(len(self.page._heat_rows["exported_heat"]), 1)
        self.assertEqual(len(self.page._output_electricity_rows), 1)
        self.assertEqual(self.page._fields["heat_id"].text(), "heat-1")
        self.assertEqual(self.page._fields["exported_heat_id"].text(), "exported-heat-1")
        self.assertEqual(self.page._output_electricity_rows[0]["id"].text(), "exported-electricity-1")
        self.assertEqual(self.page._heat_rows["heat"][0]["amount"].text(), "")
        self.assertEqual(self.page._heat_rows["exported_heat"][0]["amount"].text(), "")
        self.assertEqual(self.page._output_electricity_rows[0]["amount"].text(), "")
        self.assertFalse(any(
            row.get("flags", {}).get("carbon_output_included_in_input", None).isChecked()
            for prefix in ("calcination", "baking")
            for row in self.page._process_rows[prefix]
        ))

    def test_energy_line_ids_survive_middle_deletion_and_form_state_restore(self) -> None:
        self.page._heat_rows["heat"][0]["amount"].setText("10")
        second_heat = self.page._add_heat_row("heat")
        second_heat["amount"].setText("20")
        third_heat = self.page._add_heat_row("heat")
        third_heat["amount"].setText("30")
        for row in self.page._heat_rows["heat"]:
            row["measured"].setText("0.11")
            row["source"].setText("多来源身份测试报告")
        self.page._remove_heat_row("heat", second_heat["widget"])

        self.page._output_electricity_rows[0]["amount"].setText("1")
        second_power = self.page._add_output_electricity_row()
        second_power["amount"].setText("2")
        third_power = self.page._add_output_electricity_row()
        third_power["amount"].setText("3")
        self.page._remove_output_electricity_row(second_power["widget"])

        state = self.page._capture_form_state()
        self.assertEqual(state["heat_line_ids"]["heat"], ["heat-1", "heat-3"])
        self.assertEqual(state["exported_electricity_line_ids"], ["exported-electricity-1", "exported-electricity-3"])
        self.assertEqual([line.line_id for line in self.page._heat("heat")], ["heat-1", "heat-3"])
        self.assertEqual([line.line_id for line in self.page._exported_electricity()], ["exported-electricity-1", "exported-electricity-3"])

        self.page._restore_form_state(state)
        self.assertEqual([line.line_id for line in self.page._heat("heat")], ["heat-1", "heat-3"])
        self.assertEqual([line.line_id for line in self.page._exported_electricity()], ["exported-electricity-1", "exported-electricity-3"])
        next_heat = self.page._add_heat_row("heat")
        next_power = self.page._add_output_electricity_row()
        self.assertEqual(next_heat["default_line_id"], "heat-4")
        self.assertEqual(next_power["default_line_id"], "exported-electricity-4")

        fresh_window = create_main_window(
            AppConfig(catalog_database=self.catalog_path),
            catalog_service=self.catalog_service,
            record_repository=InMemoryRecordRepository(),
        )
        fresh_window.show()
        try:
            self.application.processEvents()
            fresh_shell = fresh_window.centralWidget()
            self.assertIsInstance(fresh_shell, AppShell)
            assert isinstance(fresh_shell, AppShell)
            fresh_page = fresh_shell.pages[AppRoute.NEW_ACCOUNTING]
            self.assertIsInstance(fresh_page, CarbonMaterialAccountingPage)
            assert isinstance(fresh_page, CarbonMaterialAccountingPage)
            fresh_page._restore_form_state(state)
            self.assertEqual([row["default_line_id"] for row in fresh_page._heat_rows["heat"]], ["heat-1", "heat-3"])
            self.assertEqual([row["default_line_id"] for row in fresh_page._output_electricity_rows], ["exported-electricity-1", "exported-electricity-3"])
            self.assertEqual(fresh_page._add_heat_row("heat")["default_line_id"], "heat-4")
            self.assertEqual(fresh_page._add_output_electricity_row()["default_line_id"], "exported-electricity-4")
        finally:
            fresh_window.close()

    def test_fgd_ui_keeps_multiple_components_scoped_to_each_unit(self) -> None:
        self.page.enterprise_name.setText("多脱硫设施UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-FGD-001")
        first_unit = self.page._process_rows["fgd"][0]
        first_component, = first_unit["components"]
        first_component["cal"].setText("10")
        first_component["i"].setText("0.4")
        first_component["factor_source_reference"].setText("检测报告-1")
        first_component["carbonate_type"].setCurrentIndex(first_component["carbonate_type"].findData("car-par-c2-caco3"))
        second_component = self.page._add_fgd_component(first_unit)
        second_component["cal"].setText("2")
        second_component["i"].setText("0.4")
        second_component["factor_source_reference"].setText("检测报告-2")
        second_component["carbonate_type"].setCurrentIndex(second_component["carbonate_type"].findData("car-par-c2-mgco3"))
        self.page._add_process_row("fgd")
        second_unit = self.page._process_rows["fgd"][1]
        second_unit["components"][0]["cal"].setText("5")
        second_unit["components"][0]["carbonate_type"].setCurrentIndex(
            second_unit["components"][0]["carbonate_type"].findData("car-par-c2-na2co3")
        )
        input_value = self.page._input()
        self.assertEqual([len(unit.components) for unit in input_value.fgd_units], [2, 1])
        reordered_fgd = replace(
            input_value,
            fgd=None,
            fgd_units=tuple(
                replace(unit, components=tuple(reversed(unit.components)))
                for unit in reversed(input_value.fgd_units)
            ),
        )
        self.assertEqual(
            self.page._fingerprint_business_input(input_value),
            self.page._fingerprint_business_input(reordered_fgd),
        )
        outcome = self.page.calculator.calculate(input_value)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertTrue(any(line.line_id.endswith(input_value.fgd_units[0].instance_id) for line in outcome.result.lines))
        self.assertTrue(any(line.line_id.endswith(input_value.fgd_units[1].instance_id) for line in outcome.result.lines))

    def test_ui_builds_multiple_instances_for_every_process_source(self) -> None:
        self.page.enterprise_name.setText("全过程多实例企业")
        self.page.boundary_confirmed.setChecked(True)
        source_ids = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
            "fume": "CAR-SRC-FUME-INCINERATION-001",
            "fgd": "CAR-SRC-FGD-001",
        }
        values_by_prefix = {
            "calcination": {
                "gc": "100", "wfc": "0.01", "cc": "30", "ucc": "4", "du": "1",
                "wfc_c": "0.002", "wvar": "0.10", "wvar_c": "0.02",
            },
            "baking": {
                "bpm": "10", "bpmfc": "0.5", "bg": "100", "bgfc": "0.7", "bwt": "0.05",
                "bp": "95", "bpfc": "0.6", "bpmvar": "10", "bgvar": "2",
            },
            "graphitization": {
                "gpm": "10", "gpmfc": "0.5", "gta": "100", "gtafc": "0.7", "gwt": "0.05",
                "gp": "95", "gpfc": "0.6", "gpmvar": "10",
            },
            "fume": {"q": "1000", "qvar": "10", "hm": "30", "fch": "0.02", "fox": "0.98", "duration": "1"},
        }
        for prefix, source_id in source_ids.items():
            self._set_source_involved(source_id)
            first = self.page._process_rows[prefix][0]
            if prefix == "fgd":
                component = first["components"][0]
                component["cal"].setText("10")
                component["i"].setText("45")
                component["factor_source_reference"].setText("脱硫剂检测报告-A")
                component["carbonate_type"].setCurrentIndex(component["carbonate_type"].findData("car-par-c2-caco3"))
                self.page._add_fgd_component(first)
                component = first["components"][1]
                component["cal"].setText("2")
                component["i"].setText("45")
                component["factor_source_reference"].setText("脱硫剂检测报告-A")
                component["carbonate_type"].setCurrentIndex(component["carbonate_type"].findData("car-par-c2-mgco3"))
                second = self.page._add_process_row(prefix)
                second_component = second["components"][0]
                second_component["cal"].setText("5")
                second_component["i"].setText("90")
                second_component["factor_source_reference"].setText("脱硫剂检测报告-B")
                second_component["carbonate_type"].setCurrentIndex(
                    second_component["carbonate_type"].findData("car-par-c2-na2co3")
                )
                continue
            for key, value in values_by_prefix[prefix].items():
                first["fields"][key].setText(value)
            second = self.page._add_process_row(prefix)
            for key, value in values_by_prefix[prefix].items():
                second["fields"][key].setText(value)
            if prefix == "baking":
                for key, value in {
                    "bpm": "25", "bpmfc": "1.2", "bg": "150", "bgfc": "1", "bwt": "0.02",
                    "bp": "110", "bpfc": "0.9", "bpmvar": "8", "bgvar": "3",
                }.items():
                    second["fields"][key].setText(value)
            elif prefix == "graphitization":
                for key, value in {
                    "gpm": "20", "gpmfc": "1.2", "gta": "140", "gtafc": "1", "gwt": "0.02",
                    "gp": "115", "gpfc": "0.8", "gpmvar": "8",
                }.items():
                    second["fields"][key].setText(value)
            else:
                first_field = next(iter(values_by_prefix[prefix]))
                second["fields"][first_field].setText(str(Decimal(values_by_prefix[prefix][first_field]) * 2))

        domain_input = self.page._input()
        process_tuples = {
            "calcination": domain_input.calcinations,
            "baking": domain_input.bakings,
            "graphitization": domain_input.graphitizations,
            "fume": domain_input.fume_incinerations,
            "fgd": domain_input.fgd_units,
        }
        self.assertTrue(all(len(items) == 2 for items in process_tuples.values()))
        for prefix, items in process_tuples.items():
            self.assertEqual(len({item.instance_id for item in items}), 2, prefix)
            self.assertNotIn(items[0].instance_id, "\n".join(label.text() for label in self.page.findChildren(QLabel)))
        self.assertEqual(str(domain_input.calcinations[0].gc.value), "100")
        self.assertEqual(str(domain_input.calcinations[1].gc.value), "200")
        self.assertEqual(str(domain_input.bakings[0].bpm.value), "10")
        self.assertEqual(str(domain_input.bakings[1].bpm.value), "25")
        self.assertEqual(str(domain_input.graphitizations[0].gpm.value), "10")
        self.assertEqual(str(domain_input.graphitizations[1].gpm.value), "20")
        self.assertEqual(str(domain_input.fume_incinerations[0].q.value), "1000")
        self.assertEqual(str(domain_input.fume_incinerations[1].q.value), "2000")
        self.assertEqual(domain_input.fgd_units[0].components[0].emission_factor.parameter_id, "car-par-c2-caco3")
        self.assertEqual(domain_input.fgd_units[0].components[1].emission_factor.parameter_id, "car-par-c2-mgco3")
        self.assertEqual(domain_input.fgd_units[1].components[0].emission_factor.parameter_id, "car-par-c2-na2co3")
        for source_id in source_ids.values():
            self.assertTrue(any(state.source_id == source_id and state.status is EmissionSourceStatus.INVOLVED for state in domain_input.source_states))

        outcome = self.page.calculator.calculate(domain_input)
        self.assertTrue(outcome.successful, outcome.problems)
        expected_sources = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
            "fume_incineration": "CAR-SRC-FUME-INCINERATION-001",
            "fgd": "CAR-SRC-FGD-001",
        }
        for name, items in process_tuples.items():
            source_id = expected_sources["fume_incineration" if name == "fume" else name]
            rows = [line for line in outcome.result.lines if line.emission_source_id == source_id]
            self.assertEqual(len(rows), 2, name)
            self.assertEqual({line.line_id.rsplit(".", 1)[-1] for line in rows}, {item.instance_id for item in items})

    def test_heat_and_exported_power_rows_keep_factors_and_sources_independently(self) -> None:
        self.page.enterprise_name.setText("多能源来源UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-PURCHASED-HEAT-001")
        self._set_source_involved("CAR-SRC-EXPORTED-HEAT-001")
        self._set_source_involved("CAR-SRC-EXPORTED-ELECTRICITY-001")
        self.page._fields["heat_amount"].setText("100")
        self.page._fields["heat_enthalpy"].setText("2800")
        self.page._heat_rows["heat"][0]["enthalpy_mode"].setCurrentIndex(
            self.page._heat_rows["heat"][0]["enthalpy_mode"].findData("MANUAL")
        )
        self.page._heat_rows["heat"][0]["factor_mode"].setCurrentIndex(
            self.page._heat_rows["heat"][0]["factor_mode"].findData(HeatFactorMode.MEASURED)
        )
        self.page.heat_measured_factor.setText("0.11")
        self.page.heat_factor_source_reference.setText("购热报告-A")
        self.page._fields["exported_heat_amount"].setText("25")
        self.page._fields["exported_heat_enthalpy"].setText("2700")
        self.page._heat_rows["exported_heat"][0]["enthalpy_mode"].setCurrentIndex(
            self.page._heat_rows["exported_heat"][0]["enthalpy_mode"].findData("MANUAL")
        )
        self.page._heat_rows["exported_heat"][0]["factor_mode"].setCurrentIndex(
            self.page._heat_rows["exported_heat"][0]["factor_mode"].findData(HeatFactorMode.MEASURED)
        )
        self.page.exported_heat_measured_factor.setText("0.12")
        self.page.exported_heat_factor_source_reference.setText("售热报告-A")
        self.page._add_heat_row("heat")
        second_heat = self.page._heat_rows["heat"][1]
        second_heat["amount"].setText("200")
        second_heat["enthalpy"].setText("3000")
        second_heat["enthalpy_mode"].setCurrentIndex(second_heat["enthalpy_mode"].findData("MANUAL"))
        second_heat["factor_mode"].setCurrentIndex(second_heat["factor_mode"].findData(HeatFactorMode.MEASURED))
        second_heat["measured"].setText("0.20")
        second_heat["source"].setText("购热报告-B")
        self.page._add_heat_row("exported_heat")
        second_output_heat = self.page._heat_rows["exported_heat"][1]
        second_output_heat["amount"].setText("75")
        second_output_heat["enthalpy"].setText("2900")
        second_output_heat["enthalpy_mode"].setCurrentIndex(second_output_heat["enthalpy_mode"].findData("MANUAL"))
        second_output_heat["factor_mode"].setCurrentIndex(second_output_heat["factor_mode"].findData(HeatFactorMode.MEASURED))
        second_output_heat["measured"].setText("0.16")
        second_output_heat["source"].setText("售热报告-B")
        self.page._output_electricity_rows[0]["amount"].setText("10")
        self.page._output_electricity_rows[0]["measured"].setText("0.50")
        self.page._output_electricity_rows[0]["source"].setText("电力报告-A")
        self.page._add_output_electricity_row(line_id="exported-electricity-b")
        second_power = self.page._output_electricity_rows[1]
        second_power["amount"].setText("4")
        second_power["measured"].setText("0.25")
        second_power["source"].setText("电力报告-B")

        input_value = self.page._input()
        self.assertEqual([line.factor.value for line in input_value.purchased_heat], [Decimal("0.11"), Decimal("0.20")])
        self.assertEqual([line.factor.value for line in input_value.exported_heat], [Decimal("0.12"), Decimal("0.16")])
        self.assertEqual([line.factor.value for line in input_value.exported_electricity], [Decimal("0.50"), Decimal("0.25")])
        self.assertIn("purchased_heat", input_value.purchased_heat[0].factor.selection_reason)
        self.assertIn("exported_heat", input_value.exported_heat[0].factor.selection_reason)
        outcome = self.page.calculator.calculate(input_value)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertEqual(sum(1 for line in outcome.result.lines if line.emission_source_id == "CAR-SRC-EXPORTED-ELECTRICITY-001"), 2)

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
            self.assertIn("已确定", row.parameter_status.text())
            self.assertNotIn(factor_id, row.parameter_factor.text())
            self.assertIn("来源说明", row.parameter_source.text())
            self.assertNotIn("审核状态", row.parameter_source.text())
            self.assertTrue(row.parameter_reason.text().strip())
            self.assertFalse(row.professional_details.isVisible())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
        self.assertTrue(all(not row.professional_details.isVisible() for row in self.page._electricity_rows))

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
        cases = (
            ("calcination", "CAR-SRC-CALCINATION-001", "gc"),
            ("baking", "CAR-SRC-BAKING-001", "bpm"),
            ("graphitization", "CAR-SRC-GRAPHITIZATION-001", "gpm"),
        )
        for prefix, source_id, field in cases:
            self._set_source_involved(source_id)
            self.page._fields[f"{prefix}.{field}"].setText("10")
            controls = self.page._material_controls[prefix]
            for key in ("mass_basis", "composition_basis", "normalized_basis"):
                controls[key].setCurrentIndex(controls[key].findData(MaterialBasis.RECEIVED))
            controls["fixed_carbon_component_kind"].setCurrentIndex(
                controls["fixed_carbon_component_kind"].findData(MaterialComponentKind.VOLATILE_MATTER)
            )
            controls["volatile_matter_component_kind"].setCurrentIndex(
                controls["volatile_matter_component_kind"].findData(MaterialComponentKind.VOLATILE_MATTER)
            )
            outcome = self.page.calculator.calculate(self.page._input())
            self.assertTrue(any(
                problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
                and problem.field_id.startswith(f"{source_id}.")
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
                and problem.field_id.startswith(f"{source_id}.")
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
        self.page._source_statuses["CAR-SRC-EXPORTED-ELECTRICITY-001"].setCurrentIndex(1)
        self.page._source_statuses["CAR-SRC-EXPORTED-HEAT-001"].setCurrentIndex(1)
        self.page._fields["exported_electricity_amount"].setText("2")
        self.page._fields["exported_heat_amount"].setText("100")
        self.page._fields["exported_heat_enthalpy"].setText("2800")
        heat_row = self.page._heat_rows["exported_heat"][0]
        heat_row["enthalpy_mode"].setCurrentIndex(heat_row["enthalpy_mode"].findData("MANUAL"))
        value = self.page._input()
        self.assertEqual(len(value.exported_electricity), 1)
        self.assertEqual(value.exported_electricity[0].amount.value, 2)
        self.assertEqual(len(value.exported_heat), 1)
        self.assertEqual(value.exported_heat[0].amount.value, 100)
        self.assertEqual(value.exported_heat[0].amount.unit, "t")
        self.assertEqual(value.exported_heat[0].steam_amount_t.value, Decimal("100"))
        self.assertTrue(value.exported_heat[0].manual_enthalpy)
        self.assertEqual(value.exported_heat[0].factor_mode, HeatFactorMode.STANDARD_DEFAULT)

    def test_empty_enterprise_name_is_optional_and_successfully_creates_record(self) -> None:
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isHidden())
        records = self.page.calculator.record_repository.list_all()
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].input_snapshot.enterprise_name)
        self.assertEqual(self.page.validation_list.topLevelItemCount(), 0)

    def test_heat_defaults_to_canonical_factor_and_automatic_steam_enthalpy(self) -> None:
        row = self.page._heat_rows["heat"][0]
        factor_mode = row["factor_mode"]
        enthalpy_mode = row["enthalpy_mode"]
        self.assertEqual(row["amount"].property("fieldUnit"), "t")
        self.assertEqual(row["amount"].spec.domain_unit, "kg")
        self.assertEqual(get_field_spec("heat_pressure").label, "蒸汽压力（MPa，绝压）")
        self.assertEqual(factor_mode.currentData(), HeatFactorMode.STANDARD_DEFAULT)
        self.assertIn("0.11", factor_mode.currentText())
        self.assertEqual(enthalpy_mode.currentData(), "AUTO")
        self.assertFalse(self.page.heat_factor_selector.isVisible())
        self.assertFalse(self.page.heat_factor_metadata.isVisible())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))

        self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        self.page._source_statuses["CAR-SRC-EXPORTED-HEAT-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-EXPORTED-HEAT-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        row["amount"].setText("1")
        row["pressure"].setText("0.1")
        output_row = self.page._heat_rows["exported_heat"][0]
        output_row["amount"].setText("0.5")
        output_row["pressure"].setText("0.1")
        value = self.page._input()
        heat_input = value.purchased_heat[0]
        self.assertEqual(heat_input.amount.value, Decimal("1"))
        self.assertEqual(heat_input.amount.unit, "t")
        self.assertEqual(heat_input.steam_amount_t.value, Decimal("1"))
        self.assertFalse(heat_input.manual_enthalpy)
        self.assertEqual(heat_input.steam_kind, SteamKind.SATURATED)
        outcome = self.page.calculator.calculate(value)
        self.assertTrue(outcome.successful, outcome.problems)
        trace = next(item for item in outcome.traces if item.formula_id == "CAR-FML-PURCHASED-HEAT-001")
        provenance = dict(trace.provenance)
        self.assertEqual(provenance["enthalpy_source"], "标准表自动确定")
        self.assertEqual(provenance["table"], "C.4")
        self.assertEqual(provenance["heat_factor_source"], "标准缺省值")
        factor_snapshot = next(
            item for item in outcome.parameter_snapshots
            if item.parameter_id == "heat_emission_factor_default"
        )
        self.assertEqual(factor_snapshot.factor_id, "heat_default_2025")
        self.assertEqual(factor_snapshot.value_used, Decimal("0.11"))
        output_heat = value.exported_heat[0]
        self.assertEqual(output_heat.amount.value, Decimal("0.5"))
        self.assertEqual(output_heat.factor_mode, HeatFactorMode.STANDARD_DEFAULT)
        output_trace = next(item for item in outcome.traces if item.formula_id == "CAR-FML-EXPORTED-HEAT-001")
        self.assertEqual(dict(output_trace.provenance)["heat_factor_source"], "标准缺省值")
        self.assertEqual(dict(output_trace.provenance)["enthalpy_source"], "标准表自动确定")

    def test_process_material_rows_flow_through_shared_normalization(self) -> None:
        from packages.standards.carbon_material_normalization import normalize_material_inputs

        self.page.enterprise_name.setText("多物料输入企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        process_row = self.page._process_rows["calcination"][0]
        feed, = process_row["materials"]
        feed["name"].setText("原料甲")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("80")
        feed["volatile_matter"].setText("10")
        self.assertEqual(feed["fixed_carbon_source"].currentData(), MaterialDataSource.MEASURED)
        self.assertEqual(feed["volatile_matter_source"].currentData(), MaterialDataSource.MEASURED)

        second_feed = self.page._add_material_line(process_row)
        second_feed["name"].setText("原料乙")
        second_feed["mass"].setText("50")
        second_feed["fixed_carbon"].setText("60")
        second_feed["volatile_matter"].setText("20")
        product = self.page._add_material_line(process_row)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("120")
        product["fixed_carbon"].setText("90")
        product["volatile_matter"].setText("2")

        domain_input = self.page._input()
        payload = domain_input.calcinations[0]
        normalized = normalize_material_inputs("calcination", payload.material_rows, policy=self.page.calculator.policy)
        self.assertFalse(normalized.problems, normalized.problems)
        self.assertEqual(payload.gc.value, normalized.value("gc"))
        self.assertEqual(payload.wfc.value, normalized.value("wfc"))
        self.assertEqual(payload.cc.value, normalized.value("cc"))
        self.assertIn("原料 150 t", process_row["material_summary"].text())
        outcome = self.page.calculator.calculate(domain_input)
        self.assertTrue(outcome.successful, outcome.problems)
        trace = next(item for item in outcome.traces if item.formula_id == "CAR-FML-CALCINATION-001")
        provenance = set(trace.provenance)
        self.assertIn((f"material.{feed['line_id']}.name", "原料甲"), provenance)
        self.assertIn((f"material.{second_feed['line_id']}.name", "原料乙"), provenance)
        self.assertIn((f"material.{product['line_id']}.name", "煅后料"), provenance)

    def test_manual_steam_result_explains_used_and_reference_enthalpy(self) -> None:
        self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        row = self.page._heat_rows["heat"][0]
        row["amount"].setText("1")
        row["pressure"].setText("0.1")
        row["enthalpy"].setText("2810")
        row["enthalpy_mode"].setCurrentIndex(row["enthalpy_mode"].findData("MANUAL"))

        self.page._run_calculation()

        self.assertFalse(self.page.result_card.isHidden())
        explanation = self.page.result_line_details.text()
        self.assertIn("用户手动填写", explanation)
        self.assertIn("2810.0 kJ/kg", explanation)
        self.assertIn("参考值为 2675.7 kJ/kg", explanation)
        self.assertIn("本次采用您填写的 2810", explanation)

    def test_legacy_project_steam_kg_and_manual_enthalpy_restore_without_loss(self) -> None:
        legacy_state = self.page._capture_form_state()
        legacy_state.pop("steam_input_version", None)
        legacy_state["heat_amountInput"] = "1250"
        legacy_state["heat_enthalpyInput"] = "2780"
        legacy_state["heatFactorModeSelector"] = 0
        self.page._restore_form_state(legacy_state)
        row = self.page._heat_rows["heat"][0]
        self.assertEqual(row["amount"].text(), "1.25")
        self.assertEqual(row["enthalpy"].text(), "2780")
        self.assertEqual(row["enthalpy_mode"].currentData(), "MANUAL")
        self.assertEqual(row["factor_mode"].currentData(), HeatFactorMode.STANDARD_DEFAULT)

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
        self.assertIn("GB/T 32151.34—2024", self.page.standard_id_label.text())
        self.assertIn("炭素材料生产企业", self.page.standard_id_label.text())

    def test_calculation_renders_result_and_boundary_error_without_persistence(self) -> None:
        self.page.enterprise_name.setText("UI 测试企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertIn("温室气体排放总量：", self.page.result_total.text())
        self.assertIn("已形成 0 条参数快照", self.page.parameter_snapshot_summary.text())
        calculator_repository = self.page.calculator.record_repository
        self.assertEqual(len(calculator_repository.list_all()), 1)

        self.page.boundary_confirmed.setChecked(False)
        self.page.calculate_button.click()
        self.application.processEvents()
        validation_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("核算边界尚未确认", validation_text)
        self.assertNotIn("CAR-VAL-", validation_text)
        self.assertEqual(len(calculator_repository.list_all()), 1)


if __name__ == "__main__":
    unittest.main()
