from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QWidget

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
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material import EmissionSourceStatus, FuelPath
from packages.standards.carbon_material_normalization import MaterialRole
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.ui.source_cards import SourceCard, SourceCardPresentationState
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import tree_texts


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

    def test_eight_source_toggles_default_disabled_and_map_to_ten_domain_sources(self) -> None:
        self.assertEqual(
            set(self.page._source_toggle_buttons),
            {"fuel", "calcination", "baking", "graphitization", "fume", "fgd", "electricity", "heat"},
        )
        self.assertEqual(set(self.page._source_cards), set(SOURCE_IDS))
        for source_id in SOURCE_IDS:
            card = self._card(source_id)
            self.assertFalse(card.body.isVisible())
            self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.NOT_INVOLVED)
            self.assertIs(card.presentation_state, SourceCardPresentationState.NOT_INVOLVED)
            self.assertNotIn("CAR-", card.summary_label.text())
        for group_id in self.page._source_toggle_buttons:
            toggle = self.page._source_toggle_buttons[group_id]
            self.assertIn("未启用", toggle.text())

    def test_enable_maps_existing_domain_state_without_creating_activity_data(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        card = self._card(source_id)
        toggle = self.page.findChild(QPushButton, "sourceToggle_calcination")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        self.application.processEvents()

        self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.INVOLVED)
        self.assertIn("已启用", toggle.text())
        self.assertTrue(card.isVisible())
        self.assertTrue(card.body.isVisible())
        self.assertGreater(card.body.height(), 0)
        self.assertGreater(self.page._fields["calcination.gc"].height(), 0)
        self.assertFalse(self.page._field_has_value("calcination.gc"))
        self.assertEqual(card.presentation_state, SourceCardPresentationState.NEEDS_ATTENTION)

    def test_disabling_and_reenabling_source_preserves_values_and_domain_parity(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        toggle = self.page.findChild(QPushButton, "sourceToggle_calcination")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        self.page.enterprise_name.setText("卡片保持企业")
        self.page.boundary_confirmed.setChecked(True)
        process = self.page._process_rows["calcination"][0]
        feed, = process["materials"]
        feed["role"].setCurrentIndex(feed["role"].findData(MaterialRole.CALCINATION_FEED))
        feed["name"].setText("煅烧原料")
        feed["mass"].setText("100")
        feed["fixed_carbon"].setText("50")
        feed["volatile_matter"].setText("10")
        product = self.page._add_material_line(process)
        product["role"].setCurrentIndex(product["role"].findData(MaterialRole.CALCINED_PRODUCT))
        product["name"].setText("煅后料")
        product["mass"].setText("70")
        product["fixed_carbon"].setText("25")
        product["volatile_matter"].setText("2")
        before = self.page._input()
        before_outcome = self.page.calculator.calculate(before)
        self.assertTrue(before_outcome.successful, before_outcome.problems)

        card = self._card(source_id)
        toggle.click()
        self.application.processEvents()
        self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.NOT_INVOLVED)
        self.assertFalse(card.isVisible())
        self.assertFalse(card.body.isVisible())
        self.assertEqual(feed["mass"].text(), "100")
        disabled = self.page._input()
        self.assertFalse(any(
            item.source_id == source_id and item.status is EmissionSourceStatus.INVOLVED
            for item in disabled.source_states
        ))

        toggle.click()
        self.application.processEvents()
        self.assertEqual(self._status_combo(source_id).currentData(), EmissionSourceStatus.INVOLVED)
        self.assertTrue(card.isVisible())
        self.assertTrue(card.body.isVisible())
        self.assertEqual(feed["mass"].text(), "100")
        self.assertEqual(feed["fixed_carbon"].text(), "50")

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
            (EmissionSourceStatus.INVOLVED, SourceCardPresentationState.NEEDS_ATTENTION),
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
        toggle = self.page.findChild(QPushButton, "sourceToggle_fuel")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        row = self.page._fuel_rows[0]
        row.fuel_type.setEditText("天然气")
        row.path.setCurrentIndex(row.path.findData(FuelPath.MASS))
        row.carbon_basis.setCurrentIndex(row.carbon_basis.findData("DIRECT"))
        row.activity.setText("10")
        row.carbon_direct.setText("0.02")
        row.direct_carbon_source.setCurrentIndex(row.direct_carbon_source.findData("MEASURED"))
        row.oxidation.setText("98")
        row.oxidation_source.setCurrentIndex(row.oxidation_source.findData("USER_DEFINED"))
        row.source_reference.setText("检测报告-UIR02")
        card = self._card(source_id)
        card.set_expanded(False)
        summary = card.summary_label.text()
        self.assertIn("1 条燃料明细", summary)
        self.assertIn("已完成", summary)
        for forbidden in ("fuel_", "CAR-SRC", "resolver", "candidate"):
            self.assertNotIn(forbidden, summary)

    def test_navigation_keeps_card_inputs_in_memory(self) -> None:
        source_id = "CAR-SRC-BAKING-001"
        toggle = self.page.findChild(QPushButton, "sourceToggle_baking")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        material = self.page._process_rows["baking"][0]["materials"][0]
        material["name"].setText("待焙烧品")
        material["mass"].setText("8.5")
        self.shell.navigate(AppRoute.HOME)
        self.shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.application.processEvents()
        self.assertEqual(material["mass"].text(), "8.5")
        self.assertTrue(self._card(source_id).is_expanded)

    def test_multiple_electricity_details_survive_source_toggle_and_stay_independent(self) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_electricity")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        rows = self.page._energy_family_rows["electricity"]
        second = self.page._add_unified_energy_row(kind="purchased_electricity", line_id="onsite-nonfossil")
        rows[0].line_id.setText("grid-ordinary")
        rows[0].amount.setText("10")
        rows[1].amount.setText("20")
        rows[1].attribute.setCurrentIndex(rows[1].attribute.findData(ElectricityAttribute.NONFOSSIL))
        rows[0].line_id.setText("grid-ordinary")
        self.assertIs(second, rows[1])

        toggle.click()
        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual(
            [(item.detail_id, item.electricity_amount) for item in details],
            [("grid-ordinary", Decimal("10")), ("onsite-nonfossil", Decimal("20"))],
        )
        toggle.click()
        self.assertEqual([row.amount.text() for row in rows], ["10", "20"])
        toggle.click()
        details = self.page._electricity("enterprise.ui", self.page._period())
        self.assertEqual([item.detail_id for item in details], ["grid-ordinary", "onsite-nonfossil"])

    def test_nonfossil_electricity_needs_no_proof_to_complete(self) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_electricity")
        assert toggle is not None
        row = self.page._energy_family_rows["electricity"][0]
        row.line_id.setText("nonfossil-purchase")
        row.amount.setText("20")
        row.attribute.setCurrentIndex(row.attribute.findData(ElectricityAttribute.NONFOSSIL))
        toggle.click()
        self.page.enterprise_name.setText("非化石电力企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page._run_calculation()
        self.application.processEvents()

        messages = "\n".join(tree_texts(self.page.validation_list))
        self.assertFalse(self.page.result_card.isHidden(), messages)
        self.assertEqual(len(self.page.record_repository.list_all()), 1)
        self.assertNotIn("证明材料", messages)
        self.assertIsNone(self.page.findChild(QWidget, "electricityProofTypeSelector"))
        self.assertIsNone(self.page.findChild(QWidget, "electricityProofStatusSelector"))
    def test_existing_domain_error_marks_process_card_needs_attention(self) -> None:
        source_id = "CAR-SRC-CALCINATION-001"
        toggle = self.page.findChild(QPushButton, "sourceToggle_calcination")
        self.assertIsNotNone(toggle)
        assert toggle is not None
        toggle.click()
        self.page.enterprise_name.setText("缺少物料企业")
        self.page.boundary_confirmed.setChecked(True)
        material = self.page._process_rows["calcination"][0]["materials"][0]
        material["mass"].setText("100")
        self.page._run_calculation()
        self.application.processEvents()

        card = self._card(source_id)
        validation_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertTrue(card.isVisible())
        self.assertIn("必须修正", validation_text)
        self.assertIn("物料名称", validation_text)
        self.assertNotIn("CAR-VAL-", validation_text)
        self.assertEqual(self.page.record_repository.list_all(), ())
        self.assertIsNone(self.page.findChild(QWidget, "showProfessionalDetailsCheckBox"))
        self.assertIsNone(self.page.findChild(QWidget, "calculationValidationProfessionalDetails"))

    def test_heat_domain_error_maps_to_i02_and_recovers_after_recheck(self) -> None:
        toggle = self.page.findChild(QPushButton, "sourceToggle_heat")
        assert toggle is not None
        self.page.enterprise_name.setText("热力状态企业")
        self.page.boundary_confirmed.setChecked(True)
        self.page.period_year.setValue(2026)
        row = self.page._energy_family_rows["heat"][0]
        row.amount.setText("1")
        row.pressure.clear()
        toggle.click()

        self.page._run_calculation()
        self.application.processEvents()

        card = self._card("CAR-SRC-PURCHASED-HEAT-001")
        validation_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertIn("蒸汽状态资料不完整", validation_text)
        self.assertNotIn("CAR-VAL-", validation_text)
        self.assertIs(card.presentation_state, SourceCardPresentationState.NEEDS_ATTENTION)
        self.assertIn("需要处理", card.summary_label.text())
        self.assertEqual(self.page.record_repository.list_all(), ())

        row.enthalpy_mode.setCurrentIndex(row.enthalpy_mode.findData("MANUAL"))
        row.enthalpy.setText("2800")
        self.page._run_calculation()
        self.application.processEvents()

        validation_text = "\n".join(tree_texts(self.page.validation_list))
        self.assertNotIn("CAR-VAL-", validation_text)
        self.assertIs(card.presentation_state, SourceCardPresentationState.COMPLETED)
        self.assertIn("已完成", card.summary_label.text())
        self.assertEqual(len(self.page.record_repository.list_all()), 1)

if __name__ == "__main__":
    unittest.main()
