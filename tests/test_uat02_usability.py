"""Focused offscreen probes for the UAT02 accounting usability repairs."""

from __future__ import annotations

import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material import EmissionSourceStatus, FuelPath, FuelType
from packages.ui.carbon_material_page import _display_amount, _display_compact_decimal
from packages.ui.record_experience import format_amount
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import tree_texts


class UAT02UsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls.temp_directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, cls.catalog_path)
        cls.catalog_service = CatalogQueryService(
            SQLiteCatalogRepository(cls.catalog_path),
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
        self.shell = self.window.centralWidget()
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.page = self.shell.pages[AppRoute.NEW_ACCOUNTING]

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def test_closed_selectors_and_year_do_not_consume_page_wheel(self) -> None:
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.NATURAL_GAS))
        scrollbar = self.shell.main_scroll_area.verticalScrollBar()
        scrollbar.setValue(min(200, scrollbar.maximum()))
        before_scroll = scrollbar.value()
        before_fuel = row.fuel_type.currentData()
        wheel = QWheelEvent(
            QPointF(5, 5), QPointF(5, 5), QPoint(), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollUpdate, False,
        )
        QApplication.sendEvent(row.fuel_type, wheel)
        self.assertEqual(row.fuel_type.currentData(), before_fuel)
        self.assertGreaterEqual(scrollbar.value(), before_scroll)
        year = self.page.period_year.value()
        QApplication.sendEvent(self.page.period_year, QWheelEvent(
            QPointF(5, 5), QPointF(5, 5), QPoint(), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollUpdate, False,
        ))
        self.assertEqual(self.page.period_year.value(), year)
        self.page.period_year.setFocus()
        QTest.keyClick(self.page.period_year, Qt.Key.Key_Up)
        self.assertEqual(self.page.period_year.value(), year + 1)
        row.fuel_type.setFocus()
        QTest.keyClick(row.fuel_type, Qt.Key.Key_Down)
        self.assertNotEqual(row.fuel_type.currentData(), before_fuel)
        before_popup = row.fuel_type.currentIndex()
        row.fuel_type.showPopup()
        self.application.processEvents()
        self.assertTrue(row.fuel_type.view().isVisible())
        QTest.keyClick(row.fuel_type.view(), Qt.Key.Key_Down)
        QTest.keyClick(row.fuel_type.view(), Qt.Key.Key_Return)
        self.assertNotEqual(row.fuel_type.currentIndex(), before_popup)

    def test_twenty_dynamic_rows_expand_and_shrink_scroll_host(self) -> None:
        source = self.page._source_statuses["CAR-SRC-FUEL-001"]
        source.setCurrentIndex(source.findData(EmissionSourceStatus.INVOLVED))
        self.application.processEvents()
        baseline = self.shell.scroll_host.height()
        for _ in range(20):
            self.page._add_fuel_row()
        self.application.processEvents()
        QTest.qWait(1)
        grown = self.shell.scroll_host.height()
        self.assertGreater(grown, baseline)
        self.assertGreater(self.shell.main_scroll_area.verticalScrollBar().maximum(), 0)
        middle = self.page._fuel_rows[10]
        self.page._remove_fuel_row(middle)
        self.application.processEvents()
        QTest.qWait(1)
        self.assertEqual(len(self.page._fuel_rows), 20)
        self.assertLess(self.shell.scroll_host.height(), grown)

    def test_fgd_id_stays_internal_and_process_addition_is_secondary(self) -> None:
        component = self.page._process_rows["fgd"][0]["components"][0]
        self.assertTrue(component["_component_id"].isHidden())
        self.assertEqual(component["_component_id"].text(), component["component_id"])
        button = self.page.findChild(QWidget, "add_calcination_instance")
        self.assertTrue(button.isHidden())
        self.page.manage_process_button.click()
        self.assertFalse(button.isHidden())

    def test_blank_enterprise_factor_source_warns_but_missing_value_blocks(self) -> None:
        source = self.page._source_statuses["CAR-SRC-FUEL-001"]
        source.setCurrentIndex(source.findData(EmissionSourceStatus.INVOLVED))
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.OTHER))
        row.custom_name.setText("测试燃料")
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.activity.setText("1")
        self.page._run_calculation()
        self.assertTrue(self.page.result_card.isHidden())
        self.assertIn("未完成：请修正", self.page.calculation_status_hint.text())
        self.assertIn("单位含碳量", "\n".join(tree_texts(self.page.validation_list)))
        row.carbon.setText("0.02")
        row.oxidation.setText("98")
        for combo in (row.carbon_source, row.oxidation_source):
            combo.setCurrentIndex(combo.findData("MEASURED"))
        self.page._run_calculation()
        self.assertFalse(self.page.result_card.isHidden(), tree_texts(self.page.validation_list))
        record = self.page.record_repository.list_all()[0]
        self.assertEqual(record.status.value, "COMPLETED_WITH_WARNINGS")
        self.assertTrue(any(snapshot.source_id is None for snapshot in record.parameter_snapshots))
        self.assertEqual(row.source_reference.text(), "")

    def test_failed_calculation_focuses_the_specific_fuel_field(self) -> None:
        source = self.page._source_statuses["CAR-SRC-FUEL-001"]
        source.setCurrentIndex(source.findData(EmissionSourceStatus.INVOLVED))
        row = self.page._fuel_rows[0]
        row.fuel_type.setCurrentIndex(row.fuel_type.findData(FuelType.OTHER))
        row.custom_name.setText("测试燃料")
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.activity.setText("1")
        self.page.quick_calculate_button.click()
        self.application.processEvents()
        self.application.processEvents()
        self.assertTrue(self.page._source_cards["CAR-SRC-FUEL-001"].is_expanded)
        self.assertIn("未完成：请修正", self.page.calculation_status_hint.text())
        self.assertIs(self.application.focusWidget(), row.carbon)
        self.assertEqual(self.page.record_repository.list_all(), ())

    def test_small_display_value_is_not_zeroed_or_written_to_input(self) -> None:
        value = Decimal("0.000023456789")
        self.assertNotIn("0.00 tCO₂", _display_amount(value, "tCO2"))
        self.assertNotEqual(format_amount(value), "0.00 tCO₂")
        self.assertEqual(value, Decimal("0.000023456789"))
        self.assertEqual(_display_compact_decimal(Decimal("150")), "150.00")

    def test_record_audit_is_not_part_of_ordinary_layout(self) -> None:
        records = self.shell.pages[AppRoute.RECORDS]
        self.assertTrue(records.audit_dialog.isHidden())
        self.assertIs(records.detail_text.parentWidget(), records.audit_dialog)
        self.assertIsNotNone(records.audit_button)
        records.audit_button.click()
        self.application.processEvents()
        self.assertTrue(records.audit_dialog.isVisible())
        records.audit_dialog.close()


if __name__ == "__main__":
    unittest.main()
