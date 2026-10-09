from __future__ import annotations

import os
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QValidator
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from packages.application import CatalogQueryService
from packages.core import AccountingPeriod, PeriodType
from packages.standards.carbon_material import (
    CalcinationInput,
    CarbonMaterialCalculator,
    EmissionSourceStatus,
    InputValue,
    MaterialBasis,
    MaterialComponentKind,
)
from packages.standards.carbon_material_normalization import MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage, SOURCE_LABELS
from packages.ui.field_specs import (
    CURRENT_UI_INPUT_KEYS,
    FIELD_SPECS,
    FieldDataType,
    domain_to_ui_value,
    get_field_spec,
    numeric_field_specs,
    ui_to_domain_value,
)
from packages.ui.typed_inputs import create_typed_input
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH


class UIR01FieldSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def _page(self) -> CarbonMaterialAccountingPage:
        return CarbonMaterialAccountingPage(
            catalog_service=CatalogQueryService.empty(),
            calculator=CarbonMaterialCalculator(),
        )

    def test_every_current_input_has_traceable_field_spec_and_user_label(self) -> None:
        self.assertEqual(set(CURRENT_UI_INPUT_KEYS), set(FIELD_SPECS))
        internal_names = {
            "gc", "wfc", "cc", "ucc", "du", "wfc_c", "wvar", "wvar_c",
            "bpm", "bpmfc", "bg", "bgfc", "bwt", "bp", "bpfc", "bpmvar", "bgvar",
            "gpm", "gpmfc", "gta", "gtafc", "gwt", "gp", "gpfc", "gpmvar",
        }
        for key in CURRENT_UI_INPUT_KEYS:
            spec = get_field_spec(key)
            self.assertTrue(spec.display_name.strip(), key)
            self.assertNotEqual(spec.display_name, spec.internal_key)
            self.assertTrue(spec.standard_clause, key)
            self.assertTrue(spec.source_location, key)
            if spec.is_numeric:
                self.assertTrue(spec.unit and spec.unit != "无", key)
                self.assertTrue(spec.data_type in {
                    FieldDataType.QUANTITY,
                    FieldDataType.PERCENTAGE,
                    FieldDataType.INTEGER,
                })
            self.assertNotIn(spec.display_name, internal_names)

        page = self._page()
        visible_labels = {label.text().strip() for label in page.findChildren(QLabel)}
        self.assertTrue(internal_names.isdisjoint(visible_labels))
        page.deleteLater()

    def test_page_controls_are_all_backed_by_specs(self) -> None:
        page = self._page()
        keys = {
            "enterprise_name",
            "period_type",
            "period_year",
            "period_month",
            "boundary_confirmed",
            "other_activity_present",
            "transport_present",
            "fuel_id",
            "fuel_type",
            "fuel_path",
            "fuel_activity",
            "fuel_carbon",
            "fuel_oxidation",
            "fuel_lhv",
            "fuel_source_reference",
            "exported_electricity_id",
            "exported_electricity_amount",
            "heat_id",
            "heat_amount",
            "heat_enthalpy",
            "heat_pressure",
            "heat_temperature",
            "heat_steam_kind",
            "heat_factor",
            "heat_factor_selection_reason",
            "exported_heat_id",
            "exported_heat_amount",
            "exported_heat_enthalpy",
            "exported_heat_pressure",
            "exported_heat_temperature",
            "exported_heat_steam_kind",
        }
        keys.update(page._fields)
        keys.update(f"source_status.{source_id}" for source_id in SOURCE_LABELS)
        for prefix in ("calcination", "baking", "graphitization"):
            keys.update(
                f"{prefix}.{suffix}"
                for suffix in (
                    "mass_basis",
                    "composition_basis",
                    "normalized_basis",
                    "fixed_carbon_component_kind",
                    "volatile_matter_component_kind",
                    "moisture_evidence",
                    "conversion_evidence",
                    "evidence_reference",
                )
            )
        keys.update(
            f"electricity.{suffix}"
            for suffix in (
                "detail_id",
                "amount",
                "acquisition",
                "attribute",
                "proof_type",
                "proof_status",
            )
        )
        self.assertTrue(keys.issubset(FIELD_SPECS), sorted(keys.difference(FIELD_SPECS)))
        page.deleteLater()

    def test_typed_numeric_inputs_reject_letters_negative_and_invalid_fraction(self) -> None:
        parent = QWidget()
        for spec in numeric_field_specs():
            widget = create_typed_input(parent, spec, f"test_{spec.internal_key.replace('.', '_')}")
            self.assertIsNotNone(widget.validator(), spec.internal_key)  # type: ignore[attr-defined]
            validator = widget.validator()  # type: ignore[attr-defined]
            self.assertEqual(validator.validate("abc", 0)[0], QValidator.State.Invalid, spec.internal_key)
            widget.setText("")  # type: ignore[attr-defined]
            self.assertEqual(widget.text(), "", spec.internal_key)  # type: ignore[attr-defined]
            zero_or_minimum = "0" if spec.min is None or spec.min <= 0 else format(spec.min, "f")
            widget.setText(zero_or_minimum)  # type: ignore[attr-defined]
            self.assertEqual(widget.text(), zero_or_minimum, spec.internal_key)  # type: ignore[attr-defined]
            if spec.data_type is not FieldDataType.INTEGER:
                widget.setText("1.25")  # type: ignore[attr-defined]
                self.assertEqual(widget.text(), "1.25", spec.internal_key)  # type: ignore[attr-defined]
            else:
                self.assertEqual(validator.validate("1.25", 0)[0], QValidator.State.Invalid, spec.internal_key)
            widget.setText("-1")  # type: ignore[attr-defined]
            self.assertEqual(widget.text(), "", spec.internal_key)  # type: ignore[attr-defined]

        percentage = create_typed_input(parent, get_field_spec("calcination.wfc"), "percentage")
        percentage.setText("0")  # type: ignore[attr-defined]
        self.assertTrue(percentage.hasAcceptableInput())  # type: ignore[attr-defined]
        percentage.setText("100")  # type: ignore[attr-defined]
        self.assertEqual(percentage.text(), "100")  # type: ignore[attr-defined]
        self.assertTrue(percentage.hasAcceptableInput())  # type: ignore[attr-defined]
        percentage.setText("101")  # type: ignore[attr-defined]
        self.assertEqual(percentage.text(), "")  # type: ignore[attr-defined]
        self.assertFalse(percentage.hasAcceptableInput())  # type: ignore[attr-defined]
        parent.deleteLater()

    def test_typed_numeric_inputs_reject_real_keyboard_and_paste_candidates(self) -> None:
        parent = QWidget()
        parent.show()
        percentage = create_typed_input(parent, get_field_spec("calcination.wfc"), "percentage")
        percentage.setFocus()  # type: ignore[attr-defined]

        QTest.keyClicks(percentage, "100")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "100")  # type: ignore[attr-defined]
        self.assertTrue(percentage.hasAcceptableInput())  # type: ignore[attr-defined]

        # QDoubleValidator used to report 101 as Intermediate, allowing the
        # third key to remain visible.  The exact candidate must now be
        # rejected before QLineEdit mutates its text.
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "101")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "10")  # type: ignore[attr-defined]
        self.assertNotEqual(percentage.text(), "101")  # type: ignore[attr-defined]
        self.assertTrue(percentage.hasAcceptableInput())  # type: ignore[attr-defined]

        # A rejected minus sign must not silently turn the subsequent ``1``
        # into a valid-looking positive value.
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "-1")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "")  # type: ignore[attr-defined]

        # Keyboard separators are rejected, and the edit remains an
        # acceptable numeric value rather than retaining ``1,000``.
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "1,000")  # type: ignore[arg-type]
        self.assertNotIn(",", percentage.text())  # type: ignore[attr-defined]
        self.assertTrue(percentage.hasAcceptableInput())  # type: ignore[attr-defined]

        clipboard = self.application.clipboard()
        original_clipboard = clipboard.text()
        try:
            for pasted in ("101", "-1", "1,000"):
                percentage.clear()  # type: ignore[attr-defined]
                clipboard.setText(pasted)
                percentage.setFocus()  # type: ignore[attr-defined]
                QTest.keyClick(percentage, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
                self.assertEqual(percentage.text(), "", pasted)  # type: ignore[attr-defined]
        finally:
            clipboard.setText(original_clipboard)

        # After an invalid attempt, valid boundary values and a corrected
        # edit must still be accepted immediately.
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "0")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "0")  # type: ignore[attr-defined]
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "100")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "100")  # type: ignore[attr-defined]
        percentage.clear()  # type: ignore[attr-defined]
        QTest.keyClicks(percentage, "101")  # type: ignore[arg-type]
        QTest.keyClick(percentage, Qt.Key.Key_Backspace)
        QTest.keyClicks(percentage, "00")  # type: ignore[arg-type]
        self.assertEqual(percentage.text(), "100")  # type: ignore[attr-defined]

        parent.deleteLater()

    def test_percentage_ui_and_domain_ratio_conversion_is_decimal_and_bidirectional(self) -> None:
        spec = get_field_spec("calcination.wfc")
        self.assertEqual(ui_to_domain_value(spec, "0"), "0")
        self.assertEqual(ui_to_domain_value(spec, "100"), "1")
        self.assertEqual(ui_to_domain_value(spec, "12.5"), "0.125")
        self.assertEqual(domain_to_ui_value(spec, Decimal("0")), "0")
        self.assertEqual(domain_to_ui_value(spec, Decimal("1")), "100")
        self.assertEqual(domain_to_ui_value(spec, Decimal("0.125")), "12.500")
        self.assertIsNone(ui_to_domain_value(spec, None))

    def test_same_legal_input_maps_to_equal_domain_and_equal_result(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        catalog_path = Path(directory.name) / "catalog.sqlite"
        build_catalog_database(DEFAULT_SOURCE_PATH, catalog_path)
        service = CatalogQueryService(
            SQLiteCatalogRepository(catalog_path),
            as_of=date(2026, 9, 12),
        )
        page = CarbonMaterialAccountingPage(
            catalog_service=service,
            calculator=CarbonMaterialCalculator(),
        )
        page.enterprise_name.setText("UIR01 等价企业")
        page.boundary_confirmed.setChecked(True)
        page._source_toggle_buttons["calcination"].click()
        process_row = page._process_rows["calcination"][0]
        feed, = process_row["materials"]
        feed["role"].setCurrentIndex(feed["role"].findData(MaterialRole.CALCINATION_FEED))
        feed["name"].setText("煅烧原料")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("50")
        feed["volatile_matter"].setText("10")
        product = page._add_material_line(process_row)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("70")
        product["fixed_carbon"].setText("25")
        product["volatile_matter"].setText("2")

        ui_input = page._input()
        actual_process = ui_input.calcinations[0]
        self.assertEqual(actual_process.gc.value, Decimal("100"))
        self.assertEqual(actual_process.wfc.value, Decimal("0.5"))
        self.assertEqual(actual_process.cc.value, Decimal("70"))
        self.assertEqual(actual_process.ucc.value, Decimal("0"))
        self.assertEqual(actual_process.du.value, Decimal("0"))
        self.assertEqual(actual_process.wfc_c.value, Decimal("0.25"))
        self.assertEqual(actual_process.wvar.value, Decimal("0.1"))
        self.assertEqual(actual_process.wvar_c.value, Decimal("0.02"))

        expected_process = CalcinationInput(
            gc="100",
            wfc=InputValue("0.5", "ratio"),
            cc="70",
            ucc="0",
            du="0",
            wfc_c=InputValue("0.25", "ratio"),
            wvar=InputValue("0.1", "ratio"),
            wvar_c=InputValue("0.02", "ratio"),
            k1=actual_process.k1,
            mass_basis=MaterialBasis.RECEIVED,
            composition_basis=MaterialBasis.RECEIVED,
            normalized_basis=MaterialBasis.RECEIVED,
            fixed_carbon_component_kind=MaterialComponentKind.FIXED_CARBON,
            volatile_matter_component_kind=MaterialComponentKind.VOLATILE_MATTER,
            instance_id=actual_process.instance_id,
        )
        direct_input = replace(
            ui_input,
            input_id="input.uir01.expected",
            calcination=expected_process,
            calcinations=(expected_process,),
        )
        ui_outcome = page.calculator.calculate(ui_input)
        expected_outcome = CarbonMaterialCalculator().calculate(direct_input)
        self.assertTrue(ui_outcome.successful, ui_outcome.problems)
        self.assertTrue(expected_outcome.successful, expected_outcome.problems)
        self.assertEqual(ui_outcome.result.total_amount, expected_outcome.result.total_amount)
        page.deleteLater()

if __name__ == "__main__":
    unittest.main()
