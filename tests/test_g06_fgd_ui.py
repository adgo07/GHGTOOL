import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QApplication

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import CatalogQueryService
from packages.core import DomainValidationError
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import EmissionSourceStatus, FGDInput, InputOrigin, ParameterSourceKind
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.name_selector import NameSelector, chemical_label
from packages.ui.compact_choices import SegmentedChoiceControl
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


class G06FgdUiTests(unittest.TestCase):
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
        self.page = shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(self.page, CarbonMaterialAccountingPage)
        assert isinstance(self.page, CarbonMaterialAccountingPage)

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def _catalog_option(self, parameter_id: str):
        return next(
            item for item in self.page._carbonate_options()
            if item.factor.parameter_id == parameter_id
        )

    def _select_catalog(self, component: dict[str, object], parameter_id: str):
        option = self._catalog_option(parameter_id)
        selector = component["carbonate_type"]
        self.assertIsInstance(selector, NameSelector)
        selector.setEditText(chemical_label(option.label))
        selector.confirm_name(force=True)
        self.assertEqual(component["confirmed_name"], option.label)
        return option

    def _unit(self) -> dict[str, object]:
        unit = self.page._process_rows["fgd"][0]
        unit["reagent_name"].setText("石灰石")
        unit["group_amount"].setText("10")
        return unit

    def _enable_fgd(self) -> None:
        status = self.page._source_statuses["CAR-SRC-FGD-001"]
        status.setCurrentIndex(status.findData(EmissionSourceStatus.INVOLVED))

    def test_confirmed_catalog_identity_uses_subscript_display_and_explicit_factor_source(self) -> None:
        unit = self._unit()
        component = unit["components"][0]
        option = self._select_catalog(component, "car-par-c2-caco3")
        selector = component["carbonate_type"]
        self.assertEqual(component["confirmed_name"], option.label)
        self.assertEqual(selector.currentText(), chemical_label(option.label))
        self.assertEqual(selector.currentData().factor.factor_id, option.factor.factor_id)
        self.assertEqual(component["ef1_source"].currentData(), "STD")
        self.assertTrue(component["ef1"].isReadOnly())
        self.assertTrue(any(
            isinstance(child, SegmentedChoiceControl)
            and {button.text() for button in child.group.buttons()} == {"标准值", "计算值", "实测值"}
            for child in component["_widget"].findChildren(SegmentedChoiceControl)
            if child.combo is component["ef1_source"]
        ))

        component["ef1_source"].setCurrentIndex(component["ef1_source"].findData("CALC"))
        self.assertEqual(component["ef1"].text(), "")
        self.assertFalse(component["ef1"].isReadOnly())
        component["ef1"].setText("0.456789012345")
        component["i_source"].setCurrentIndex(component["i_source"].findData("CALCULATED"))
        component["i"].setText("92.3456789")
        component["tr_source"].setCurrentIndex(component["tr_source"].findData("MEASURED"))
        component["tr"].setText("98.7654321")

        value = self.page._process("fgd", FGDInput).components[0]
        self.assertIs(value.origin, InputOrigin.CATALOG)
        self.assertEqual(value.emission_factor.value, Decimal("0.456789012345"))
        self.assertIs(value.emission_factor.source_kind, ParameterSourceKind.CALCULATED)
        self.assertIs(value.carbonate_fraction.source_kind, ParameterSourceKind.CALCULATED)
        self.assertIs(value.conversion_rate.source_kind, ParameterSourceKind.MEASURED)

    def test_unconfirmed_custom_name_and_unselected_source_do_not_become_user_defined(self) -> None:
        unit = self._unit()
        component = unit["components"][0]
        selector = component["carbonate_type"]
        selector.setEditText("企业自定义碳酸盐")
        with self.assertRaisesRegex(DomainValidationError, "确认碳酸盐名称"):
            self.page._process("fgd", FGDInput)

        selector.confirm_name(force=True)
        self.assertIsNone(component["ef1_source"].currentData())
        component["ef1"].setText("0.501")
        with self.assertRaisesRegex(DomainValidationError, "选择标准值、计算值或实测值"):
            self.page._process("fgd", FGDInput)

        component["ef1_source"].setCurrentIndex(component["ef1_source"].findData("MEASURED"))
        component["ef1"].setText("0.501")
        component["i_source"].setCurrentIndex(component["i_source"].findData("MEASURED"))
        component["i"].setText("91.25")
        component["tr_source"].setCurrentIndex(component["tr_source"].findData("CALCULATED"))
        component["tr"].setText("99.5")
        value = self.page._process("fgd", FGDInput).components[0]
        self.assertIs(value.origin, InputOrigin.CUSTOM)
        self.assertIs(value.emission_factor.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(value.carbonate_fraction.source_kind, ParameterSourceKind.MEASURED)
        self.assertIs(value.conversion_rate.source_kind, ParameterSourceKind.CALCULATED)

    def test_new_component_does_not_change_existing_sources_or_fake_ratio_measurements(self) -> None:
        unit = self._unit()
        first = unit["components"][0]
        self._select_catalog(first, "car-par-c2-caco3")
        first_ratio_modes = (first["i_source"].currentData(), first["tr_source"].currentData())
        first_ratio_values = (first["i"].text(), first["tr"].text())

        second = self.page._add_fgd_component(unit)
        self.assertEqual((first["i_source"].currentData(), first["tr_source"].currentData()), first_ratio_modes)
        self.assertEqual((first["i"].text(), first["tr"].text()), first_ratio_values)
        self.assertIsNone(second["i_source"].currentData())
        self.assertIsNone(second["tr_source"].currentData())
        self.assertEqual((second["i"].text(), second["tr"].text()), ("", ""))

        self._select_catalog(second, "car-par-c2-mgco3")
        self.assertEqual(second["ef1_source"].currentData(), "STD")
        self.assertIsNone(second["i_source"].currentData())
        self.assertIsNone(second["tr_source"].currentData())
        self.assertEqual((second["i"].text(), second["tr"].text()), ("", ""))
        restored = self.page._process("fgd", FGDInput)
        self.assertEqual(len(restored.components), 2)
        self.assertIsNone(restored.components[1].carbonate_fraction)
        self.assertIsNone(restored.components[1].conversion_rate)

    def test_restore_preserves_saved_standard_values_and_legacy_same_name_identity(self) -> None:
        unit = self._unit()
        component = unit["components"][0]
        option = self._select_catalog(component, "car-par-c2-caco3")
        self.assertEqual(component["i_source"].currentData(), "STANDARD_DEFAULT")
        self.assertEqual(component["tr_source"].currentData(), "STANDARD_DEFAULT")
        for edit, value in ((component["ef1"], "0.440123"), (component["i"], "90.12345"), (component["tr"], "99.87654")):
            blocker = QSignalBlocker(edit)
            edit.setText(value)
            del blocker
        saved_state = self.page._capture_form_state()
        self.page._restore_form_state(saved_state)
        restored = self.page._process_rows["fgd"][0]["components"][0]
        self.assertEqual(
            (restored["ef1"].text(), restored["i"].text(), restored["tr"].text()),
            ("0.440123", "90.12345", "99.87654"),
        )
        self.assertEqual(restored["ef1_source"].currentData(), "STD")
        self.assertEqual(restored["i_source"].currentData(), "STANDARD_DEFAULT")
        self.assertEqual(restored["tr_source"].currentData(), "STANDARD_DEFAULT")
        restored["ef1_source"].setCurrentIndex(restored["ef1_source"].findData("CALC"))
        self.assertEqual(restored["ef1"].text(), "")

        legacy_state = dict(saved_state)
        legacy_state["fgd_carbonate_confirmations"] = dict(saved_state["fgd_carbonate_confirmations"])
        legacy_state["fgd_factor_provenance"] = dict(saved_state["fgd_factor_provenance"])
        component_id = restored["component_id"]
        legacy_state["fgd_carbonate_confirmations"][component_id] = {
            "confirmed_name": option.label,
            "legacy_custom_identity": True,
        }
        legacy_state["fgd_factor_provenance"][component_id] = {
            "mode": "USER_DEFINED",
            "factor_id": None,
            "legacy_custom_identity": True,
        }
        self.page._restore_form_state(legacy_state)
        restored = self.page._process_rows["fgd"][0]["components"][0]
        self.assertTrue(restored["legacy_custom_identity"])
        self.assertIsNone(self.page._fgd_component_option(restored))
        self.assertEqual(restored["ef1_source"].currentData(), "USER_DEFINED")
        value = self.page._process("fgd", FGDInput).components[0]
        self.assertIs(value.origin, InputOrigin.CUSTOM)
        self.assertIs(value.emission_factor.source_kind, ParameterSourceKind.USER_DEFINED)

    def test_restored_standard_values_matching_current_catalog_are_used_as_standard_defaults(self) -> None:
        unit = self._unit()
        component = unit["components"][0]
        option = self._select_catalog(component, "car-par-c2-caco3")
        self._enable_fgd()
        saved_state = self.page._capture_form_state()
        self.page._restore_form_state(saved_state)

        restored_unit = self.page._input(increment=False, render_electricity=False).fgd_units[0]
        restored = restored_unit.components[0]
        i_factor, _ = self.page._fgd_default_ratio("i")
        tr_factor, _ = self.page._fgd_default_ratio("tr")
        expected_ef = self.page._parameter_value_from_factor(
            option.factor, option.selection_reason
        )
        self.assertEqual(restored.emission_factor.value, Decimal(str(option.factor.value)))
        self.assertIs(restored.emission_factor.source_kind, expected_ef.source_kind)
        self.assertIsNotNone(i_factor)
        self.assertEqual(restored.carbonate_fraction.value, Decimal(str(i_factor.value)))
        self.assertIs(restored.carbonate_fraction.source_kind, ParameterSourceKind.STANDARD_DEFAULT)
        self.assertIsNotNone(tr_factor)
        self.assertEqual(restored.conversion_rate.value, Decimal(str(tr_factor.value)))
        self.assertIs(restored.conversion_rate.source_kind, ParameterSourceKind.STANDARD_DEFAULT)

    def test_restored_standard_values_differing_from_current_catalog_block_formal_input(self) -> None:
        cases = (
            ("ef1", "0.440123", "排放因子"),
            ("i", "90.12345", "碳酸盐含量"),
            ("tr", "99.87654", "转化率"),
        )
        for field, saved_value, label in cases:
            with self.subTest(field=field):
                unit = self._unit()
                component = unit["components"][0]
                self._select_catalog(component, "car-par-c2-caco3")
                self._enable_fgd()
                blocker = QSignalBlocker(component[field])
                component[field].setText(saved_value)
                del blocker
                saved_state = self.page._capture_form_state()
                self.page._restore_form_state(saved_state)

                restored = self.page._process_rows["fgd"][0]["components"][0]
                self.assertEqual(restored[field].text(), saved_value)
                mode_key = "ef1_source" if field == "ef1" else f"{field}_source"
                expected_mode = "STD" if field == "ef1" else "STANDARD_DEFAULT"
                self.assertEqual(restored[mode_key].currentData(), expected_mode)
                with self.assertRaisesRegex(DomainValidationError, label):
                    self.page._input(increment=False, render_electricity=False)


if __name__ == "__main__":
    unittest.main()
