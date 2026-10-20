from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
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
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    STANDARD_ID,
    FGDInput,
    HeatFactorMode,
    FuelPath,
    FuelType,
    MaterialBasis,
    MaterialComponentKind,
    MeasuredFactorEvidence,
    EmissionSourceStatus,
    ParameterSourceKind,
    SteamKind,
)
from packages.standards.carbon_material_normalization import MaterialDataSource, MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.carbon_material_page import _C2_CARBONATES
from packages.standards.carbon_material_input_policy import fuel_path_for_unit
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

    def test_page_exposes_g06_sections_and_v2_source_groups(self) -> None:
        self.assertEqual(self.page.standard_id, STANDARD_ID)
        self.assertEqual(len(self.page._source_statuses), 10)
        self.assertEqual(set(self.page._source_toggle_buttons), {
            "fuel", "calcination", "baking", "graphitization", "fume", "fgd", "electricity", "heat",
        })
        self.assertEqual(len(self.page._energy_family_rows["electricity"]), 1)
        self.assertEqual(len(self.page._energy_family_rows["heat"]), 1)
        for object_name in (
            "boundaryConfirmedCheckBox",
            "accountingStandardId",
            "sourceToggle_fuel",
            "sourceToggle_calcination",
            "sourceToggle_baking",
            "sourceToggle_graphitization",
            "sourceToggle_fume",
            "sourceToggle_fgd",
            "sourceToggle_electricity",
            "sourceToggle_heat",
            "addUnifiedElectricityRow",
            "addUnifiedHeatRow",
            "calculateAccountingButton",
            "calculationTrace",
            "calculationTotal",
            "calculationValidationList",
        ):
            self.assertIsNotNone(self.page.findChild(QWidget, object_name), object_name)

    def test_quick_jump_matches_eight_source_groups_and_material_roles_are_preopened(self) -> None:
        self.assertEqual(self.page._fuel_rows[0].fuel_type_label.text(), "燃料种类")
        self.assertEqual(self.page.source_navigation.count(), 9)
        self.assertEqual(
            [self.page.source_navigation.itemText(index) for index in range(1, 9)],
            [label for _group_id, label, _source_ids in self.page._source_toggle_groups],
        )
        self.assertEqual(
            [self.page._source_toggle_buttons[group_id].accessibleName()
             for group_id, _label, _source_ids in self.page._source_toggle_groups],
            [label for _group_id, label, _source_ids in self.page._source_toggle_groups],
        )
        expected = {
            "calcination": ["原料", "煅后料", "欠煅烧料", "碳粉尘"],
            "baking": ["填充料", "待焙烧（炭化）品", "焙烧（炭化）品", "粉尘", "碎屑", "副产品"],
            "graphitization": ["保温料", "电阻料", "待石墨化品", "石墨化品", "粉尘", "碎屑", "残块", "副产品"],
        }
        expected_roles = {
            "calcination": [
                MaterialRole.CALCINATION_FEED, MaterialRole.CALCINED_PRODUCT,
                MaterialRole.UNDERBURN_RECOVERED, MaterialRole.CARBON_DUST,
            ],
            "baking": [
                MaterialRole.BAKING_FILLER, MaterialRole.GREEN_BAKING_PRODUCT,
                MaterialRole.BAKED_PRODUCT, MaterialRole.BAKING_BYPRODUCT,
                MaterialRole.BAKING_BYPRODUCT, MaterialRole.BAKING_BYPRODUCT,
            ],
            "graphitization": [
                MaterialRole.GRAPHITIZATION_PACKING, MaterialRole.GRAPHITIZATION_PACKING,
                MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, MaterialRole.GRAPHITIZED_PRODUCT,
                MaterialRole.GRAPHITIZATION_BYPRODUCT, MaterialRole.GRAPHITIZATION_BYPRODUCT,
                MaterialRole.GRAPHITIZATION_BYPRODUCT, MaterialRole.GRAPHITIZATION_BYPRODUCT,
            ],
        }
        source_ids = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
        }
        for prefix, labels in expected.items():
            with self.subTest(prefix=prefix):
                self._set_source_involved(source_ids[prefix])
                process = self.page._process_rows[prefix][0]
                materials = process["materials"]
                self.assertEqual([line["role"].currentText() for line in materials], labels)
                self.assertEqual(
                    [line["role"].currentData() for line in materials],
                    expected_roles[prefix],
                )
                self.assertTrue(all(not line["remove_button"].isHidden() for line in materials))
                self.assertEqual(self.page._material_inputs(process), ())

        self.assertEqual(len(expected["calcination"]), 4)
        self.assertEqual(len(expected["baking"]), 6)
        self.assertEqual(len(expected["graphitization"]), 8)
        self.assertEqual(
            [self.page._process_rows["baking"][0]["materials"][i]["role"].itemText(i)
             for i in range(4)],
            ["填充料", "待焙烧/炭化品", "焙烧/炭化产品", "粉尘/碎屑/副产品"],
        )
        self.assertEqual(
            [self.page._process_rows["graphitization"][0]["materials"][i]["role"].itemText(i)
             for i in range(4)],
            ["保温料/电阻料", "待石墨化品", "石墨化产品", "粉尘/碎屑/残块/副产品"],
        )

        calcination = self.page._process_rows["calcination"][0]
        for material in tuple(calcination["materials"]):
            self.page._remove_material_line(calcination, material["line_id"])
        self.assertEqual(calcination["materials"], [])
        saved = self.page._capture_form_state()
        saved_rows = saved["process_instances"]["calcination"]
        self.assertEqual(saved_rows[0]["material_ids"], [])
        self.page._restore_form_state(saved)
        self.assertEqual(self.page._process_rows["calcination"][0]["materials"], [])

    def test_typing_does_not_relayout_the_active_source_or_input(self) -> None:
        source_id = "CAR-SRC-FUEL-001"
        self._set_source_involved(source_id)
        row = self.page._fuel_rows[0]
        row.activity.setText("1")
        for _ in range(3):
            self.application.processEvents()
        card = self.page._source_cards[source_id]
        field_geometry = row.activity.geometry()
        card_geometry = card.geometry()
        scroll_value = self.shell.main_scroll_area.verticalScrollBar().value()

        row.activity.setText("12")
        for _ in range(3):
            self.application.processEvents()

        self.assertEqual(row.activity.geometry(), field_geometry)
        self.assertEqual(card.geometry(), card_geometry)
        self.assertEqual(self.shell.main_scroll_area.verticalScrollBar().value(), scroll_value)

    def test_c1_specific_fuels_resolve_canonical_defaults_through_supported_paths(self) -> None:
        row = self.page._fuel_rows[0]
        self.assertEqual(row.lower_heating_value.property("fieldSpecKey"), "fuel_lhv")
        options = row._fuel_options
        self.assertEqual(len(options), 26)
        heat_index = row.path.findData(FuelPath.HEAT)
        self.assertGreaterEqual(heat_index, 0)
        self.assertFalse(row.path.model().item(heat_index).isEnabled())
        self.assertTrue(row.path.view().isRowHidden(heat_index))
        self.assertEqual(
            {row.path.itemData(index) for index in range(row.path.count()) if not row.path.view().isRowHidden(index)},
            {FuelPath.MASS, FuelPath.VOLUME},
        )
        for option in options:
            fuel_type, subject_id = option.fuel_type, option.subject_id
            with self.subTest(fuel_type=fuel_type):
                row.activity.clear()
                row.fuel_type.setCurrentIndex(row.fuel_type.findData(fuel_type))
                defaults = self.page._uat03_parameter_queries.fuel_defaults(subject_id, self.page._period())
                expected_path = FuelPath(fuel_path_for_unit(defaults.lower_heating_value.factor.unit.removeprefix("GJ/")))
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
                self.assertIsNotNone(fuel.lower_heating_value)
                assert fuel.lower_heating_value is not None
                self.assertEqual(fuel.lower_heating_value.parameter_id, f"{subject_id}_lhv")
                self.assertIs(fuel.lower_heating_value.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
                row.activity.clear()

        row.activity.clear()
        self.assertEqual(row.fuel_type.findData(FuelType.COAL), -1)
        self.assertEqual(row.fuel_type.findData(FuelType.OTHER), -1)
        row.fuel_type.setEditText("未登记具体种类的企业燃料")
        row.fuel_type.confirm_name(force=True)
        self.assertIsNone(self.page._fuel_default_factors(row))
    def test_custom_fuel_requires_named_measured_parameters_and_source(self) -> None:
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-FUEL-001")
        row = self.page._fuel_rows[0]
        row.fuel_type.setEditText("工艺回收混合燃料")
        row.fuel_type.confirm_name(force=True)
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
        row.activity.setText("1")
        self.page._run_calculation()
        missing = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("单位含碳量", missing)
        self.assertIn("碳氧化率", missing)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.record_repository.list_all(), ())

        row.carbon_direct.setText("0.02")
        row.direct_carbon_source.setCurrentIndex(row.direct_carbon_source.findData("MEASURED"))
        row.oxidation.setText("98")
        row.oxidation_source.setCurrentIndex(row.oxidation_source.findData("MEASURED"))
        self.assertFalse(row.source_reference_control.isHidden())
        row.source_reference.setText("燃料检测报告-UAT-01")
        self.page._run_calculation()
        self.assertFalse(self.page.result_card.isHidden(), tree_texts(self.page.validation_list))
        self.assertEqual(self.page._fuel()[0].fuel_label, "工艺回收混合燃料")
        self.assertIs(self.page._fuel()[0].oxidation_rate.source_kind, ParameterSourceKind.MEASURED)
        saved = self.page.record_repository.list_all()
        self.assertEqual(len(saved), 1)
        raw_snapshot = self.page.record_repository.get_raw_input_snapshot(saved[0].record_id)
        reporting_snapshot = self.page.record_repository.get_reporting_snapshot(saved[0].record_id)
        assert raw_snapshot is not None and reporting_snapshot is not None
        frozen_fuel = raw_snapshot["fuel_inputs"][0]
        evidence_id = frozen_fuel["oxidation_rate"]["evidence_ref_ids"][0]
        self.assertEqual(frozen_fuel["oxidation_rate"]["source_kind"], "MEASURED")
        factor_evidence = next(
            item for item in reporting_snapshot["measured_factor_evidence"]
            if item["evidence_id"] == evidence_id
        )
        self.assertEqual(factor_evidence["source_reference"], "燃料检测报告-UAT-01")
        self.assertIn("碳氧化率", factor_evidence["applies_to"])

    def test_measured_oxidation_evidence_is_scoped_to_each_fuel(self) -> None:
        self._set_source_involved("CAR-SRC-FUEL-001")
        self.page._add_fuel_row()
        rows = self.page._fuel_rows
        for row, fuel_type, value, reference in (
            (rows[0], FuelType.DIESEL, "98", "柴油检测报告第2页"),
            (rows[1], FuelType.NATURAL_GAS, "99", "天然气检测报告第5页"),
        ):
            row.fuel_type.setCurrentIndex(row.fuel_type.findData(fuel_type))
            row.activity.setText("1")
            row.oxidation_source.setCurrentIndex(row.oxidation_source.findData("MEASURED"))
            row.oxidation.setText(value)
            row.source_reference.setText(reference)

        input_value = self.page._input()
        shared_evidence = MeasuredFactorEvidence(
            "evidence.factor.shared", "本次燃料实测因子", ("CAR-SRC-FUEL-001",),
            source_reference="企业共用检测台账", reason="用户标记的燃料因子共用证据。",
        )
        input_value = replace(
            input_value,
            reporting_data=replace(
                input_value.reporting_data,
                measured_factor_evidence=(*input_value.reporting_data.measured_factor_evidence, shared_evidence),
            ),
        )
        fuels = input_value.fuel_inputs
        self.assertEqual(len(fuels), 2)
        by_id = {item.evidence_id: item for item in input_value.reporting_data.measured_factor_evidence}
        expected_ids = tuple(
            f"evidence.factor.{row.internal_id.text().strip()}.oxidation"
            for row in rows
        )
        self.assertEqual(
            tuple(item.oxidation_rate.evidence_ref_ids for item in fuels),
            tuple((item,) for item in expected_ids),
        )
        self.assertEqual(set(by_id), {*expected_ids, "evidence.factor.shared"})
        self.assertTrue(all("evidence.factor.shared" not in item.oxidation_rate.evidence_ref_ids for item in fuels))
        self.assertEqual(
            tuple(by_id[item].source_reference for item in expected_ids),
            ("柴油检测报告第2页", "天然气检测报告第5页"),
        )
        self.assertTrue(all(not by_id[item].source_ids for item in expected_ids))
        self.assertTrue(all(item.oxidation_rate.source_kind is ParameterSourceKind.MEASURED for item in fuels))

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
        fgd_unit = self.page._process_rows["fgd"][0]
        fgd_unit["reagent_name"].setText("石灰石")
        fgd_unit["group_amount"].setText("10")
        component = fgd_unit["components"][0]
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
        component = self.page._process_rows["fgd"][0]["components"][0]
        options = {option.factor.parameter_id: option for option in self.page._carbonate_options()}
        for parameter_id, expected_factor in expected.items():
            with self.subTest(carbonate=parameter_id):
                self._select_carbonate(component, parameter_id)
                selector = component["carbonate_type"]
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
                option = selector.currentData()
                self.assertEqual(option.factor, options[parameter_id].factor)
                self.assertEqual(option.factor.parameter_id, parameter_id)
                self.assertEqual(option.factor.source_id, "SRC-32151-34-2024")

        selector = component["carbonate_type"]
        selector.setEditText("未登记碳酸盐")
        selector.confirm_name(force=True)
        legacy_fgd = self.page._process("fgd", FGDInput)
        self.assertIsNotNone(legacy_fgd)
        assert legacy_fgd is not None
        self.assertIsNone(legacy_fgd.components[0].emission_factor)
        outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-CARBONATE-FACTOR-MISSING" for problem in outcome.problems))
        self.assertEqual(self.page.record_repository.list_all(), ())

        component["ef1_source"].setCurrentIndex(component["ef1_source"].findData("MEASURED"))
        component["ef1"].setText("0.500")
        component["factor_source_reference"].setText("脱硫剂检测报告-UI-01")
        manual = self.page._process("fgd", FGDInput)
        self.assertIsNotNone(manual)
        assert manual is not None
        factor = manual.components[0].emission_factor
        self.assertIsNotNone(factor)
        assert factor is not None
        self.assertIs(factor.source_kind, ParameterSourceKind.MEASURED)
        self.assertIsNone(factor.source_id)
        self.assertNotIn("化学计算", factor.source_location)
        self.assertIn("脱硫剂检测报告-UI-01", factor.source_location)
        component["i_source"].setCurrentIndex(component["i_source"].findData("MEASURED"))
        component["i"].setText("90")
        component["tr_source"].setCurrentIndex(component["tr_source"].findData("MEASURED"))
        component["tr"].setText("100")
        manual_outcome = self.page.calculator.calculate(self.page._input())
        self.assertTrue(manual_outcome.successful, manual_outcome.problems)
        manual_snapshot = next(
            snapshot for snapshot in manual_outcome.parameter_snapshots
            if snapshot.parameter_id == "fgd_carbonate_emission_factor_user"
        )
        self.assertIsNone(manual_snapshot.source_id)
        self.assertIn("脱硫剂检测报告-UI-01", manual_snapshot.source_location)
    def test_electricity_direction_and_attribute_are_independent(self) -> None:
        rows = self.page._energy_family_rows["electricity"]
        self.page._add_unified_energy_row(kind="purchased_electricity", line_id="electricity-detail-2")
        self.page._add_unified_energy_row(kind="purchased_electricity", line_id="electricity-detail-3")
        values = (
            ("electricity-detail-1", "10", ElectricityAttribute.ORDINARY),
            ("electricity-detail-2", "20", ElectricityAttribute.NONFOSSIL),
            ("electricity-detail-3", "30", "SELF_CONSUMED_EXCLUDED"),
        )
        for row, (line_id, amount, attribute) in zip(rows, values):
            row.line_id.setText(line_id)
            row.amount.setText(amount)
            row.attribute.setCurrentIndex(row.attribute.findData(attribute))

        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual(len(details), 2)
        self.assertEqual(
            [(item.acquisition_mode, item.attribute) for item in details],
            [
                (ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
                (ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.NONFOSSIL),
            ],
        )
        self.assertEqual([item.detail_id for item in details], ["electricity-detail-1", "electricity-detail-2"])
        self.assertEqual(rows[2].attribute.currentData(), "SELF_CONSUMED_EXCLUDED")
    def test_process_instances_keep_identity_and_ui_domain_results_match(self) -> None:
        self.page.enterprise_name.setText("多工序UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        roles = (
            (MaterialRole.CALCINATION_FEED, "原料", "100", "80", "10"),
            (MaterialRole.CALCINED_PRODUCT, "煅后料", "70", "90", "2"),
        )
        first = self.page._process_rows["calcination"][0]
        for role, label, mass, fc, vm in roles:
            material = self._material_for_role(first, role)
            self._fill_material_line(material, role, f"{label}甲", mass, fc, vm)
        second = self.page._add_process_row("calcination")
        for index, (role, label, mass, fc, vm) in enumerate(roles):
            material = self._material_for_role(second, role)
            self._fill_material_line(material, role, f"{label}乙", "240" if index == 0 else "180", "75" if index == 0 else "88", "8" if index == 0 else "1")
        input_value = self.page._input()
        self.assertEqual(len(input_value.calcinations), 2)
        first_id, second_id = (item.instance_id for item in input_value.calcinations)
        self.assertEqual([line.name for line in input_value.calcinations[0].material_rows], ["原料甲", "煅后料甲"])
        self.assertEqual([line.name for line in input_value.calcinations[1].material_rows], ["原料乙", "煅后料乙"])
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
        self.assertEqual([str(row["instance_id"]) for row in self.page._process_rows["calcination"]], [before_delete[0], third_id])
    def test_process_validation_names_the_invalid_instance_in_business_language(self) -> None:
        self.page.enterprise_name.setText("实例错误定位企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-GRAPHITIZATION-001")
        roles = (
            (MaterialRole.GRAPHITIZATION_PACKING, "保温料", "10", "50", "2"),
            (MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品", "100", "80", "10"),
            (MaterialRole.GRAPHITIZED_PRODUCT, "石墨化产品", "95", "90", "1"),
        )
        rows = [self.page._process_rows["graphitization"][0]]
        rows.append(self.page._add_process_row("graphitization"))
        for row_index, row in enumerate(rows):
            for role, label, mass, fc, vm in roles:
                material = self._material_for_role(row, role)
                self._fill_material_line(material, role, f"{label}{row_index + 1}", mass, fc, vm)
        invalid_row = self.page._add_process_row("graphitization")
        invalid_row["materials"][0]["mass"].setText("1")

        self.page._run_calculation()

        messages = tree_texts(self.page.validation_list)
        self.assertTrue(any("石墨化过程 3" in message for message in messages), messages)
        self.assertTrue(any("必填信息不完整" in message for message in messages), messages)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.record_repository.list_all(), ())
    def test_one_calculation_collects_issues_from_multiple_source_cards(self) -> None:
        self.page.enterprise_name.setText("多排放源错误汇总企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        self._set_source_involved("CAR-SRC-GRAPHITIZATION-001")
        self.page._process_rows["calcination"][0]["materials"][0]["mass"].setText("10")
        self.page._process_rows["graphitization"][0]["materials"][0]["mass"].setText("1")

        self.page.calculate_button.click()
        self.application.processEvents()

        messages = tree_texts(self.page.validation_list)
        joined = "\n".join(messages)
        self.assertTrue(any(text.startswith("必须修正（") for text in messages), messages)
        self.assertTrue(any("煅烧过程 1" in text for text in messages), messages)
        self.assertTrue(any("石墨化过程 1" in text for text in messages), messages)
        self.assertIn("煅烧", joined)
        self.assertIn("石墨化", joined)
        self.assertGreater(sum("必填信息不完整" in text for text in messages), 1)
        self.assertNotIn("CAR-VAL-", joined)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.page.record_repository.list_all(), ())
    def test_new_accounting_reset_removes_secondary_business_rows(self) -> None:
        for prefix in ("calcination", "baking", "graphitization", "fume", "fgd"):
            self.page._add_process_row(prefix)
        self.page._add_fgd_component(self.page._process_rows["fgd"][0])
        self.page._add_unified_energy_row(kind="purchased_heat", line_id="extra-purchased-heat")
        self.page._add_unified_energy_row(kind="exported_heat", line_id="extra-exported-heat")
        self.page._add_unified_energy_row(kind="exported_electricity", line_id="extra-exported-electricity")
        for prefix, rows in self.page._process_rows.items():
            for row in rows[1:]:
                fields = row.get("fields", {})
                if fields:
                    next(iter(fields.values())).setText("123")
                elif row.get("materials"):
                    row["materials"][0]["mass"].setText("123")
        self.page._energy_family_rows["heat"][1].amount.setText("123")
        self.page._energy_family_rows["heat"][2].amount.setText("456")
        self.page._energy_family_rows["electricity"][1].amount.setText("789")

        self.page._reset_for_new_accounting()

        self.assertTrue(all(len(rows) == 1 for rows in self.page._process_rows.values()))
        self.assertEqual(len(self.page._process_rows["fgd"][0]["components"]), 1)
        self.assertEqual(len(self.page._energy_family_rows["heat"]), 1)
        self.assertEqual(len(self.page._energy_family_rows["electricity"]), 1)
        self.assertEqual(self.page._energy_family_rows["heat"][0].kind.currentData(), "purchased_heat")
        self.assertEqual(self.page._energy_family_rows["electricity"][0].kind.currentData(), "purchased_electricity")
        self.assertEqual(self.page._energy_family_rows["heat"][0].amount.text(), "")
        self.assertEqual(self.page._energy_family_rows["electricity"][0].amount.text(), "")
        self.assertFalse(any(
            row.get("flags", {}).get("carbon_output_included_in_input", None).isChecked()
            for prefix in ("calcination", "baking")
            for row in self.page._process_rows[prefix]
        ))
    def test_energy_line_ids_survive_middle_deletion_and_form_state_restore(self) -> None:
        heat_rows = self.page._energy_family_rows["heat"]
        heat_rows[0].line_id.setText("heat-1")
        heat_rows[0].amount.setText("10")
        heat_rows[0].enthalpy_mode.setCurrentIndex(heat_rows[0].enthalpy_mode.findData("MANUAL"))
        heat_rows[0].enthalpy.setText("2800")
        second_heat = self.page._add_unified_energy_row(kind="purchased_heat", line_id="heat-2")
        second_heat.amount.setText("20")
        third_heat = self.page._add_unified_energy_row(kind="purchased_heat", line_id="heat-3")
        third_heat.amount.setText("30")
        for row in (heat_rows[0], second_heat, third_heat):
            row.enthalpy_mode.setCurrentIndex(row.enthalpy_mode.findData("MANUAL"))
            row.enthalpy.setText("2800")
            row.heat_factor_mode.setCurrentIndex(row.heat_factor_mode.findData(HeatFactorMode.MEASURED))
            row.measured_heat_factor.setText("0.11")
            row.heat_source.setText("多来源身份测试报告")
        self.page._remove_unified_energy_row(second_heat)

        electricity_rows = self.page._energy_family_rows["electricity"]
        first_power = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-1")
        first_power.amount.setText("1")
        first_power.factor_mode.setCurrentIndex(first_power.factor_mode.findData("MANUAL"))
        first_power.manual_factor.setText("0.50")
        second_power = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-2")
        second_power.amount.setText("2")
        third_power = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-3")
        third_power.amount.setText("3")
        for row in (second_power, third_power):
            row.factor_mode.setCurrentIndex(row.factor_mode.findData("MANUAL"))
            row.manual_factor.setText("0.50")
        self.page._remove_unified_energy_row(second_power)

        state = self.page._capture_form_state()
        self.assertEqual(
            [item["line_id"] for item in state["energy_rows"] if item["kind"] == "purchased_heat"],
            ["heat-1", "heat-3"],
        )
        self.assertEqual(
            [item["line_id"] for item in state["energy_rows"] if item["kind"] == "exported_electricity"],
            ["exported-electricity-1", "exported-electricity-3"],
        )
        self.assertEqual([line.line_id for line in self.page._heat("heat")], ["heat-1", "heat-3"])
        self.assertEqual([line.line_id for line in self.page._exported_electricity()], ["exported-electricity-1", "exported-electricity-3"])

        self.page._restore_form_state(state)
        self.assertEqual([line.line_id for line in self.page._heat("heat")], ["heat-1", "heat-3"])
        self.assertEqual([line.line_id for line in self.page._exported_electricity()], ["exported-electricity-1", "exported-electricity-3"])
        next_heat = self.page._add_unified_energy_row(kind="purchased_heat")
        next_power = self.page._add_unified_energy_row(kind="exported_electricity")
        existing_ids = {"heat-1", "heat-3", "exported-electricity-1", "exported-electricity-3"}
        self.assertNotIn(next_heat.line_id.text(), existing_ids)
        self.assertNotIn(next_power.line_id.text(), existing_ids)

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
            self.assertEqual(
                [row.line_id.text() for row in fresh_page._energy_family_rows["heat"]],
                ["heat-1", "heat-3"],
            )
            self.assertEqual(
                [row.line_id.text() for row in fresh_page._energy_family_rows["electricity"] if row.kind.currentData() == "exported_electricity"],
                ["exported-electricity-1", "exported-electricity-3"],
            )
        finally:
            fresh_window.close()
    def test_fgd_ui_keeps_multiple_components_scoped_to_each_unit(self) -> None:
        self.page.enterprise_name.setText("多脱硫设施UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-FGD-001")
        first_unit = self.page._process_rows["fgd"][0]
        first_unit["reagent_name"].setText("石灰石")
        first_unit["group_amount"].setText("10")
        first_component, = first_unit["components"]
        self._select_carbonate(first_component, "car-par-c2-caco3")
        first_component["i_source"].setCurrentIndex(first_component["i_source"].findData("MEASURED"))
        first_component["i"].setText("40")
        second_component = self.page._add_fgd_component(first_unit)
        self._select_carbonate(second_component, "car-par-c2-mgco3")
        second_component["i_source"].setCurrentIndex(second_component["i_source"].findData("MEASURED"))
        second_component["i"].setText("40")
        second_component["tr_source"].setCurrentIndex(second_component["tr_source"].findData("MEASURED"))
        second_component["tr"].setText("100")
        self.assertEqual([component["i_source"].currentData() for component in first_unit["components"]], ["MEASURED", "MEASURED"])
        self.page._add_process_row("fgd")
        second_unit = self.page._process_rows["fgd"][1]
        second_unit["reagent_name"].setText("石灰石")
        second_unit["group_amount"].setText("5")
        self._select_carbonate(second_unit["components"][0], "car-par-c2-na2co3")
        input_value = self.page._input()
        self.assertEqual([len(unit.components) for unit in input_value.fgd_units], [2, 1])
        self.assertEqual([unit.reagent_name for unit in input_value.fgd_units], ["石灰石", "石灰石"])
        self.assertNotEqual(input_value.fgd_units[0].instance_id, input_value.fgd_units[1].instance_id)
        self.assertEqual(
            [[component.amount.value for component in unit.components] for unit in input_value.fgd_units],
            [[Decimal("10"), Decimal("10")], [Decimal("5")]],
        )
        self.assertTrue(all(component.carbonate_fraction.source_kind is ParameterSourceKind.MEASURED for component in input_value.fgd_units[0].components))
        self.assertEqual(
            [component.conversion_rate.source_kind for component in input_value.fgd_units[0].components],
            [ParameterSourceKind.STANDARD_DEFAULT, ParameterSourceKind.MEASURED],
        )
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
        fgd_lines = [line for line in outcome.result.lines if line.emission_source_id == "CAR-SRC-FGD-001"]
        expected_fgd = sum((
            component.amount.value
            * component.carbonate_fraction.value
            * component.emission_factor.value
            * component.conversion_rate.value
            for unit in input_value.fgd_units
            for component in unit.components
        ), Decimal("0"))
        self.assertEqual(len(fgd_lines), len(input_value.fgd_units))
        self.assertEqual(sum((line.amount for line in fgd_lines), Decimal("0")), expected_fgd)
        self.assertTrue(any(line.line_id.endswith(input_value.fgd_units[0].instance_id) for line in outcome.result.lines))
        self.assertTrue(any(line.line_id.endswith(input_value.fgd_units[1].instance_id) for line in outcome.result.lines))
        self.assertEqual(
            [component.emission_factor.source_id for component in input_value.fgd_units[0].components],
            ["SRC-32151-34-2024", "SRC-32151-34-2024"],
        )
    def test_ui_builds_multiple_instances_for_every_process_source(self) -> None:
        from packages.standards.carbon_material_normalization import normalize_material_inputs

        self.page.enterprise_name.setText("全过程多实例企业")
        self.page.boundary_confirmed.setChecked(True)
        source_ids = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
            "fume": "CAR-SRC-FUME-INCINERATION-001",
            "fgd": "CAR-SRC-FGD-001",
        }
        material_roles = {
            "calcination": (
                (MaterialRole.CALCINATION_FEED, "原料", "100", "80", "10"),
                (MaterialRole.CALCINED_PRODUCT, "煅后料", "70", "90", "2"),
            ),
            "baking": (
                (MaterialRole.BAKING_FILLER, "填充料", "10", "50", "2"),
                (MaterialRole.GREEN_BAKING_PRODUCT, "待焙烧品", "100", "80", "10"),
                (MaterialRole.BAKED_PRODUCT, "焙烧产品", "95", "90", "1"),
            ),
            "graphitization": (
                (MaterialRole.GRAPHITIZATION_PACKING, "保温料", "30", "50", "2"),
                (MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品", "100", "80", "10"),
                (MaterialRole.GRAPHITIZED_PRODUCT, "石墨化产品", "95", "90", "1"),
            ),
        }
        for prefix, source_id in source_ids.items():
            self._set_source_involved(source_id)
            first = self.page._process_rows[prefix][0]
            if prefix in material_roles:
                rows = (first, self.page._add_process_row(prefix))
                for row_index, row in enumerate(rows):
                    scale = 1 if row_index == 0 else 2
                    for role, label, mass, fixed_carbon, volatile_matter in material_roles[prefix]:
                        material = self._material_for_role(row, role)
                        self._fill_material_line(
                            material, role, f"{label}{row_index + 1}", str(Decimal(mass) * scale),
                            fixed_carbon, volatile_matter,
                        )
                continue
            if prefix == "fgd":
                first["reagent_name"].setText("石灰石")
                first["group_amount"].setText("10")
                component = first["components"][0]
                self._select_carbonate(component, "car-par-c2-caco3")
                component["i_source"].setCurrentIndex(component["i_source"].findData("MEASURED"))
                component["i"].setText("45")
                second_component = self.page._add_fgd_component(first)
                self._select_carbonate(second_component, "car-par-c2-mgco3")
                second_component["i_source"].setCurrentIndex(second_component["i_source"].findData("MEASURED"))
                second_component["i"].setText("45")
                second_component["tr_source"].setCurrentIndex(second_component["tr_source"].findData("MEASURED"))
                second_component["tr"].setText("100")
                second = self.page._add_process_row(prefix)
                second["reagent_name"].setText("石灰石")
                second["group_amount"].setText("5")
                second_component = second["components"][0]
                self._select_carbonate(second_component, "car-par-c2-na2co3")
                continue
            for key, value in {"q": "1000", "qvar": "10", "hm": "30", "fch": "0.02", "fox": "0.98", "duration": "1"}.items():
                first["fields"][key].setText(value)
            second = self.page._add_process_row(prefix)
            for key, value in {"q": "2000", "qvar": "8", "hm": "25", "fch": "0.03", "fox": "0.95", "duration": "2"}.items():
                second["fields"][key].setText(value)
            from datetime import timedelta
            for row,days in ((first,1),(second,2)):
                row["segment_start"].setText(self.page._period().start.isoformat())
                row["segment_end"].setText((self.page._period().start+timedelta(days=days)).isoformat())

        domain_input = self.page._input()
        process_tuples = {
            "calcination": domain_input.calcinations,
            "baking": domain_input.bakings,
            "graphitization": domain_input.graphitizations,
            "fume": tuple(segment.measurements for segment in domain_input.fume_segments),
            "fgd": domain_input.fgd_units,
        }
        self.assertTrue(all(len(items) == 2 for items in process_tuples.values()))
        for prefix, items in process_tuples.items():
            self.assertEqual(len({item.instance_id for item in items}), 2, prefix)
            self.assertNotIn(items[0].instance_id, "\n".join(label.text() for label in self.page.findChildren(QLabel)))
        for prefix, field in (("calcination", "gc"), ("baking", "bpm"), ("graphitization", "gpm")):
            items = process_tuples[prefix]
            normalized = normalize_material_inputs(prefix, items[0].material_rows, policy=self.page.calculator.policy)
            self.assertFalse(normalized.problems, normalized.problems)
            self.assertEqual(getattr(items[0], field).value, normalized.value(field))
            self.assertTrue(items[0].material_rows)
        self.assertEqual(str(domain_input.fume_segments[0].measurements.q.value), "1000")
        self.assertEqual(str(domain_input.fume_segments[1].measurements.q.value), "2000")
        self.assertEqual(
            [component.emission_factor.source_id for component in domain_input.fgd_units[0].components],
            ["SRC-32151-34-2024", "SRC-32151-34-2024"],
        )
        self.assertEqual(domain_input.fgd_units[1].components[0].emission_factor.source_id, "SRC-32151-34-2024")
        for source_id in source_ids.values():
            self.assertTrue(any(state.source_id == source_id and state.status is EmissionSourceStatus.INVOLVED for state in domain_input.source_states))

        outcome = self.page.calculator.calculate(domain_input)
        self.assertTrue(outcome.successful, outcome.problems)
        expected_sources = {
            "calcination": "CAR-SRC-CALCINATION-001",
            "baking": "CAR-SRC-BAKING-001",
            "graphitization": "CAR-SRC-GRAPHITIZATION-001",
            "fume": "CAR-SRC-FUME-INCINERATION-001",
            "fgd": "CAR-SRC-FGD-001",
        }
        for name, items in process_tuples.items():
            rows = [line for line in outcome.result.lines if line.emission_source_id == expected_sources[name]]
            self.assertEqual(len(rows), 2, name)
            if name == "fume":
                traces = [trace for trace in outcome.traces if trace.source_id == expected_sources[name]]
                self.assertEqual(len({line.line_id for line in rows}),2)
                self.assertEqual({dict(trace.provenance)["fume.source_instance_id"] for trace in traces},{item.instance_id for item in items})
                self.assertEqual({dict(trace.provenance)["fume.segment_id"] for trace in traces},{segment.segment_id for segment in domain_input.fume_segments})
            else:
                self.assertEqual({line.line_id.rsplit(".", 1)[-1] for line in rows}, {item.instance_id for item in items})
    def test_heat_and_exported_power_rows_keep_factors_and_sources_independently(self) -> None:
        self.page.enterprise_name.setText("多能源来源UI企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-PURCHASED-HEAT-001")
        self._set_source_involved("CAR-SRC-EXPORTED-HEAT-001")
        self._set_source_involved("CAR-SRC-EXPORTED-ELECTRICITY-001")
        first_heat = self.page._energy_family_rows["heat"][0]
        first_heat.heat_boundary.setCurrentIndex(first_heat.heat_boundary.findData("OUTSIDE_ENTERPRISE"))
        first_heat.amount.setText("100")
        first_heat.enthalpy.setText("2800")
        first_heat.enthalpy_mode.setCurrentIndex(first_heat.enthalpy_mode.findData("MANUAL"))
        first_heat.heat_factor_mode.setCurrentIndex(first_heat.heat_factor_mode.findData(HeatFactorMode.MEASURED))
        first_heat.measured_heat_factor.setText("0.11")
        first_heat.heat_source.setText("购热报告-A")
        first_exported_heat = self.page._add_unified_energy_row(kind="exported_heat", line_id="exported-heat-a")
        first_exported_heat.amount.setText("25")
        first_exported_heat.enthalpy.setText("2700")
        first_exported_heat.enthalpy_mode.setCurrentIndex(first_exported_heat.enthalpy_mode.findData("MANUAL"))
        first_exported_heat.heat_factor_mode.setCurrentIndex(first_exported_heat.heat_factor_mode.findData(HeatFactorMode.MEASURED))
        first_exported_heat.measured_heat_factor.setText("0.12")
        first_exported_heat.heat_source.setText("售热报告-A")
        second_heat = self.page._add_unified_energy_row(kind="purchased_heat", line_id="purchased-heat-b")
        second_heat.heat_boundary.setCurrentIndex(second_heat.heat_boundary.findData("OUTSIDE_ENTERPRISE"))
        second_heat.amount.setText("200")
        second_heat.enthalpy.setText("3000")
        second_heat.enthalpy_mode.setCurrentIndex(second_heat.enthalpy_mode.findData("MANUAL"))
        second_heat.heat_factor_mode.setCurrentIndex(second_heat.heat_factor_mode.findData(HeatFactorMode.MEASURED))
        second_heat.measured_heat_factor.setText("0.20")
        second_heat.heat_source.setText("购热报告-B")
        second_exported_heat = self.page._add_unified_energy_row(kind="exported_heat", line_id="exported-heat-b")
        second_exported_heat.amount.setText("75")
        second_exported_heat.enthalpy.setText("2900")
        second_exported_heat.enthalpy_mode.setCurrentIndex(second_exported_heat.enthalpy_mode.findData("MANUAL"))
        second_exported_heat.heat_factor_mode.setCurrentIndex(second_exported_heat.heat_factor_mode.findData(HeatFactorMode.MEASURED))
        second_exported_heat.measured_heat_factor.setText("0.16")
        second_exported_heat.heat_source.setText("售热报告-B")
        first_power = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-a")
        first_power.amount.setText("10")
        first_power.factor_mode.setCurrentIndex(first_power.factor_mode.findData("MANUAL"))
        first_power.manual_factor.setText("0.50")
        first_power.electricity_source.setText("电力报告-A")
        second_power = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-b")
        second_power.amount.setText("4")
        second_power.factor_mode.setCurrentIndex(second_power.factor_mode.findData("MANUAL"))
        second_power.manual_factor.setText("0.25")
        second_power.electricity_source.setText("电力报告-B")

        input_value = self.page._input()
        self.assertEqual([line.factor.value for line in input_value.purchased_heat], [Decimal("0.11"), Decimal("0.20")])
        self.assertEqual([line.factor.value for line in input_value.exported_heat], [Decimal("0.12"), Decimal("0.16")])
        self.assertEqual([line.factor.value for line in input_value.exported_electricity], [Decimal("0.50"), Decimal("0.25")])
        self.assertEqual(
            [item.factor_source_note for item in input_value.purchased_heat],
            ["购热报告-A", "购热报告-B"],
        )
        self.assertEqual(
            [item.factor_source_note for item in input_value.exported_heat],
            ["售热报告-A", "售热报告-B"],
        )
        outcome = self.page.calculator.calculate(input_value)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertEqual(sum(1 for line in outcome.result.lines if line.emission_source_id == "CAR-SRC-EXPORTED-ELECTRICITY-001"), 2)
    def _set_source_involved(self, source_id: str) -> None:
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
            self.page._source_toggle_buttons[group_by_source[source_id]].click()
            self.application.processEvents()

    def _fill_material_line(self, row: dict[str, object], role: MaterialRole, name: str, mass: str,
                            fixed_carbon: str = "50", volatile_matter: str = "10") -> None:
        row["role"].setCurrentIndex(row["role"].findData(role))
        row["name"].setText(name)
        row["mass"].setText(mass)
        row["fixed_carbon"].setText(fixed_carbon)
        row["volatile_matter"].setText(volatile_matter)

    @staticmethod
    def _material_for_role(process_row: dict[str, object], role: MaterialRole) -> dict[str, object]:
        materials = process_row.get("materials", [])
        if not isinstance(materials, list):
            raise AssertionError("process row has no material rows")
        return next(
            line for line in materials
            if isinstance(line, dict)
            and isinstance(line.get("role"), QComboBox)
            and line["role"].currentData() == role
        )

    def _select_carbonate(self, component: dict[str, object], parameter_id: str) -> None:
        selector = component["carbonate_type"]
        self.assertIsInstance(selector, QComboBox)
        option = next(
            (item for item in self.page._carbonate_options() if item.factor.parameter_id == parameter_id),
            None,
        )
        self.assertIsNotNone(option, parameter_id)
        index = next(
            (i for i in range(selector.count())
             if getattr(selector.itemData(i), "subject_id", None) == option.subject_id),
            -1,
        )
        self.assertGreaterEqual(index, 0, option.label)
        selector.setCurrentIndex(index)
        selected = selector.currentData()
        self.assertIsNotNone(selected)
        self.assertEqual(selected.factor.parameter_id, parameter_id)
        self.assertEqual(selected.factor.source_id, "SRC-32151-34-2024")

    def test_electricity_rows_show_factor_resolution_and_exclude_self_consumption(self) -> None:
        self.page.period_year.setValue(2026)
        rows = self.page._energy_family_rows["electricity"]
        self.page._add_unified_energy_row(kind="purchased_electricity", line_id="grid-nonfossil")
        self.page._add_unified_energy_row(kind="purchased_electricity", line_id="self-consumed")
        values = (
            ("grid-ordinary", "10", ElectricityAttribute.ORDINARY),
            ("grid-nonfossil", "20", ElectricityAttribute.NONFOSSIL),
            ("self-consumed", "30", "SELF_CONSUMED_EXCLUDED"),
        )
        for row, (line_id, amount, attribute) in zip(rows, values):
            row.line_id.setText(line_id)
            row.amount.setText(amount)
            row.attribute.setCurrentIndex(row.attribute.findData(attribute))

        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual([item.detail_id for item in details], ["grid-ordinary", "grid-nonfossil"])
        self.assertEqual([item.attribute for item in details], [ElectricityAttribute.ORDINARY, ElectricityAttribute.NONFOSSIL])
        ordinary_option = rows[0].factor_selector.currentData()
        self.assertIsNotNone(ordinary_option)
        ordinary_factor_id = ordinary_option.factor.factor_id
        self.assertEqual(self.page._electricity_resolution_states.get(rows[0].line_id.text()), "RESOLVED")
        self.assertEqual(details[0].selected_factor_id, ordinary_factor_id)
        self.assertNotIn(ordinary_factor_id, rows[0].status.text())
        self.assertNotIn("审核状态", rows[0].status.text())
        self.assertEqual(self.page._electricity_resolution_states.get(rows[1].line_id.text()), "RESOLVED")
        self.assertIsNone(details[1].selected_factor_id)
        for row in rows[:2]:
            self.assertNotIn("审核状态", row.status.text())
        self.assertIn("不计入", rows[2].status.text())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
    def test_page_preserves_other_activity_and_transport_as_warnings(self) -> None:
        self.page.enterprise_name.setText("其他活动声明企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.other_activity_present.setChecked(True)
        self.page.transport_present.setChecked(True)
        value = self.page._input()
        self.assertTrue(value.other_activity_present)
        self.assertTrue(value.transport_present)
        outcome = self.page.calculator.calculate(value)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertTrue(all(problem.level.value != "ERROR" for problem in outcome.problems if problem.code == "CAR-VAL-OTHER-STANDARD"))
        self.assertTrue(any(problem.code == "CAR-VAL-OTHER-STANDARD" for problem in outcome.problems))

    def test_component_selectors_are_hidden_and_material_kinds_are_automatic(self) -> None:
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        process = self.page._process_rows["calcination"][0]
        feed = self._material_for_role(process, MaterialRole.CALCINATION_FEED)
        self._fill_material_line(feed, MaterialRole.CALCINATION_FEED, "原料甲", "100", "50", "10")
        product = self._material_for_role(process, MaterialRole.CALCINED_PRODUCT)
        self._fill_material_line(product, MaterialRole.CALCINED_PRODUCT, "煅后料甲", "70", "25", "2")
        controls = self.page._material_controls["calcination"]
        self.assertFalse(controls["basis_editor"].isVisible())
        self.assertFalse(controls["fixed_carbon_component_kind"].isVisible())
        self.assertFalse(controls["volatile_matter_component_kind"].isVisible())
        value = self.page._input()
        assert value.calcination is not None
        self.assertIs(value.calcination.fixed_carbon_component_kind, MaterialComponentKind.FIXED_CARBON)
        self.assertIs(value.calcination.volatile_matter_component_kind, MaterialComponentKind.VOLATILE_MATTER)
        outcome = self.page.calculator.calculate(value)
        self.assertTrue(outcome.successful, outcome.problems)
    def test_page_exposes_output_energy_and_hides_legacy_material_basis_controls(self) -> None:
        self.assertEqual(set(self.page._energy_family_rows), {"electricity", "heat"})
        self.assertTrue(self.page.findChild(QWidget, "unifiedElectricityCard"))
        self.assertTrue(self.page.findChild(QWidget, "unifiedHeatCard"))
        for prefix in ("calcination", "baking", "graphitization"):
            controls = self.page._material_controls[prefix]
            self.assertFalse(controls["basis_editor"].isVisible())
            self.assertFalse(controls["basis_summary"].isVisible())
            self.assertFalse(controls["professional_details"].isVisible())
            for key in ("mass_basis", "composition_basis", "normalized_basis",
                        "fixed_carbon_component_kind", "volatile_matter_component_kind"):
                self.assertFalse(controls[key].isVisible(), f"{prefix}.{key}")

        self.page.enterprise_name.setText("输出能源控件企业")
        self.page.period_year.setValue(2026)
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-EXPORTED-ELECTRICITY-001")
        self._set_source_involved("CAR-SRC-EXPORTED-HEAT-001")
        electricity = self.page._add_unified_energy_row(kind="exported_electricity", line_id="exported-electricity-test")
        electricity.amount.setText("2")
        heat = self.page._add_unified_energy_row(kind="exported_heat", line_id="exported-heat-test")
        heat.amount.setText("100")
        heat.enthalpy.setText("2800")
        heat.enthalpy_mode.setCurrentIndex(heat.enthalpy_mode.findData("MANUAL"))
        value = self.page._input()
        self.assertEqual(len(value.exported_electricity), 1)
        self.assertEqual(value.exported_electricity[0].amount.value, Decimal("2"))
        self.assertEqual(len(value.exported_heat), 1)
        self.assertEqual(value.exported_heat[0].amount.value, Decimal("100"))
        self.assertEqual(value.exported_heat[0].amount.unit, "t")
        self.assertEqual(value.exported_heat[0].steam_amount_t.value, Decimal("100"))
        self.assertTrue(value.exported_heat[0].manual_enthalpy)
        self.assertEqual(value.exported_heat[0].factor_mode, HeatFactorMode.STANDARD_DEFAULT)
    def test_empty_enterprise_name_is_optional_and_successfully_creates_record(self) -> None:
        self.page.calculate_button.click()
        self.application.processEvents()
        self.assertFalse(self.page.result_card.isHidden())
        records = self.page.record_repository.list_all()
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].input_snapshot.enterprise_name)
        messages = tree_texts(self.page.validation_list)
        self.assertTrue(any("跨越所选标准的实施日期" in message for message in messages), messages)
        self.assertTrue(any("此提醒不阻断核算" in message for message in messages), messages)
        self.assertEqual(self.page.validation_list.topLevelItemCount(), 1)
        self.assertEqual(records[0].status.value, "COMPLETED_WITH_WARNINGS")

    def test_heat_defaults_to_canonical_factor_and_automatic_steam_enthalpy(self) -> None:
        self.page.period_year.setValue(2026)
        self.page.boundary_confirmed.setChecked(True)
        row = self.page._energy_family_rows["heat"][0]
        self.assertEqual(row.amount.property("fieldUnit"), "t")
        self.assertEqual(get_field_spec("heat_pressure").label, "蒸汽压力（MPa，绝压）")
        self.assertEqual(row.heat_factor_mode.currentData(), HeatFactorMode.STANDARD_DEFAULT)
        self.assertEqual(row.heat_factor_mode.currentText(), "缺省值")
        self.assertEqual(row.enthalpy_mode.currentData(), "AUTO")
        self.assertFalse(row.measured_heat_factor.isVisible())
        self.assertFalse(row.heat_source.isVisible())
        self.assertFalse(self.page.heat_factor_selector.isVisible())
        self.assertFalse(self.page.heat_factor_metadata.isVisible())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))

        self._set_source_involved("CAR-SRC-PURCHASED-HEAT-001")
        self._set_source_involved("CAR-SRC-EXPORTED-HEAT-001")
        row.heat_boundary.setCurrentIndex(row.heat_boundary.findData("OUTSIDE_ENTERPRISE"))
        row.amount.setText("1")
        row.pressure.setText("0.1")
        output_row = self.page._add_unified_energy_row(kind="exported_heat", line_id="exported-heat-default")
        output_row.amount.setText("0.5")
        output_row.pressure.setText("0.1")
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
        self.assertEqual(provenance["enthalpy_source"], "IAPWS-IF97自动物性")
        self.assertEqual(provenance["table"], "")
        self.assertEqual(provenance["enthalpy_method_version"], "CAR-HEAT-IF97-017.1")
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
        self.assertEqual(dict(output_trace.provenance)["enthalpy_source"], "IAPWS-IF97自动物性")
    def test_process_material_rows_flow_through_shared_normalization(self) -> None:
        from packages.standards.carbon_material_normalization import normalize_material_inputs

        self.page.enterprise_name.setText("多物料输入企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        process_row = self.page._process_rows["calcination"][0]
        feed = self._material_for_role(process_row, MaterialRole.CALCINATION_FEED)
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
        product = self._material_for_role(process_row, MaterialRole.CALCINED_PRODUCT)
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
        self.assertIn("原料 150.00 t", process_row["material_summary"].text())
        outcome = self.page.calculator.calculate(domain_input)
        self.assertTrue(outcome.successful, outcome.problems)
        trace = next(item for item in outcome.traces if item.formula_id == "CAR-FML-CALCINATION-001")
        provenance = set(trace.provenance)
        self.assertIn((f"material.{feed['line_id']}.name", "原料甲"), provenance)
        self.assertIn((f"material.{second_feed['line_id']}.name", "原料乙"), provenance)
        self.assertIn((f"material.{product['line_id']}.name", "煅后料"), provenance)

    def test_manual_steam_result_explains_the_user_entered_enthalpy(self) -> None:
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-PURCHASED-HEAT-001")
        row = self.page._energy_family_rows["heat"][0]
        row.heat_boundary.setCurrentIndex(row.heat_boundary.findData("OUTSIDE_ENTERPRISE"))
        row.amount.setText("1")
        row.enthalpy.setText("2810")
        row.enthalpy_mode.setCurrentIndex(row.enthalpy_mode.findData("MANUAL"))

        self.page._run_calculation()

        self.assertFalse(self.page.result_card.isHidden())
        explanation = self.page.result_line_details.text()
        self.assertIn("用户手动填写", explanation)
        self.assertIn("2810.0 kJ/kg", explanation)
        self.assertIn("本次按您填写的 2810.0 kJ/kg 计算", explanation)
    def test_legacy_project_steam_kg_and_manual_enthalpy_restore_without_loss(self) -> None:
        legacy_state = self.page._capture_form_state()
        legacy_state.pop("energy_rows", None)
        legacy_state.pop("steam_input_version", None)
        legacy_state["heat_amountInput"] = "1250"
        legacy_state["heat_enthalpyInput"] = "2780"
        legacy_state["heatFactorModeSelector"] = 0
        self.page._restore_form_state(legacy_state)
        heat_rows = [
            row for row in self.page._energy_family_rows["heat"]
            if row.kind.currentData() == "purchased_heat"
        ]
        self.assertEqual(len(heat_rows), 1)
        row = heat_rows[0]
        self.assertEqual(row.amount.text(), "1.25")
        self.assertEqual(row.enthalpy.text(), "2780")
        self.assertEqual(row.enthalpy_mode.currentData(), "MANUAL")
        self.assertEqual(row.heat_factor_mode.currentData(), HeatFactorMode.STANDARD_DEFAULT)
    def test_material_basis_without_conversion_evidence_is_blocked(self) -> None:
        self.page.enterprise_name.setText("基准证明企业")
        self.page.boundary_confirmed.setChecked(True)
        self._set_source_involved("CAR-SRC-CALCINATION-001")
        process = self.page._process_rows["calcination"][0]
        feed = self._material_for_role(process, MaterialRole.CALCINATION_FEED)
        self._fill_material_line(feed, MaterialRole.CALCINATION_FEED, "原料甲", "100", "50", "10")
        product = self._material_for_role(process, MaterialRole.CALCINED_PRODUCT)
        self._fill_material_line(product, MaterialRole.CALCINED_PRODUCT, "煅后料甲", "70", "25", "2")
        current_input = self.page._input()
        current_process = current_input.calcinations[0]
        legacy_process = replace(
            current_process,
            material_rows=None,
            mass_basis=MaterialBasis.DRY,
            composition_basis=MaterialBasis.DRY,
            normalized_basis=MaterialBasis.RECEIVED,
            moisture_evidence=False,
            conversion_evidence=False,
        )
        legacy_input = replace(
            current_input,
            input_id="input.g06.legacy-basis-mismatch",
            calcination=legacy_process,
            calcinations=(legacy_process,),
        )
        outcome = self.page.calculator.calculate(legacy_input)
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
        calculator_repository = self.page.record_repository
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
