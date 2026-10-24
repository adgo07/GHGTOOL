"""Focused offscreen probes for the UAT02 accounting usability repairs."""

from __future__ import annotations

import os
import tempfile
import time
from unittest.mock import patch
import unittest
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLineEdit, QPushButton, QWidget

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
from tests.ui_tree_helpers import dispose_test_widget, tree_texts


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
        dispose_test_widget(self.window)
        self.application.processEvents()

    def test_closed_selectors_and_year_do_not_consume_page_wheel(self) -> None:
        row = self.page._fuel_rows[0]
        natural_gas = row.fuel_type.findData(FuelType.NATURAL_GAS)
        row.fuel_type.setCurrentIndex(natural_gas)
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
        QTest.mouseClick(row.path, Qt.MouseButton.LeftButton)
        self.application.processEvents()
        self.assertTrue(row.path.view().isVisible())
        row.path.hidePopup()
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

        # Typing a name creates a draft until explicitly confirmed. Clicking
        # the editable area does not force the option popup; the arrow still
        # opens it so a Catalog choice remains selectable.
        line_edit = row.fuel_type.lineEdit()
        self.assertIsNotNone(line_edit)
        assert line_edit is not None
        committed_before_typing = row._committed_name
        line_edit.setText("测试燃料")
        self.assertEqual(row.fuel_type.currentText(), "测试燃料")
        self.assertEqual(row._committed_name, committed_before_typing)
        row.fuel_type.confirm_name(force=True)
        self.assertEqual(row._committed_name, "测试燃料")
        QTest.mouseClick(line_edit, Qt.MouseButton.LeftButton)
        self.application.processEvents()
        self.assertFalse(row.fuel_type.view().isVisible())
        QTest.mouseClick(
            row.fuel_type,
            Qt.MouseButton.LeftButton,
            pos=QPoint(row.fuel_type.width() - 5, row.fuel_type.height() // 2),
        )
        self.application.processEvents()
        self.assertTrue(row.fuel_type.view().isVisible())
        row.fuel_type.view().setCurrentIndex(row.fuel_type.model().index(natural_gas, 0))
        QTest.keyClick(row.fuel_type.view(), Qt.Key.Key_Return)
        self.assertEqual(row.fuel_type.currentIndex(), natural_gas)
        self.assertEqual(row.fuel_type.currentData(), FuelType.NATURAL_GAS)
        self.assertEqual(row._committed_name, "天然气")

    def test_accounting_page_event_filter_follows_page_visibility(self) -> None:
        self.assertTrue(self.page._application_event_filter_installed)
        self.shell.navigate(AppRoute.HOME)
        self.application.processEvents()
        self.assertFalse(self.page._application_event_filter_installed)

        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.assertTrue(self.page._application_event_filter_installed)

        self.window.close()
        self.application.processEvents()
        self.assertFalse(self.page._application_event_filter_installed)

    def test_twenty_dynamic_rows_expand_and_shrink_scroll_host(self) -> None:
        errors = []
        def settle_geometry():
            # Normal Qt events only: a real deadline and successive stable
            # observations, never a forced product/layout refresh.
            samples = []
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                self.application.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 5)
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                samples.append((self.shell.scroll_host.height(),
                    self.shell.main_scroll_area.verticalScrollBar().maximum(),
                    tuple(row.geometry().getRect() for row in self.page._fuel_rows)))
                self.assertEqual(errors, [], errors)
                if len(samples) >= 8 and samples[-3:] == [samples[-1]] * 3:
                    return samples[-1]
            self.fail(f"正常事件处理2秒内几何未收敛：height/scroll_max序列={[(x[0], x[1]) for x in samples]}; Qt异常={errors}")

        with patch("sys.excepthook", side_effect=lambda kind, value, trace: errors.append(f"{kind.__name__}: {value}")):
            self.page._source_toggle_buttons["fuel"].click()
            baseline = settle_geometry()[0]
            for _ in range(20):
                self.page._add_fuel_row()
            grown, grown_scroll, _ = settle_geometry()
            self.assertGreater(grown, baseline)
            self.assertGreater(grown_scroll, 0)
            middle = self.page._fuel_rows[10]
            expected_remaining = [row for row in self.page._fuel_rows if row is not middle]
            self.page._remove_fuel_row(middle)
            shrunk, shrunk_scroll, _ = settle_geometry()
            self.assertEqual(len(self.page._fuel_rows), 20)
            self.assertEqual(self.page._fuel_rows, expected_remaining)
            self.assertLess(shrunk, grown)
            self.assertLess(shrunk_scroll, grown_scroll)
            host = self.page.fuel_rows_host
            for index, row in enumerate(self.page._fuel_rows):
                self.assertTrue(host.rect().contains(row.geometry()))
                self.assertGreaterEqual(row.height(), row.minimumSizeHint().height())
                if index:
                    self.assertLess(self.page._fuel_rows[index - 1].geometry().bottom(), row.geometry().top())
                for control in row.findChildren(QWidget):
                    if isinstance(control, (QLineEdit, QComboBox, QAbstractButton)) and control.isVisibleTo(row):
                        self.assertTrue(control.parentWidget().rect().contains(control.geometry()),
                                        (control.objectName(), control.geometry(), control.parentWidget().size()))
            self.assertEqual(errors, [])

    def test_fgd_id_stays_internal_and_process_addition_is_secondary(self) -> None:
        component = self.page._process_rows["fgd"][0]["components"][0]
        self.assertTrue(component["_component_id"].isHidden())
        self.assertEqual(component["_component_id"].text(), component["component_id"])
        button = self.page.findChild(QWidget, "add_calcination_instance")
        self.assertTrue(button.isHidden())
        self.page.manage_process_button.click()
        self.assertFalse(button.isHidden())

    def test_blank_enterprise_factor_source_warns_but_missing_value_blocks(self) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_fuel")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        row = self.page._fuel_rows[0]
        row.fuel_type.setEditText("测试燃料")
        row.fuel_type.confirm_name(force=True)
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
        row.activity.setText("1")
        self.page._run_calculation()
        self.assertTrue(self.page.result_card.isHidden())
        self.assertIn("未完成：请修正", self.page.calculation_status_hint.text())
        self.assertIn("单位含碳量", "\n".join(tree_texts(self.page.validation_list)))
        row.carbon_direct.setText("0.02")
        row.oxidation.setText("98")
        row.direct_carbon_source.setCurrentIndex(row.direct_carbon_source.findData("MEASURED"))
        row.oxidation_source.setCurrentIndex(row.oxidation_source.findData("MEASURED"))
        self.page._run_calculation()
        self.assertFalse(self.page.result_card.isHidden(), tree_texts(self.page.validation_list))
        record = self.page.record_repository.list_all()[0]
        self.assertEqual(record.status.value, "COMPLETED_WITH_WARNINGS")
        self.assertTrue(any(
            snapshot.parameter_id.endswith("direct_carbon") and snapshot.source_id is None
            for snapshot in record.parameter_snapshots
        ))
        self.assertEqual(row.source_reference.text(), "")

    def test_failed_calculation_focuses_the_specific_fuel_field(self) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_fuel")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        row = self.page._fuel_rows[0]
        row.fuel_type.setEditText("测试燃料")
        row.fuel_type.confirm_name(force=True)
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
        row.activity.setText("1")
        self.page.quick_calculate_button.click()
        self.application.processEvents()
        self.application.processEvents()
        # PR59 deliberately waits for layout/range stability before focus.
        # Observe normal events within 100 ms; never force a product refresh.
        viewport = self.shell.main_scroll_area.viewport()
        deadline = time.monotonic() + 0.1
        while time.monotonic() < deadline:
            rectangle = QRect(row.carbon_direct.mapTo(viewport, QPoint()), row.carbon_direct.size())
            if (self.application.focusWidget() is row.carbon_direct
                    and viewport.rect().contains(rectangle)
                    and not self.shell._content_geometry_refresh_pending):
                break
            self.application.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 5)
        self.assertTrue(self.page._source_cards["CAR-SRC-FUEL-001"].is_expanded)
        self.assertIn("未完成：请修正", self.page.calculation_status_hint.text())
        self.assertIs(self.application.focusWidget(), row.carbon_direct)
        self.assertTrue(viewport.rect().contains(QRect(
            row.carbon_direct.mapTo(viewport, QPoint()), row.carbon_direct.size())))
        self.assertEqual(self.page.record_repository.list_all(), ())

    def test_small_display_value_is_not_zeroed_or_written_to_input(self) -> None:
        value = Decimal("0.000023456789")
        self.assertNotIn("0.00 tCO₂", _display_amount(value, "tCO2"))
        self.assertNotEqual(format_amount(value), "0.00 tCO₂")
        self.assertEqual(value, Decimal("0.000023456789"))
        self.assertEqual(_display_compact_decimal(Decimal("150")), "150.00")

    def test_record_audit_is_not_part_of_ordinary_layout(self) -> None:
        records = self.shell.pages[AppRoute.RECORDS]
        self.assertFalse(hasattr(records, "audit_dialog"))
        self.assertFalse(hasattr(records, "audit_button"))
        self.assertIsNone(records.findChild(QPushButton, "openRecordAuditButton"))
        self.assertEqual(records.detail_tabs.count(), 2)
        self.assertTrue(records.input_basis_view.isReadOnly())


if __name__ == "__main__":
    unittest.main()
