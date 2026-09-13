from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import (
    ElectricityAcquisitionMode,
    ElectricityAttribute,
)
from packages.standards.carbon_material import STANDARD_ID
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


class G06PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = create_main_window(
            AppConfig(), catalog_service=CatalogQueryService.empty()
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
