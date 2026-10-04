from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from packages.application import CatalogQueryService, ProjectWorkspaceService
from packages.core import (
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
    PeriodType,
)
from packages.persistence import SQLiteCatalogRepository, SQLiteProjectWorkspaceRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    EmissionSourceStatus,
    FGDInput,
    FuelPath,
    FuelType,
    InMemoryRecordRepository,
    ParameterSourceKind,
)
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage


F01 = "CAR-SRC-FUEL-001"


class AccountingProjectUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.root = root
        catalog_path = build_catalog_database(DEFAULT_SOURCE_PATH, root / "catalog.sqlite")
        self.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(catalog_path), as_of=date(2026, 9, 23)
        )
        self.project_service = ProjectWorkspaceService(
            SQLiteProjectWorkspaceRepository(root / "projects.sqlite")
        )
        self.records = InMemoryRecordRepository()
        self.page = self._new_page()

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.temp_directory.cleanup()

    def _new_page(self) -> CarbonMaterialAccountingPage:
        return CarbonMaterialAccountingPage(
            catalog_service=self.catalog_service,
            record_repository=self.records,
            project_service=self.project_service,
        )

    def _enable_fuel(self) -> None:
        action = self.page.findChild(QPushButton, f"sourceCardAction_{F01}")
        self.assertIsNotNone(action)
        assert action is not None
        action.click()
        self.assertTrue(self.page._source_is_enabled(F01))

    def test_legacy_project_without_carbonate_selection_opens_and_blocks_recalculation(self) -> None:
        self.page.project_name.setText("旧版脱硫项目")
        self.page.enterprise_name.setText("旧项目企业")
        self.page.boundary_confirmed.setChecked(True)
        fgd_status = self.page._source_statuses["CAR-SRC-FGD-001"]
        fgd_status.setCurrentIndex(fgd_status.findData(EmissionSourceStatus.INVOLVED))
        self.page._fields["fgd.cal"].setText("10")
        self.assertTrue(self.page._save_project())

        workspace = self.project_service.get(self.page._workspace.project_id)
        self.assertIsNotNone(workspace)
        assert workspace is not None
        unit = workspace.units[0]
        legacy_state = dict(unit.form_state)
        self.assertIn("fgdCarbonateTypeSelector", legacy_state)
        legacy_state.pop("fgdCarbonateTypeSelector")
        legacy_unit = replace(unit, form_state=legacy_state)
        legacy_workspace = replace(workspace, units=(legacy_unit,))
        self.project_service.save(legacy_workspace)

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        saved_index = self.page.saved_projects.findData(workspace.project_id)
        self.assertGreaterEqual(saved_index, 0)
        self.page.saved_projects.setCurrentIndex(saved_index)
        self.page._open_selected_project()

        self.assertEqual(self.page._fields["fgd.cal"].text(), "10")
        self.assertIsNone(self.page._carbonate_type_selector.currentData())
        restored = self.page._process("fgd", FGDInput)
        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertEqual(str(restored.components[0].amount.value), "10")
        self.assertIsNone(restored.components[0].emission_factor)

        self.page._run_calculation()
        validation_text = "\n".join(
            self.page.validation_list.item(index).text()
            for index in range(self.page.validation_list.count())
        )
        self.assertIn("请选择脱硫剂中的碳酸盐种类，或提供可追溯的排放因子。", validation_text)
        self.assertTrue(self.page.result_card.isHidden())
        self.assertEqual(self.records.list_all(), ())

    def test_period_choices_map_to_annual_month_and_custom_domain_periods(self) -> None:
        self.assertIs(self.page._period().period_type, PeriodType.ANNUAL)
        self.assertNotIn("accountingPeriodMonth", self.page._capture_form_state())

        self.page.period_year.setValue(2026)
        self.page.period_type.setCurrentIndex(7)
        monthly = self.page._period()
        self.assertIs(monthly.period_type, PeriodType.MONTHLY)
        self.assertEqual((monthly.start.isoformat(), monthly.end.isoformat()), ("2026-07-01", "2026-07-31"))

        self.page.period_type.setCurrentIndex(13)
        self.page.period_start.setDate(QDate(2026, 3, 14))
        self.page.period_end.setDate(QDate(2026, 8, 22))
        custom = self.page._period()
        self.assertIs(custom.period_type, PeriodType.CUSTOM)
        self.assertEqual((custom.start.isoformat(), custom.end.isoformat()), ("2026-03-14", "2026-08-22"))

    def test_natural_gas_heat_path_uses_verified_canonical_defaults(self) -> None:
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
        row.path.setCurrentIndex(row.path.findData(FuelPath.HEAT))
        row.activity.setText("10")

        self.assertEqual(row.activity.placeholderText(), "活动量（GJ）")
        self.assertEqual(row.carbon.placeholderText(), "单位含碳量（tC/GJ）")
        self.assertEqual(row.carbon.text(), "0.0153")
        self.assertEqual(row.oxidation.text(), "99.00")
        self.assertIn("标准默认", row.parameter_summary.text())
        fuel = self.page._fuel()[0]
        self.assertEqual(fuel.carbon_content.parameter_id, "natural_gas_carbon_content")
        self.assertEqual(str(fuel.carbon_content.value), "0.0153")
        self.assertEqual(str(fuel.oxidation_rate.value), "0.99")

    def test_source_check_shows_preview_or_missing_input_without_creating_a_record(self) -> None:
        self.page.enterprise_name.setText("燃料预览企业")
        self.page.boundary_confirmed.setChecked(True)
        self._enable_fuel()
        card = self.page._source_cards[F01]
        self.page._check_data()
        self.assertIn("需要补充", card.check_result_label.text())
        self.assertEqual(self.records.list_all(), ())

        fuel = self.page._fuel_rows[0]
        fuel.activity.setText("10")
        fuel.carbon.setText("0.2")
        fuel.oxidation.setText("98")
        fuel.source_reference.setText("燃料实测报告-预览")
        self.page._check_data()
        self.assertIn("本排放源排放量（预览）", card.check_result_label.text())
        self.assertIn("tCO₂", card.check_result_label.text())
        self.assertEqual(self.records.list_all(), ())

    def test_unit_can_be_renamed_and_only_nonfinal_unit_can_be_deleted(self) -> None:
        with (
            patch("packages.ui.carbon_material_page.QInputDialog.getItem", return_value=("生产工序", True)),
            patch("packages.ui.carbon_material_page.QInputDialog.getText", return_value=("石墨化工序", True)),
        ):
            self.page._add_accounting_unit()
        self.assertEqual(len(self.page._workspace.units), 2)
        with patch(
            "packages.ui.carbon_material_page.QInputDialog.getText",
            return_value=("煅烧工序", True),
        ):
            self.page._rename_accounting_unit()
        self.assertEqual(self.page._unit().name, "煅烧工序")
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.page._delete_accounting_unit()
        self.assertEqual(len(self.page._workspace.units), 1)
        self.assertEqual(self.page._unit().name, "全厂")
        with patch("packages.ui.carbon_material_page.QMessageBox.information") as information:
            self.page._delete_accounting_unit()
        information.assert_called_once()
        self.assertEqual(len(self.page._workspace.units), 1)

    def test_close_requires_explicit_save_discard_or_cancel_choice(self) -> None:
        self.page.project_name.setText("关闭提示项目")
        self.page._project_dirty = True
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Cancel,
        ):
            self.assertFalse(self.page.confirm_project_close())
        self.assertEqual(self.project_service.list_all(), ())

        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Discard,
        ):
            self.assertTrue(self.page.confirm_project_close())
        self.assertEqual(self.project_service.list_all(), ())

        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Save,
        ):
            self.assertTrue(self.page.confirm_project_close())
        self.assertEqual(len(self.project_service.list_all()), 1)
        self.assertFalse(self.page._project_dirty)

    def test_deleting_active_project_resets_input_but_keeps_record_store_separate(self) -> None:
        self.page.project_name.setText("待删除的项目")
        self.page.enterprise_name.setText("不应残留的企业名称")
        self.assertTrue(self.page._save_project())
        deleted_id = self.page._workspace.project_id
        self.assertIsNotNone(self.project_service.get(deleted_id))
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.page._delete_selected_project()
        self.assertIsNone(self.project_service.get(deleted_id))
        self.assertNotEqual(self.page._workspace.project_id, deleted_id)
        self.assertEqual(self.page.enterprise_name.text(), "")
        self.assertFalse(self.page._project_dirty)
        self.assertEqual(self.records.list_all(), ())

    def test_electricity_rows_keep_stable_identity_through_delete_switch_and_reopen(self) -> None:
        self.page.project_name.setText("多条电力项目")
        self.page._add_electricity_row()
        self.page._add_electricity_row()
        middle = self.page._electricity_rows[1]
        self.page._remove_electricity_row(middle)
        self.page._add_electricity_row()
        expected = (
            (
                "electricity-a",
                "11",
                ElectricityAcquisitionMode.PURCHASED,
                ElectricityAttribute.ORDINARY,
                ElectricityProofType.NONE,
                ElectricityProofStatus.NOT_PROVIDED,
            ),
            (
                "electricity-c",
                "33",
                ElectricityAcquisitionMode.SELF_CONSUMED,
                ElectricityAttribute.NONFOSSIL,
                ElectricityProofType.MONTHLY_ORIGINAL_RECORD,
                ElectricityProofStatus.VALID,
            ),
            (
                "electricity-d",
                "44",
                ElectricityAcquisitionMode.PURCHASED,
                ElectricityAttribute.NONFOSSIL,
                ElectricityProofType.GEC,
                ElectricityProofStatus.VALID,
            ),
        )
        for row, values in zip(self.page._electricity_rows, expected):
            detail_id, amount, acquisition, attribute, proof_type, proof_status = values
            row.detail_id.setText(detail_id)
            row.amount.setText(amount)
            row.acquisition.setCurrentIndex(row.acquisition.findData(acquisition))
            row.attribute.setCurrentIndex(row.attribute.findData(attribute))
            row.proof_type.setCurrentIndex(row.proof_type.findData(proof_type))
            row.proof_status.setCurrentIndex(row.proof_status.findData(proof_status))
        row_keys = [row.row_key for row in self.page._electricity_rows]
        self.assertEqual(len(set(row_keys)), 3)
        self.assertEqual(len({row.objectName() for row in self.page._electricity_rows}), 3)

        first_unit_id = self.page._unit().unit_id
        with (
            patch("packages.ui.carbon_material_page.QInputDialog.getItem", return_value=("生产工序", True)),
            patch("packages.ui.carbon_material_page.QInputDialog.getText", return_value=("切换测试单元", True)),
        ):
            self.page._add_accounting_unit()
        self.page.unit_selector.setCurrentIndex(self.page.unit_selector.findData(first_unit_id))
        self.assertTrue(self.page._save_project())

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        self.page._open_selected_project()
        first_index = self.page.unit_selector.findData(first_unit_id)
        self.page.unit_selector.setCurrentIndex(first_index)
        self.assertEqual([row.row_key for row in self.page._electricity_rows], row_keys)
        actual = tuple(
            (
                row.detail_id.text(),
                row.amount.text(),
                row.acquisition.currentData(),
                row.attribute.currentData(),
                row.proof_type.currentData(),
                row.proof_status.currentData(),
            )
            for row in self.page._electricity_rows
        )
        self.assertEqual(actual, expected)
        self.assertEqual(len({row.detail_id.text() for row in self.page._electricity_rows}), 3)

    def test_multi_process_and_energy_lines_keep_identity_after_project_reopen(self) -> None:
        self.page.project_name.setText("多实例项目")
        self.page.enterprise_name.setText("多实例企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page._source_statuses["CAR-SRC-CALCINATION-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-CALCINATION-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        first, = self.page._process_rows["calcination"]
        first["fields"]["gc"].setText("100")
        second = self.page._add_process_row("calcination")
        second["fields"]["gc"].setText("200")
        third = self.page._add_process_row("calcination")
        third["fields"]["gc"].setText("300")
        first_id = str(first["instance_id"])
        third_id = str(third["instance_id"])
        self.page._remove_process_row("calcination", str(second["instance_id"]))

        self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-PURCHASED-HEAT-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        self.page._fields["heat_id"].setText("heat-source-a")
        self.page._fields["heat_amount"].setText("10")
        self.page.heat_measured_factor.setText("0.11")
        self.page.heat_factor_source_reference.setText("热力实测-A")
        second_heat = self.page._add_heat_row("heat", line_id="heat-source-b")
        second_heat["amount"].setText("20")
        second_heat["measured"].setText("0.20")
        second_heat["source"].setText("热力实测-B")

        self.page._source_statuses["CAR-SRC-EXPORTED-ELECTRICITY-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-EXPORTED-ELECTRICITY-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        self.page._output_electricity_rows[0]["id"].setText("power-source-a")
        self.page._output_electricity_rows[0]["amount"].setText("5")
        self.page._output_electricity_rows[0]["measured"].setText("0.50")
        self.page._output_electricity_rows[0]["source"].setText("电力实测-A")
        second_power = self.page._add_output_electricity_row(line_id="power-source-b")
        second_power["amount"].setText("8")
        second_power["measured"].setText("0.25")
        second_power["source"].setText("电力实测-B")
        self.assertTrue(self.page._save_project())
        project_id = self.page._workspace.project_id
        saved_workspace = self.project_service.get(project_id)
        self.assertIsNotNone(saved_workspace)
        assert saved_workspace is not None
        saved_state = saved_workspace.units[0].form_state
        self.assertEqual(saved_state.get("heat_line_ids", {}).get("heat"), ["heat-source-a", "heat-source-b"])
        self.assertEqual(saved_state.get("heatAmount_heat-source-b"), "20")

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        saved_index = self.page.saved_projects.findData(project_id)
        self.assertGreaterEqual(saved_index, 0)
        self.page.saved_projects.setCurrentIndex(saved_index)
        self.page._open_selected_project()

        restored_processes = self.page._process_rows["calcination"]
        self.assertEqual([str(row["instance_id"]) for row in restored_processes], [first_id, third_id])
        self.assertEqual([row["fields"]["gc"].text() for row in restored_processes], ["100", "300"])
        domain_input = self.page._input()
        self.assertEqual([item.instance_id for item in domain_input.calcinations], [first_id, third_id])
        self.assertEqual([str(item.gc.value) for item in domain_input.calcinations], ["100", "300"])
        self.assertEqual(
            [item.line_id for item in domain_input.purchased_heat], ["heat-source-a", "heat-source-b"],
            f"rows={[(row['id'].text(), row['amount'].text()) for row in self.page._heat_rows['heat']]}",
        )
        self.assertEqual([str(item.factor.value) for item in domain_input.purchased_heat], ["0.11", "0.20"])
        self.assertEqual([item.line_id for item in domain_input.exported_electricity], ["power-source-a", "power-source-b"])
        self.assertEqual([str(item.factor.value) for item in domain_input.exported_electricity], ["0.50", "0.25"])
        self.assertEqual(self.page._add_process_row("calcination")["instance_id"], "calcination-4")

    def test_report_data_and_reusable_evidence_restore_from_project_form_state(self) -> None:
        self.page.project_name.setText("报告资料恢复项目")
        self.page.enterprise_name.setText("报告资料企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.report_data_toggle.setChecked(True)
        self.page.reporting_fields["industry"].setText("炭素材料制造")
        self.page.reporting_fields["social_credit_code"].setText("913300000000000000")
        self.page.activity_evidence_fields["source_reference"].setText("燃料台账第2页")
        self.page.activity_evidence_fields["monitoring_method"].setText("连续计量")
        self.page.activity_evidence_sources[F01].setChecked(True)
        self.page.factor_evidence_fields["source_reference"].setText("燃料检测报告第4页")
        self.page.factor_evidence_fields["testing_method"].setText("实验室检测")
        self.page.factor_evidence_sources[F01].setChecked(True)
        self.assertTrue(self.page._save_project())
        project_id = self.page._workspace.project_id

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        saved_index = self.page.saved_projects.findData(project_id)
        self.assertGreaterEqual(saved_index, 0)
        self.page.saved_projects.setCurrentIndex(saved_index)
        self.page._open_selected_project()

        self.assertTrue(self.page.report_data_toggle.isChecked())
        self.assertEqual(self.page.reporting_fields["social_credit_code"].text(), "913300000000000000")
        self.assertEqual(self.page.activity_evidence_fields["source_reference"].text(), "燃料台账第2页")
        self.assertTrue(self.page.activity_evidence_sources[F01].isChecked())
        input_value = self.page._input()
        self.assertEqual(input_value.reporting_data.industry, "炭素材料制造")
        self.assertEqual(input_value.reporting_data.activity_evidence[0].source_reference, "燃料台账第2页")
        self.assertEqual(input_value.reporting_data.measured_factor_evidence[0].testing_method, "实验室检测")
        self.assertEqual(input_value.reporting_data.activity_evidence[0].source_ids, (F01,))

    def test_legacy_singleton_project_and_v1_fingerprint_migrate_without_stale_result(self) -> None:
        self.page.project_name.setText("旧版单过程项目")
        self.page.enterprise_name.setText("旧版单过程企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page._source_statuses["CAR-SRC-CALCINATION-001"].setCurrentIndex(
            self.page._source_statuses["CAR-SRC-CALCINATION-001"].findData(EmissionSourceStatus.INVOLVED)
        )
        for field, value in {
            "gc": "100", "wfc": "0.008", "cc": "70", "ucc": "5", "du": "1",
            "wfc_c": "0.002", "wvar": "0.10", "wvar_c": "0.02",
        }.items():
            self.page._fields[f"calcination.{field}"].setText(value)
        self.page._run_calculation()
        self.assertEqual(len(self.records.list_all()), 1)
        historical_record = self.records.list_all()[0]
        historical_result = self.page._unit().result_snapshot
        self.assertIsNotNone(historical_result)

        workspace = self.project_service.get(self.page._workspace.project_id)
        self.assertIsNotNone(workspace)
        assert workspace is not None
        unit = workspace.units[0]
        legacy_state = dict(unit.form_state)
        for key in (
            "business_fingerprint_version", "process_instances",
            "exported_electricity_line_ids", "heat_line_ids",
            "calcination_carbonOutputIncludedInInput", "baking_carbonOutputIncludedInInput",
            "graphitization_furnaceLossIncluded", "exportedElectricityFactorSelector",
            "exportedElectricityMeasuredFactor", "exportedElectricityFactorSource",
            "exportedHeatFactorSelector", "exportedHeatFactorReasonInput",
            "exportedHeatMeasuredFactorInput", "exportedHeatFactorSourceReferenceInput",
        ):
            legacy_state.pop(key, None)
        legacy_fingerprint = self.page._fingerprint_state(legacy_state)
        legacy_unit = replace(unit, form_state=legacy_state, input_fingerprint=legacy_fingerprint)
        self.project_service.save(replace(workspace, units=(legacy_unit,)))
        project_id = workspace.project_id

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        saved_index = self.page.saved_projects.findData(project_id)
        self.assertGreaterEqual(saved_index, 0)
        self.page.saved_projects.setCurrentIndex(saved_index)
        self.page._open_selected_project()

        restored_input = self.page._input()
        self.assertEqual(len(restored_input.calcinations), 1)
        self.assertEqual(str(restored_input.calcinations[0].gc.value), "100")
        self.assertNotEqual(self.page._unit().input_fingerprint, legacy_fingerprint)
        self.assertEqual(self.page._unit().result_snapshot, historical_result)
        self.assertIn("上次成功结果", self.page.unit_result_summary.text())
        self.assertFalse(self.page.result_card.isHidden())
        self.assertEqual(self.records.list_all(), (historical_record,))

    def test_equal_fuel_values_with_enterprise_source_remain_measured_and_stable(self) -> None:
        self.page.project_name.setText("实测参数来源项目")
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
        row.path.setCurrentIndex(row.path.findData(FuelPath.HEAT))
        row.activity.setText("10")
        row.source_reference.setText("企业检测报告-EQUAL-01")
        before_row_key = row.row_key
        before = self.page._fuel()[0]
        self.assertIs(before.carbon_content.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(before.oxidation_rate.source_kind, ParameterSourceKind.MEASURED)
        self.assertIn("企业实测", row.parameter_summary.text())
        self.assertEqual(self.page._capture_form_state()["fuel_rows"][0]["parameter_source"], "MEASURED")
        self.assertTrue(self.page._save_project())

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        self.page._open_selected_project()
        restored_row = self.page._fuel_rows[0]
        after = self.page._fuel()[0]
        self.assertEqual(restored_row.row_key, before_row_key)
        self.assertEqual(restored_row.source_reference.text(), "企业检测报告-EQUAL-01")
        self.assertEqual(restored_row.parameter_source, "MEASURED")
        self.assertEqual(after.carbon_content.parameter_id, before.carbon_content.parameter_id)
        self.assertEqual(after.oxidation_rate.parameter_id, before.oxidation_rate.parameter_id)
        self.assertIs(after.carbon_content.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(after.oxidation_rate.source_kind, ParameterSourceKind.MEASURED)

    def test_changed_input_marks_result_stale_after_switch_save_and_reopen(self) -> None:
        self.page.project_name.setText("结果过期项目")
        self.page.enterprise_name.setText("结果过期企业")
        self.page.boundary_confirmed.setChecked(True)
        self._enable_fuel()
        fuel = self.page._fuel_rows[0]
        fuel.activity.setText("10")
        fuel.carbon.setText("0.2")
        fuel.oxidation.setText("98")
        fuel.source_reference.setText("结果过期检测报告")
        self.page._run_calculation()
        self.assertEqual(len(self.records.list_all()), 1)
        first_unit_id = self.page._unit().unit_id
        persisted = self.project_service.get(self.page._workspace.project_id)
        self.assertIsNotNone(persisted)
        assert persisted is not None
        self.assertEqual(persisted.units[0].record_ids, (self.records.list_all()[0].record_id,))

        fuel.activity.setText("12")
        self.assertIn("上一计算结果已过期", self.page.unit_result_summary.text())
        with (
            patch("packages.ui.carbon_material_page.QInputDialog.getItem", return_value=("生产工序", True)),
            patch("packages.ui.carbon_material_page.QInputDialog.getText", return_value=("过期状态切换单元", True)),
        ):
            self.page._add_accounting_unit()
        self.page.unit_selector.setCurrentIndex(self.page.unit_selector.findData(first_unit_id))
        self.assertIn("上一计算结果已过期", self.page.unit_result_summary.text())
        self.assertTrue(self.page._save_project())

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        self.page = self._new_page()
        self.page._open_selected_project()
        self.page.unit_selector.setCurrentIndex(self.page.unit_selector.findData(first_unit_id))
        self.assertIn("上一计算结果已过期", self.page.unit_result_summary.text())
        self.assertTrue(self.page.result_card.isHidden())

    def test_report_only_change_keeps_calculation_result_and_new_record_freezes_updated_details(self) -> None:
        self.page.project_name.setText("报告资料变化项目")
        self.page.enterprise_name.setText("报告资料变化企业")
        self.page.boundary_confirmed.setChecked(True)
        self._enable_fuel()
        fuel = self.page._fuel_rows[0]
        fuel.activity.setText("10")
        fuel.carbon.setText("0.2")
        fuel.oxidation.setText("98")
        fuel.source_reference.setText("报告资料变化测试燃料实测报告")
        self.page.reporting_fields["industry"].setText("首次填写行业")
        self.page._run_calculation()
        first_record = self.records.list_all()[0]
        first_result = self.page._unit().result_snapshot
        first_total = first_record.calculation_result.total_amount
        first_reporting = self.records.get_reporting_snapshot(first_record.record_id)
        self.assertEqual(first_reporting["industry"], "首次填写行业")

        self.page.reporting_fields["industry"].setText("更新后的行业信息")
        self.assertFalse(self.page._calculation_result_is_stale(self.page._unit()))
        self.assertFalse(self.page.result_card.isHidden())
        self.assertIn("报告资料已修改", self.page.unit_result_summary.text())
        self.assertIn("报告资料已修改", self.page.report_changes_status.text())
        self.assertEqual(self.page._unit().result_snapshot["total"], first_result["total"])
        self.assertEqual(self.records.list_all(), (first_record,))

        self.assertTrue(self.page._save_project())
        self.page._run_calculation()
        records = self.records.list_all()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].calculation_result.total_amount, first_total)
        self.assertEqual(self.records.get_reporting_snapshot(first_record.record_id)["industry"], "首次填写行业")
        self.assertEqual(self.records.get_reporting_snapshot(records[1].record_id)["industry"], "更新后的行业信息")

    def test_record_link_save_does_not_persist_other_units_unfinished_input(self) -> None:
        self.page.project_name.setText("关联最小保存项目")
        first_unit_id = self.page._unit().unit_id
        with (
            patch("packages.ui.carbon_material_page.QInputDialog.getItem", return_value=("生产工序", True)),
            patch("packages.ui.carbon_material_page.QInputDialog.getText", return_value=("未完成单元", True)),
        ):
            self.page._add_accounting_unit()
        second_unit_id = self.page._unit().unit_id
        self.assertTrue(self.page._save_project())
        self.page.enterprise_name.setText("不得静默保存的未完成输入")
        self.page.unit_selector.setCurrentIndex(self.page.unit_selector.findData(first_unit_id))

        self.page.enterprise_name.setText("已完成核算企业")
        self.page.boundary_confirmed.setChecked(True)
        self._enable_fuel()
        fuel = self.page._fuel_rows[0]
        fuel.activity.setText("10")
        fuel.carbon.setText("0.2")
        fuel.oxidation.setText("98")
        fuel.source_reference.setText("完成单元检测报告")
        self.page._run_calculation()
        self.assertEqual(len(self.records.list_all()), 1)

        persisted = self.project_service.get(self.page._workspace.project_id)
        self.assertIsNotNone(persisted)
        assert persisted is not None
        first = next(unit for unit in persisted.units if unit.unit_id == first_unit_id)
        second = next(unit for unit in persisted.units if unit.unit_id == second_unit_id)
        self.assertEqual(first.record_ids, (self.records.list_all()[0].record_id,))
        self.assertNotEqual(
            second.form_state.get("enterpriseNameInput"),
            "不得静默保存的未完成输入",
        )
        self.assertTrue(self.page._project_dirty)

    def test_corrupt_project_json_shows_safe_error_on_open_and_page_startup(self) -> None:
        self.page.project_name.setText("损坏项目提示")
        self.assertTrue(self.page._save_project())
        project_id = self.page._workspace.project_id
        connection = sqlite3.connect(self.root / "projects.sqlite")
        try:
            connection.execute(
                "UPDATE accounting_units SET form_state_json=? WHERE project_id=?",
                ("{broken-json", project_id),
            )
            connection.commit()
        finally:
            connection.close()

        with patch("packages.ui.carbon_material_page.QMessageBox.critical") as critical:
            self.page._open_selected_project()
        critical.assert_called_once()
        self.assertIn("打开项目失败", self.page.project_save_status.text())

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        with patch("packages.ui.carbon_material_page.QMessageBox.critical") as critical:
            self.page = self._new_page()
        critical.assert_called_once()
        self.assertEqual(self.page.saved_projects.count(), 0)
        self.assertIn("读取已保存项目失败", self.page.project_save_status.text())

    def test_multiple_fuels_and_unit_results_restore_independently_after_reopen(self) -> None:
        self.page.project_name.setText("多单元燃料企业")
        self.page.enterprise_name.setText("多单元燃料企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        self.page.period_type.setCurrentIndex(2)
        self._enable_fuel()

        first = self.page._fuel_rows[0]
        first.fuel_type.setCurrentIndex(first.fuel_type.findData(FuelType.DIESEL))
        first.path.setCurrentIndex(first.path.findData(FuelPath.VOLUME))
        first.activity.setText("10")
        first.carbon.setText("0.2")
        first.oxidation.setText("98")
        first.source_reference.setText("柴油检测报告-01")

        self.page.add_fuel_button.click()
        middle = self.page._fuel_rows[1]
        middle.fuel_type.setCurrentIndex(middle.fuel_type.findData(FuelType.COAL))
        middle.path.setCurrentIndex(middle.path.findData(FuelPath.MASS))
        middle.activity.setText("3")
        middle.carbon.setText("0.7")
        middle.oxidation.setText("95")
        middle.source_reference.setText("煤质检测报告-02")

        self.page.add_fuel_button.click()
        last = self.page._fuel_rows[2]
        last.fuel_type.setCurrentIndex(last.fuel_type.findData(FuelType.COKE_OVEN_GAS))
        last.path.setCurrentIndex(last.path.findData(FuelPath.HEAT))
        last.activity.setText("4")
        last.carbon.setText("0.03")
        last.oxidation.setText("97")
        last.source_reference.setText("焦炉煤气检测报告-03")
        middle.remove_button.click()
        self.assertEqual(len(self.page._fuel_rows), 2)
        self.assertEqual([row.activity.text() for row in self.page._fuel_rows], ["10", "4"])
        fuel_inputs = self.page._fuel()
        self.assertEqual([fuel.fuel_type for fuel in fuel_inputs], [FuelType.DIESEL, FuelType.COKE_OVEN_GAS])
        self.assertEqual(len({fuel.fuel_id for fuel in fuel_inputs}), 2)

        first_period = self.page._period()
        self.page._run_calculation()
        self.assertFalse(self.page.result_card.isHidden())
        self.assertEqual(len(self.records.list_all()), 1)
        first_unit_id = self.page._unit().unit_id
        first_result = self.page._unit().result_snapshot
        self.assertIsNotNone(first_result)

        with (
            patch("packages.ui.carbon_material_page.QInputDialog.getItem", return_value=("生产工序", True)),
            patch("packages.ui.carbon_material_page.QInputDialog.getText", return_value=("石墨化工序", True)),
        ):
            self.page._add_accounting_unit()
        self.assertNotEqual(self.page._unit().unit_id, first_unit_id)
        self.page.enterprise_name.setText("多单元燃料企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        self.page.period_type.setCurrentIndex(13)
        self.page.period_start.setDate(QDate(2026, 3, 14))
        self.page.period_end.setDate(QDate(2026, 8, 22))
        self._enable_fuel()
        second_fuel = self.page._fuel_rows[0]
        second_fuel.fuel_type.setCurrentIndex(second_fuel.fuel_type.findData(FuelType.DIESEL))
        second_fuel.path.setCurrentIndex(second_fuel.path.findData(FuelPath.VOLUME))
        second_fuel.activity.setText("1")
        second_fuel.carbon.setText("0.3")
        second_fuel.oxidation.setText("90")
        second_fuel.source_reference.setText("石墨化工序燃料检测报告")
        self.page._run_calculation()
        self.assertFalse(
            self.page.result_card.isHidden(),
            [self.page.validation_list.item(i).text() for i in range(self.page.validation_list.count())],
        )
        self.assertEqual(len(self.records.list_all()), 2)
        second_unit_id = self.page._unit().unit_id
        second_result = self.page._unit().result_snapshot
        self.assertIsNotNone(second_result)
        self.assertNotEqual(first_result["total"], second_result["total"])

        self.assertTrue(self.page._save_project())
        persisted = self.project_service.get(self.page._workspace.project_id)
        self.assertIsNotNone(persisted)
        assert persisted is not None
        self.assertEqual(persisted.active_unit_id, second_unit_id)
        self.assertEqual(len(persisted.units), 2)
        first_saved = next(unit for unit in persisted.units if unit.unit_id == first_unit_id)
        self.assertEqual(first_saved.result_snapshot, first_result)
        self.assertEqual(len(first_saved.form_state["fuel_rows"]), 2)

        self.page.close()
        self.page.deleteLater()
        self.application.processEvents()
        reopened = self._new_page()
        self.addCleanup(reopened.deleteLater)
        self.page = reopened
        self.assertEqual(self.page.saved_projects.count(), 1)
        self.page._open_selected_project()
        self.assertEqual(self.page._unit().unit_id, second_unit_id)
        self.assertIs(self.page._period().period_type, PeriodType.CUSTOM)
        self.assertEqual(self.page._period().start.isoformat(), "2026-03-14")
        self.assertEqual(self.page._period().end.isoformat(), "2026-08-22")
        self.assertFalse(self.page.result_card.isHidden())
        self.assertEqual(self.page._unit().result_snapshot, second_result)

        first_index = self.page.unit_selector.findData(first_unit_id)
        self.page.unit_selector.setCurrentIndex(first_index)
        self.assertEqual(self.page._period(), first_period)
        self.assertEqual(len(self.page._fuel_rows), 2)
        self.assertEqual([row.activity.text() for row in self.page._fuel_rows], ["10", "4"])
        self.assertEqual(self.page._unit().result_snapshot, first_result)
        self.assertEqual(self.page.result_total.text(), f"温室气体排放总量：{first_result['total_display']}")
        self.assertEqual(len(self.records.list_all()), 2)

        second_index = self.page.unit_selector.findData(second_unit_id)
        self.page.unit_selector.setCurrentIndex(second_index)
        with patch(
            "packages.ui.carbon_material_page.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.page._delete_accounting_unit()
        self.assertEqual(len(self.page._workspace.units), 1)
        self.assertTrue(self.page._save_project())
        self.assertEqual(len(self.records.list_all()), 2)
        self.assertEqual(len(self.project_service.get(self.page._workspace.project_id).units), 1)


if __name__ == "__main__":
    unittest.main()
