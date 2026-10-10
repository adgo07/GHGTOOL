"""Presentation checks for the unified Appendix B import page."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QFrame

from packages.application.project_workspaces import AccountingUnitType
from packages.core.models import AccountingPeriod, PeriodType
from packages.excel.ingress import (
    ImportMessage,
    WorkbookFatalError,
    WorkbookImportPreview,
    WorkbookProvenance,
    UnitCalculationPreview,
)
from packages.excel.templates import ExcelTemplateService
from packages.standards.carbon_material import CarbonMaterialInput
from packages.ui.pages import ExcelImportPage


class P3EExcelImportPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.page = ExcelImportPage()

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_page_has_four_compact_zones_and_separate_file_selection_from_preview(self) -> None:
        for name in (
            "excelImportTemplateSection",
            "excelImportFileSection",
            "excelImportCheckSection",
            "excelImportActionSection",
        ):
            self.assertIsNotNone(self.page.findChild(QFrame, name))

        source = Path("selected workbook.xlsx")
        with patch("packages.ui.pages.QFileDialog.getOpenFileName", return_value=(str(source), "Excel 工作簿 (*.xlsx)")) as dialog:
            self.page._choose_workbook()
        self.assertEqual(dialog.call_args.args[-1], "Excel 工作簿 (*.xlsx)")
        self.assertIsNone(self.page._last_preview)
        self.assertEqual(self.page.selected_file_label.text(), source.name)
        self.assertTrue(self.page.preview_button.isEnabled())
        with patch.object(self.page, "_preview_workbook") as preview:
            self.page.preview_button.click()
            preview.assert_called_once_with(source)

    def test_template_download_copies_exact_approved_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "approved-copy.xlsx"
            with (
                patch(
                    "packages.ui.pages.QFileDialog.getSaveFileName",
                    return_value=(str(destination), "Excel 工作簿 (*.xlsx)"),
                ),
                patch("packages.ui.pages.QMessageBox.information"),
            ):
                self.page.templateButton.click()
            self.assertEqual(destination.read_bytes(), ExcelTemplateService.default().read_bytes())

    def test_mixed_preview_shows_each_unit_and_cell_location(self) -> None:
        provenance = WorkbookProvenance(
            workbook_sha256="a" * 64,
            template_id="approved-template",
            template_version="1.0.0",
            standard_id="GB/T 32151.34",
            standard_version="2024",
            ingress_policy_id="appendix-b",
            imported_at=datetime.now(timezone.utc),
        )
        valid = UnitCalculationPreview(
            unit_id="unit-1",
            name="有效单元",
            unit_type=AccountingUnitType.WHOLE_SITE,
            input_value=object(),
            calculation=SimpleNamespace(
                successful=True,
                result=SimpleNamespace(total_amount=Decimal("2.345"), total_unit="tCO2"),
            ),
        )
        invalid = UnitCalculationPreview(
            unit_id="unit-2",
            name="需修正单元",
            unit_type=AccountingUnitType.PROCESS,
            input_value=None,
            calculation=None,
            errors=(ImportMessage("EXB01_CELL_INVALID", "请输入有效数值。", "B.2!B14", "活动量"),),
        )
        preview = WorkbookImportPreview(
            provenance=provenance,
            units=(valid, invalid),
            warnings=(ImportMessage("EXB01_NOTE", "该表有待确认信息。", "B.8!C4", "电量"),),
            numeric_evidence=(),
        )
        self.page._last_preview = preview
        self.page._render_import_preview(preview)

        self.assertEqual(self.page.preview_panel.units.rowCount(), 2)
        self.assertIn("1 个可保存", self.page.preview_panel.summary.text())
        self.assertEqual(self.page.preview_panel.units.item(0, 2).text(), "2.35 tCO₂")
        self.page.preview_panel.units.setCurrentCell(1, 0)
        self.app.processEvents()
        details = self.page.preview_text.toPlainText()
        self.assertIn("B.2!B14", details)
        self.assertIn("活动量", details)
        self.assertIn("B.8!C4", details)
        self.assertIn("不会保存项目或生成正式记录", details)

    def test_saving_a_mixed_preview_keeps_only_valid_units_as_a_project(self) -> None:
        class ProjectService:
            def __init__(self) -> None:
                self.saved = None

            def save(self, workspace) -> None:
                self.saved = workspace

            def list_all(self):
                return (self.saved,) if self.saved is not None else ()

        period = AccountingPeriod(
            period_type=PeriodType.ANNUAL,
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )
        canonical = CarbonMaterialInput(
            input_id="input.p3e",
            enterprise_id="enterprise.p3e",
            enterprise_name="示例企业",
            period=period,
            boundary_confirmed=True,
        )
        provenance = WorkbookProvenance(
            workbook_sha256="b" * 64,
            template_id="approved-template",
            template_version="1.0.0",
            standard_id="GB/T 32151.34",
            standard_version="2024",
            ingress_policy_id="appendix-b",
            imported_at=datetime.now(timezone.utc),
        )
        valid = UnitCalculationPreview(
            unit_id="unit-valid",
            name="有效单元",
            unit_type=AccountingUnitType.WHOLE_SITE,
            input_value=canonical,
            calculation=SimpleNamespace(
                successful=True,
                result=SimpleNamespace(total_amount=Decimal("1"), total_unit="tCO2"),
            ),
        )
        invalid = UnitCalculationPreview(
            unit_id="unit-invalid",
            name="无效单元",
            unit_type=AccountingUnitType.PROCESS,
            input_value=None,
            calculation=None,
            errors=(ImportMessage("EXB01_CELL_INVALID", "缺少数据。", "B.3!C5", "物料量"),),
        )
        preview = WorkbookImportPreview(
            provenance=provenance,
            units=(valid, invalid),
            warnings=(),
            numeric_evidence=(),
        )
        project_service = ProjectService()
        self.page.project_service = project_service
        self.page.import_enterprise_name.setText("示例企业")
        self.page.import_period_type.setCurrentIndex(
            self.page.import_period_type.findData(PeriodType.ANNUAL.value)
        )
        self.page.import_period_start.setText("2025-01-01")
        self.page.import_period_end.setText("2025-12-31")
        self.page.import_boundary_confirmed.setChecked(True)
        self.page._last_preview = preview
        self.page._last_workbook_path = Path("mixed.xlsx")
        self.page._chosen_workbook_path = Path("mixed.xlsx")
        self.page._preview_context_key = self.page._import_context_key()

        with patch.object(self.page, "open_project", return_value=True):
            self.page._save_preview_as_project()

        self.assertIsNotNone(project_service.saved)
        self.assertEqual([unit.name for unit in project_service.saved.units], ["有效单元"])
        self.assertIn("1 个无效单元未保存", self.page.status_label.text())
        self.assertIsNone(self.page._last_preview)

    def test_workbook_check_failure_is_visible_inline_without_modal(self) -> None:
        self.page.import_period_type.setCurrentIndex(
            self.page.import_period_type.findData("ANNUAL")
        )
        self.page.import_period_start.setText("2025-01-01")
        self.page.import_period_end.setText("2025-12-31")
        self.page.import_boundary_confirmed.setChecked(True)
        source = Path("broken.xlsx")
        with (
            patch(
                "packages.excel.appendix_b.AppendixBWorkbookImporter.import_preview",
                side_effect=WorkbookFatalError("B.2!A3 表头不匹配。"),
            ),
            patch("packages.ui.pages.QMessageBox.warning") as warning,
        ):
            self.page._preview_workbook(source)
        self.assertIn("B.2!A3", self.page.preview_text.toPlainText())
        self.assertIn("无法预览", self.page.status_label.text())
        warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
