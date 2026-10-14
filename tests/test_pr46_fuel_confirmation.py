"""Explicit name confirmation, reset, typed drafts and source presentation."""
import gc, os, tempfile, unittest
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QToolButton, QLineEdit
from packages.application.catalog_queries import CatalogQueryService
from packages.persistence import build_catalog_database, SQLiteCatalogRepository, InMemoryRecordRepository
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.standards.carbon_material import FuelType, FuelPath

class FuelConfirmationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.temp=tempfile.TemporaryDirectory()
        cls.catalog=CatalogQueryService(SQLiteCatalogRepository(build_catalog_database(output_path=Path(cls.temp.name)/"catalog.sqlite")))
    @classmethod
    def tearDownClass(cls):
        gc.collect(); cls.temp.cleanup()
    def setUp(self):
        self.page=CarbonMaterialAccountingPage(catalog_service=self.catalog,record_repository=InMemoryRecordRepository())
        self.row=self.page._fuel_rows[0]
    def tearDown(self):
        self.page.hide(); self.page.deleteLater(); self.app.processEvents()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    def select(self,kind):
        row=self.row; row.fuel_type.setCurrentIndex(row.fuel_type.findData(kind)); row.fuel_type.confirm_name(force=True)
    def test_typing_chinese_does_not_change_parameters_or_open_popup(self):
        self.select(FuelType.DIESEL)
        self.row.activity.setText("123.4567890123456789")
        before=(self.row.lower_heating_value.text(),self.row.carbon.text(),self.row.oxidation.text(),self.row.path.currentData())
        self.row.fuel_type.lineEdit().setText("企业混合燃料")
        self.app.processEvents()
        self.assertEqual(before,(self.row.lower_heating_value.text(),self.row.carbon.text(),self.row.oxidation.text(),self.row.path.currentData()))
        self.assertFalse(self.row.fuel_type.view().isVisible())
        self.row.fuel_type.confirm_name()
        self.assertIsNone(self.page._fuel_option_for_row(self.row))
        self.assertEqual(self.row.carbon.text(),"")
        self.assertIsNone(self.row.carbon_source.currentData())
        self.assertIsNone(self.row.findChild(QCheckBox,"fuelCustomMode1"))
    def test_confirming_same_catalog_fuel_resets_parameters_and_basis(self):
        self.select(FuelType.NATURAL_GAS)
        self.row.lhv_source.setCurrentIndex(self.row.lhv_source.findData("MEASURED"))
        self.row.lower_heating_value.setText("400.123456789")
        self.row.carbon_basis.setCurrentIndex(self.row.carbon_basis.findData("DIRECT"))
        self.row.fuel_type.activated.emit(self.row.fuel_type.currentIndex())
        self.assertEqual(self.row.lhv_source.currentData(),"STANDARD_DEFAULT")
        self.assertEqual(self.row.lower_heating_value.text(),"389.31")
        self.assertEqual(self.row.carbon_basis.currentData(),"HEAT_CONTENT")
        self.assertIsInstance(self.row.calculated_carbon_label,QLineEdit)
        self.assertTrue(self.row.calculated_carbon_label.isReadOnly())
        self.assertTrue(self.row.findChildren(QToolButton))
    def test_nonempty_activity_is_not_reinterpreted_when_confirmed_unit_changes(self):
        self.select(FuelType.DIESEL); self.row.activity.setText("42.1234567890123456789")
        self.select(FuelType.NATURAL_GAS)
        self.assertEqual(self.row.path.currentData(),FuelPath.VOLUME)
        self.assertEqual(self.row.activity.text(),"")
        self.assertTrue(self.row._activity_drafts)
        self.assertIn("42.1234567890123456789",self.row._activity_drafts.values())
        self.select(FuelType.DIESEL)
        self.row.restore_activity_button.click()
        self.assertEqual(self.row.activity.text(),"42.1234567890123456789")
    def test_project_restore_keeps_explicit_sources_values_and_pending_name(self):
        self.select(FuelType.NATURAL_GAS)
        self.row.lhv_source.setCurrentIndex(self.row.lhv_source.findData("MEASURED"))
        self.row.lower_heating_value.setText("400.1234567890123456789")
        self.row.activity.setText("1.")
        self.row.fuel_type.setEditText("未确认的新名称")
        state=self.page._capture_form_state()
        self.page._restore_form_state(state)
        row=self.page._fuel_rows[0]
        self.assertEqual(row.lower_heating_value.text(),"400.1234567890123456789")
        self.assertEqual(row.lhv_source.currentData(),"MEASURED")
        self.assertEqual(row.activity.text(),"1.")
        self.assertEqual(row.fuel_type.currentText(),"未确认的新名称")
        self.assertNotEqual(row._committed_name,row.fuel_type.currentText())

    def test_catalog_fch_explicit_source_editability_and_restore_default_evidence(self):
        self.select(FuelType.NATURAL_GAS)
        self.assertTrue(self.row.carbon.isReadOnly())
        self.row.carbon_source.setCurrentIndex(self.row.carbon_source.findData("CALCULATED"))
        self.assertFalse(self.row.carbon.isReadOnly())
        self.row.carbon.setText("0.01534567890123456789")
        state=self.page._capture_form_state()
        self.page._restore_form_state(state)
        row=self.page._fuel_rows[0]
        self.assertEqual(row.carbon.text(),"0.01534567890123456789")
        self.assertEqual(row.carbon_source.currentData(),"CALCULATED")
        self.assertFalse(row.carbon.isReadOnly())
        row.lhv_source.setCurrentIndex(row.lhv_source.findData("STANDARD_DEFAULT"))
        row.lower_heating_value.setText("388.123456789")
        state=self.page._capture_form_state()
        self.page._restore_form_state(state)
        row=self.page._fuel_rows[0]
        self.assertEqual(row.lower_heating_value.text(),"388.123456789")
        self.assertTrue(row.lower_heating_value.isReadOnly())
        row.activity.setText("1")
        from packages.core.models import DomainValidationError
        with self.assertRaisesRegex(DomainValidationError, "与当前缺省值不一致"):
            self.page._fuel()
        row.lhv_source.setCurrentIndex(row.lhv_source.findData("MEASURED"))
        self.assertEqual(self.page._fuel()[0].lower_heating_value.value, __import__('decimal').Decimal("388.123456789"))
    def test_header_and_top_switch_share_state_and_keep_input(self):
        group_id=self.page._source_toggle_groups[0][0]
        top=self.page._source_toggle_buttons[group_id]
        header=self.page._source_header_buttons[group_id][0]
        self.row.activity.setText("123.456789")
        before=header.label.text()
        header.click()
        self.assertNotEqual(header.label.text(),before)
        self.assertEqual(top.state_label.text().replace("✓ ",""),header.label.text())
        self.assertEqual(self.row.activity.text(),"123.456789")
        top.click()
        self.assertEqual(header.label.text(),before)
        self.assertEqual(self.row.activity.text(),"123.456789")

    def test_new_confirmed_fuel_does_not_inherit_legacy_direct_source(self):
        self.row.direct_carbon_source.setCurrentIndex(self.row.direct_carbon_source.findData("USER_DEFINED"))
        self.select(FuelType.DIESEL)
        self.row.carbon_basis.setCurrentIndex(self.row.carbon_basis.findData("DIRECT"))
        self.row.carbon_direct.setText("0.7")
        self.row.activity.setText("1")
        from packages.standards.carbon_material import ParameterSourceKind
        self.assertIs(self.page._fuel()[0].carbon_content.source_kind,ParameterSourceKind.MEASURED)
    def test_special_electricity_basis_never_becomes_automatic_fallback(self):
        from unittest.mock import patch
        row=self.page._energy_family_rows["electricity"][0]
        option=row.factor_selector.currentData()
        self.assertEqual(option.table_number,"表1")
        queries=self.page._uat03_parameter_queries
        original=queries.electricity_catalog_options
        with patch.object(queries,"electricity_catalog_options",side_effect=lambda *args: tuple(item for item in original(*args) if item.table_number!="表1")):
            self.page._refresh_energy_factor_options(row)
            self.assertIsNone(row.factor_selector.currentData())
            row.amount.setText("1")
            from packages.core.models import DomainValidationError
            with self.assertRaisesRegex(DomainValidationError,"明确选择"):
                self.page._electricity("enterprise.current",self.page._period(),render=False)
            saved=self.page._energy_row_state(row)
            self.assertEqual(saved["selected_factor_id"],option.factor.factor_id)
            index=next(i for i in range(row.factor_selector.count()) if getattr(row.factor_selector.itemData(i),"table_number",None)=="表4")
            row.factor_selector.setCurrentIndex(index)
            self.assertEqual(self.page._electricity("enterprise.current",self.page._period(),render=False)[0].selected_factor_id,row.factor_selector.currentData().factor.factor_id)
    def test_unavailable_restored_electricity_id_is_retained_and_not_replaced(self):
        row=self.page._energy_family_rows["electricity"][0]
        saved=self.page._energy_row_state(row)
        saved.update(amount="1", selected_factor_id="missing-historical-factor")
        self.page._restore_unified_energy_rows([saved])
        row=self.page._energy_family_rows["electricity"][0]
        self.assertIsNone(row.factor_selector.currentData())
        self.assertEqual(self.page._energy_row_state(row)["selected_factor_id"],"missing-historical-factor")
        from packages.core.models import DomainValidationError
        with self.assertRaisesRegex(DomainValidationError,"明确选择"):
            self.page._electricity("enterprise.current",self.page._period(),render=False)
        row.kind.setCurrentIndex(row.kind.findData("exported_electricity"))
        with self.assertRaisesRegex(DomainValidationError,"明确选择"):
            self.page._exported_electricity()
