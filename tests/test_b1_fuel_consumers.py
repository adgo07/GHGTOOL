"""R11 fuel consumer expectations: approved corrections and retained input."""
import gc
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from packages.application.catalog_queries import CatalogQueryService
from packages.core.models import DomainValidationError
from packages.persistence import build_catalog_database, SQLiteCatalogRepository, InMemoryRecordRepository
from packages.standards.carbon_material import FuelPath, FuelType, ParameterSourceKind
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage


class FuelConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.directory = tempfile.TemporaryDirectory()
        cls.catalog = CatalogQueryService(SQLiteCatalogRepository(
            build_catalog_database(output_path=Path(cls.directory.name) / "catalog.sqlite")))

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        cls.directory.cleanup()

    def setUp(self):
        self.records = InMemoryRecordRepository()
        self.page = CarbonMaterialAccountingPage(catalog_service=self.catalog, record_repository=self.records)
        self.row = self.page._fuel_rows[0]
        self.select(FuelType.NATURAL_GAS)

    def tearDown(self):
        self.page.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def select(self, kind):
        self.row.fuel_type.setCurrentIndex(self.row.fuel_type.findData(kind))
        self.row.fuel_type.confirm_name(force=True)

    def source(self, combo, kind):
        index = combo.findData(kind)
        self.assertGreaterEqual(index, 0, kind)
        combo.setCurrentIndex(index)

    @staticmethod
    def enabled_sources(combo):
        from PySide6.QtCore import Qt
        return {combo.itemData(index) for index in range(combo.count())
                if combo.model().flags(combo.model().index(index, 0)) & Qt.ItemFlag.ItemIsEnabled
                and not combo.view().isRowHidden(index)}

    def test_bound_lhv_fch_and_oxidation_allow_only_default_or_measured(self):
        for combo in (self.row.lhv_source, self.row.carbon_source, self.row.oxidation_source):
            self.assertEqual(self.enabled_sources(combo), {"STANDARD_DEFAULT", "MEASURED"})

    def test_custom_lhv_fch_and_oxidation_start_measured_and_empty(self):
        self.row.fuel_type.setEditText("企业专用混合燃料")
        self.row.fuel_type.confirm_name(force=True)
        for combo, edit in ((self.row.lhv_source, self.row.lower_heating_value),
                            (self.row.carbon_source, self.row.carbon),
                            (self.row.oxidation_source, self.row.oxidation)):
            self.assertEqual(self.enabled_sources(combo), {"MEASURED"})
            self.assertEqual(combo.currentData(), "MEASURED")
            self.assertEqual(edit.text(), "")
            self.assertFalse(edit.isReadOnly())

    def test_direct_calculated_uses_its_own_source_and_quantity(self):
        self.row.carbon_basis.setCurrentIndex(self.row.carbon_basis.findData("DIRECT"))
        self.assertEqual(self.enabled_sources(self.row.direct_carbon_source), {"CALCULATED", "MEASURED"})
        self.source(self.row.direct_carbon_source, "CALCULATED")
        self.row.carbon_direct.setText("0.71234567890123456789")
        self.row.activity.setText("2")
        value = self.page._fuel()[0]
        self.assertIs(value.carbon_content.source_kind, ParameterSourceKind.CALCULATED)
        self.assertEqual(str(value.carbon_content.value), "0.71234567890123456789")
        self.assertEqual(value.carbon_content.unit, "tC/10^4Nm3")
        self.assertIsNone(value.lower_heating_value)
        self.assertEqual(self.records.list_all(), ())

    def test_catalog_name_without_applicable_binding_cannot_offer_defaults(self):
        from dataclasses import replace
        from datetime import timedelta
        from unittest.mock import Mock
        # Expire real Catalog bindings before the actual reporting period.
        # Returning None from a presentation helper is not proof of absence.
        expired = Mock(wraps=self.catalog.repository)
        expired.list_reference_data_bindings.return_value = tuple(
            replace(item, valid_to=self.page._period().start - timedelta(days=1))
            for item in self.catalog.repository.list_reference_data_bindings())
        previous = self.page
        self.page = CarbonMaterialAccountingPage(
            catalog_service=CatalogQueryService(expired), record_repository=self.records)
        previous.deleteLater()
        self.row = self.page._fuel_rows[0]
        self.select(FuelType.DIESEL)
        for combo, edit in ((self.row.lhv_source, self.row.lower_heating_value),
                            (self.row.carbon_source, self.row.carbon),
                            (self.row.oxidation_source, self.row.oxidation)):
            self.assertEqual(self.enabled_sources(combo), {"MEASURED"})
            self.assertEqual(combo.currentData(), "MEASURED")
            self.assertEqual(edit.text(), "")
            self.assertFalse(edit.isReadOnly())

    def test_same_confirmed_identity_preserves_parameters_basis_and_sources(self):
        self.source(self.row.lhv_source, "MEASURED")
        self.row.lower_heating_value.setText("400.1234567890123456789")
        self.row.carbon_basis.setCurrentIndex(self.row.carbon_basis.findData("DIRECT"))
        self.row.fuel_type.confirm_name(force=True)
        self.assertEqual(self.row.lhv_source.currentData(), "MEASURED")
        self.assertEqual(self.row.lower_heating_value.text(), "400.1234567890123456789")
        self.assertEqual(self.row.carbon_basis.currentData(), "DIRECT")

    def test_source_round_trip_and_restore_keep_explicit_measured_draft(self):
        self.source(self.row.carbon_source, "MEASURED")
        self.assertEqual(self.row.carbon.text(), "")
        self.row.carbon.setText("0.0161234567890123456789")
        self.source(self.row.carbon_source, "STANDARD_DEFAULT")
        self.assertEqual(self.row.carbon.text(), "0.0153")
        state = json.loads(json.dumps(self.page._capture_form_state()))
        self.page._restore_form_state(state)
        self.row = self.page._fuel_rows[0]
        self.source(self.row.carbon_source, "MEASURED")
        self.assertEqual(self.row.carbon.text(), "0.0161234567890123456789")
        self.assertFalse(self.row.carbon.isReadOnly())

    def test_path_change_does_not_reinterpret_measured_lhv(self):
        self.source(self.row.lhv_source, "MEASURED")
        self.row.lower_heating_value.setText("400.123456789")
        self.row.path.setCurrentIndex(self.row.path.findData(FuelPath.MASS))
        self.assertNotEqual(self.row.lower_heating_value.text(), "400.123456789")
        self.source(self.row.lhv_source, "MEASURED")
        self.row.lower_heating_value.setText("40.987654321")
        self.row.path.setCurrentIndex(self.row.path.findData(FuelPath.VOLUME))
        self.source(self.row.lhv_source, "MEASURED")
        self.assertEqual(self.row.lower_heating_value.text(), "400.123456789")

    def test_switching_same_unit_fuel_keeps_activity_with_original_identity(self):
        self.select(FuelType.DIESEL)
        self.row.activity.setText("42.123456789")
        self.select(FuelType.GASOLINE)
        self.assertEqual(self.row.path.currentData(), FuelPath.MASS)
        self.assertEqual(self.row.activity.text(), "")
        self.select(FuelType.DIESEL)
        self.row.restore_activity_button.click()
        self.assertEqual(self.row.activity.text(), "42.123456789")

    def test_illegal_old_calculated_fch_remains_visible_and_can_be_corrected(self):
        state = self.page._capture_form_state()
        state["fuel_rows"][0].update(carbon_source_kind="CALCULATED", carbon="0.019123456789")
        self.page._restore_form_state(state)
        self.row = self.page._fuel_rows[0]
        self.assertEqual(self.page._fuel_source_mode(self.row, "carbon"), "CALCULATED")
        self.assertEqual(self.row.carbon.text(), "0.019123456789")
        self.source(self.row.carbon_source, "MEASURED")
        self.assertEqual(self.row.carbon.text(), "")
        self.assertFalse(self.row.carbon.isReadOnly())
        self.row.carbon.setText("0.016")
        self.assertEqual(self.page._fuel_source_mode(self.row, "carbon"), "MEASURED")

    def test_pending_name_cannot_calculate_with_previous_identity(self):
        self.row.activity.setText("1")
        self.row.fuel_type.setEditText("尚未确认的燃料")
        with self.assertRaisesRegex(DomainValidationError, "确认燃料名称"):
            self.page._fuel()
        self.assertEqual(self.records.list_all(), ())

    def test_escape_cancels_pending_name_without_reconfirming_identity(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        self.source(self.row.carbon_source, "MEASURED")
        self.row.carbon.setText("0.016123456789")
        self.row.activity.setText("1")
        self.row.fuel_type.setEditText("应取消的新燃料")
        QTest.keyClick(self.row.fuel_type.lineEdit(), Qt.Key.Key_Escape)
        self.assertEqual(self.row.fuel_type.currentText(), self.row._committed_name)
        self.assertEqual(self.row.fuel_type.currentText(), "天然气")
        self.assertEqual(self.row.carbon_source.currentData(), "MEASURED")
        self.assertEqual(self.row.carbon.text(), "0.016123456789")
        self.assertEqual(self.page._fuel()[0].fuel_type, FuelType.NATURAL_GAS)
