from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QWidget

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
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import EmissionSourceStatus, InMemoryRecordRepository
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard, SourceCardPresentationState
from packages.ui.view_models import AppRoute


SOURCE_IDS = (
    "CAR-SRC-FUEL-001",
    "CAR-SRC-CALCINATION-001",
    "CAR-SRC-BAKING-001",
    "CAR-SRC-GRAPHITIZATION-001",
    "CAR-SRC-FUME-INCINERATION-001",
    "CAR-SRC-FGD-001",
    "CAR-SRC-PURCHASED-ELECTRICITY-001",
    "CAR-SRC-PURCHASED-HEAT-001",
    "CAR-SRC-EXPORTED-ELECTRICITY-001",
    "CAR-SRC-EXPORTED-HEAT-001",
)


class UIR02SourceCardTests(unittest.TestCase):
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
        self.shell = self.window.centralWidget()
        self.page = self.shell.pages[AppRoute.NEW_ACCOUNTING]
        self.assertIsInstance(self.page, CarbonMaterialAccountingPage)
        assert isinstance(self.page, CarbonMaterialAccountingPage)
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def _card(self, source_id: str) -> SourceCard:
        card = self.page.findChild(SourceCard, f"sourceCard_{source_id}")
        self.assertIsNotNone(card)
        assert card is not None
        return card

    def _status_combo(self, source_id: str) -> QComboBox:
        combo = self.page.findChild(QComboBox, f"sourceStatus_{source_id}")
        self.assertIsNotNone(combo)
        assert combo is not None
        return combo

    def test_all_ten_cards_default_to_collapsed_not_involved(self) -> None:
        self.assertEqual(set(self.page._source_cards), set(SOURCE_IDS))
        for source_id in SOURCE_IDS:
            card = self._card(source_id)
            self.assertFalse(card.body.isVisible())
            self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.NOT_INVOLVED)
            self.assertIs(card.presentation_state, SourceCardPresentationState.NOT_INVOLVED)
            self.assertNotIn("CAR-", card.summary_label.text())

    def test_enable_maps_existing_domain_state_without_creating_activity_data(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        card = self._card(source_id)
        action = card.findChild(QPushButton, f"sourceCardAction_{source_id}")
        self.assertIsNotNone(action)
        assert action is not None
        action.click()
        self.application.processEvents()

        self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.INVOLVED)
        self.assertTrue(card.is_expanded)
        self.assertTrue(card.body.isVisible())
        self.assertFalse(self.page._field_has_value("calcination.gc"))
        self.assertEqual(card.presentation_state, SourceCardPresentationState.FILLING)

    def test_expand_input_collapse_reexpand_preserves_values_and_domain_parity(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        combo = self._status_combo(source_id)
        combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))
        self.page.enterprise_name.setText("卡片保持企业")
        self.page.boundary_confirmed.setChecked(True)
        for field, value in {
            "gc": "100",
            "wfc": "50",
            "cc": "70",
            "ucc": "5",
            "du": "1",
            "wfc_c": "25",
            "wvar": "10",
            "wvar_c": "2",
        }.items():
            self.page._fields[f"calcination.{field}"].setText(value)
        controls = self.page._material_controls["calcination"]
        for key in ("mass_basis", "composition_basis", "normalized_basis"):
            controls[key].setCurrentIndex(controls[key].findData("RECEIVED"))
        controls["fixed_carbon_component_kind"].setCurrentIndex(
            controls["fixed_carbon_component_kind"].findData("FIXED_CARBON")
        )
        controls["volatile_matter_component_kind"].setCurrentIndex(
            controls["volatile_matter_component_kind"].findData("VOLATILE_MATTER")
        )
        before = self.page._input()
        before_outcome = self.page.calculator.calculate(before)
        self.assertTrue(before_outcome.successful, before_outcome.problems)

        card = self._card(source_id)
        card.set_expanded(False)
        self.assertFalse(card.body.isVisible())
        card.set_expanded(True)
        self.assertTrue(card.body.isVisible())
        self.assertEqual(self.page._fields["calcination.gc"].text(), "100")
        self.assertEqual(self.page._fields["calcination.wfc"].text(), "50")

        after = self.page._input()
        self.assertEqual(before.source_states, after.source_states)
        self.assertEqual(before.electricity_details, after.electricity_details)
        self.assertEqual(
            replace(before, input_id=after.input_id),
            after,
        )
        after_outcome = self.page.calculator.calculate(after)
        self.assertTrue(after_outcome.successful, after_outcome.problems)
        before_result = None if before_outcome.result is None else (before_outcome.result.total_amount, before_outcome.result.lines)
        after_result = None if after_outcome.result is None else (after_outcome.result.total_amount, after_outcome.result.lines)
        self.assertEqual(before_result, after_result)
        self.assertEqual(
            [(problem.code, problem.level, problem.field_id) for problem in before_outcome.problems],
            [(problem.code, problem.level, problem.field_id) for problem in after_outcome.problems],
        )
        snapshot_signature = lambda snapshot: (
            snapshot.parameter_id,
            snapshot.factor_id,
            snapshot.value_used,
            snapshot.unit_used,
            snapshot.source_id,
            snapshot.source_version,
            snapshot.selection_method,
            snapshot.selection_reason,
            snapshot.standard_id,
            snapshot.factor_version,
            snapshot.source_location,
            snapshot.factor_year,
            snapshot.detail_id,
        )
        self.assertEqual(
            [snapshot_signature(snapshot) for snapshot in before_outcome.parameter_snapshots],
            [snapshot_signature(snapshot) for snapshot in after_outcome.parameter_snapshots],
        )

    def test_domain_status_mapping_has_no_presentation_enum_leak(self) -> None:
        source_id = "CAR-SRC-FGD-001"
        combo = self._status_combo(source_id)
        card = self._card(source_id)
        expected = (
            (EmissionSourceStatus.NOT_INVOLVED, SourceCardPresentationState.NOT_INVOLVED),
            (EmissionSourceStatus.INVOLVED, SourceCardPresentationState.FILLING),
            (EmissionSourceStatus.UNCONFIRMED, SourceCardPresentationState.UNCONFIRMED),
        )
        for domain_status, presentation_status in expected:
            combo.setCurrentIndex(combo.findData(domain_status))
            self.application.processEvents()
            mapped = {item.source_id: item.status for item in self.page._source_states()}
            self.assertIs(mapped[source_id], domain_status)
            self.assertIs(card.presentation_state, presentation_status)
            self.assertNotIsInstance(card.presentation_state, EmissionSourceStatus)

    def test_completed_summary_is_business_facing_and_hides_internal_names(self) -> None:
        source_id = "CAR-SRC-FUEL-001"
        self._status_combo(source_id).setCurrentIndex(
            self._status_combo(source_id).findData(EmissionSourceStatus.INVOLVED)
        )
        for key, value in (
            ("fuel_id", "天然气"),
            ("fuel_activity", "10"),
            ("fuel_carbon", "0.2"),
            ("fuel_oxidation", "98"),
        ):
            self.page._fields[key].setText(value)
        card = self._card(source_id)
        card.set_expanded(False)
        summary = card.summary_label.text()
        self.assertIn("1 种燃料", summary)
        self.assertIn("已完成", summary)
        for forbidden in ("fuel_", "CAR-SRC", "resolver", "candidate"):
            self.assertNotIn(forbidden, summary)

    def test_navigation_keeps_card_inputs_in_memory(self) -> None:
        source_id = "CAR-SRC-BAKING-001"
        self._status_combo(source_id).setCurrentIndex(
            self._status_combo(source_id).findData(EmissionSourceStatus.INVOLVED)
        )
        self.page._fields["baking.bpm"].setText("8.5")
        self.shell.navigate(AppRoute.HOME)
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.assertEqual(self.page._fields["baking.bpm"].text(), "8.5")
        self.assertTrue(self._card(source_id).is_expanded)

    def test_multiple_electricity_details_survive_card_fold_and_stay_independent(self) -> None:
        source_id = "CAR-SRC-PURCHASED-ELECTRICITY-001"
        self._status_combo(source_id).setCurrentIndex(
            self._status_combo(source_id).findData(EmissionSourceStatus.INVOLVED)
        )
        self.page.findChild(QWidget, "addElectricityButton").click()
        rows = self.page._electricity_rows
        rows[0].detail_id.setText("grid-ordinary")
        rows[0].amount.setText("10")
        rows[0].acquisition.setCurrentIndex(rows[0].acquisition.findData(ElectricityAcquisitionMode.PURCHASED))
        rows[0].attribute.setCurrentIndex(rows[0].attribute.findData(ElectricityAttribute.ORDINARY))
        rows[1].detail_id.setText("onsite-nonfossil")
        rows[1].amount.setText("20")
        rows[1].acquisition.setCurrentIndex(rows[1].acquisition.findData(ElectricityAcquisitionMode.SELF_CONSUMED))
        rows[1].attribute.setCurrentIndex(rows[1].attribute.findData(ElectricityAttribute.NONFOSSIL))
        rows[1].proof_type.setCurrentIndex(rows[1].proof_type.findData(ElectricityProofType.MONTHLY_ORIGINAL_RECORD))
        rows[1].proof_status.setCurrentIndex(rows[1].proof_status.findData(ElectricityProofStatus.VALID))

        card = self._card(source_id)
        card.set_expanded(False)
        card.set_expanded(True)
        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual(
            [(item.detail_id, item.electricity_amount) for item in details],
            [("grid-ordinary", Decimal("10")), ("onsite-nonfossil", Decimal("20"))],
        )
        self.assertIn("2 条电力明细", card.summary_label.text())
        self.assertIn("已完成", card.summary_label.text())

    def test_blocked_electricity_resolution_marks_card_needs_attention(self) -> None:
        source_id = "CAR-SRC-PURCHASED-ELECTRICITY-001"
        self._status_combo(source_id).setCurrentIndex(
            self._status_combo(source_id).findData(EmissionSourceStatus.INVOLVED)
        )
        row = self.page._electricity_rows[0]
        row.detail_id.setText("missing-proof")
        row.amount.setText("20")
        row.acquisition.setCurrentIndex(row.acquisition.findData(ElectricityAcquisitionMode.SELF_CONSUMED))
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.NONFOSSIL))
        self.application.processEvents()

        card = self._card(source_id)
        self.assertIs(card.presentation_state, SourceCardPresentationState.NEEDS_ATTENTION)
        self.assertIn("需要处理", card.summary_label.text())
        self.assertIn("阻断", row.parameter_status.text())
        self.assertNotIn("已完成", card.summary_label.text())

    def test_existing_domain_error_marks_process_card_needs_attention(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        self._status_combo(source_id).setCurrentIndex(
            self._status_combo(source_id).findData(EmissionSourceStatus.INVOLVED)
        )
        self.page.enterprise_name.setText("基准证据缺失企业")
        self.page.boundary_confirmed.setChecked(True)
        for field, value in {
            "gc": "100",
            "wfc": "50",
            "cc": "70",
            "ucc": "5",
            "du": "1",
            "wfc_c": "25",
            "wvar": "10",
            "wvar_c": "2",
        }.items():
            self.page._fields[f"calcination.{field}"].setText(value)
        controls = self.page._material_controls["calcination"]
        for key in ("mass_basis", "composition_basis"):
            controls[key].setCurrentIndex(controls[key].findData("DRY"))
        controls["normalized_basis"].setCurrentIndex(controls["normalized_basis"].findData("RECEIVED"))
        controls["fixed_carbon_component_kind"].setCurrentIndex(
            controls["fixed_carbon_component_kind"].findData("FIXED_CARBON")
        )
        controls["volatile_matter_component_kind"].setCurrentIndex(
            controls["volatile_matter_component_kind"].findData("VOLATILE_MATTER")
        )
        self.page._run_calculation()
        self.application.processEvents()

        card = self._card(source_id)
        self.assertIs(card.presentation_state, SourceCardPresentationState.NEEDS_ATTENTION)
        self.assertIn("需要处理", card.summary_label.text())
        self.assertTrue(any("CAR-VAL-MATERIAL-BASIS-CONVERSION" in self.page.validation_list.item(i).text() for i in range(self.page.validation_list.count())))


if __name__ == "__main__":
    unittest.main()
