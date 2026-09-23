from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from packages.application import CatalogQueryService, ProjectWorkspaceService
from packages.core import PeriodType
from packages.persistence import SQLiteCatalogRepository, SQLiteProjectWorkspaceRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import EmissionSourceStatus, FuelPath, FuelType, InMemoryRecordRepository
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage


F01 = "CAR-SRC-FUEL-001"


class AccountingProjectUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
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
        self.assertEqual(self.page.result_total.text(), f"总排放量 ET：{first_result['total_display']}")
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
