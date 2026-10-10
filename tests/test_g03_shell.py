from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
)

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.product import carbon_accounting_view_model
from packages.application.project_workspaces import ProjectWorkspaceService
from packages.persistence import SQLiteProjectWorkspaceRepository
import packages.ui.shell as shell_module
from packages.ui.design_tokens import BRAND_AREA_HEIGHT, SIDEBAR_WIDTH
from packages.ui.shell import AppShell
from packages.core.models import PeriodType
from packages.standards.carbon_material import FuelPath
from packages.ui.view_models import AppRoute
from packages.persistence.in_memory_records import InMemoryRecordRepository


class G03ShellTest(unittest.TestCase):
    @classmethod

    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._project_directory = tempfile.TemporaryDirectory()
        project_repository = SQLiteProjectWorkspaceRepository(
            Path(self._project_directory.name) / "projects.sqlite"
        )
        self.project_service = ProjectWorkspaceService(project_repository)
        self.window = create_main_window(
            record_repository=InMemoryRecordRepository(),
            project_service=self.project_service,
        )
        self.window.show()
        self.application.processEvents()
        self.shell = self.window.centralWidget()
        self.assertIsInstance(self.shell, AppShell)

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()
        self._project_directory.cleanup()

    def test_shell_starts_on_home_without_sidebar_and_uses_navigation_order(self) -> None:
        shell = self.shell
        sidebar = shell.findChild(QWidget, "sidebar")
        self.assertIsNotNone(sidebar)
        assert sidebar is not None
        self.assertEqual(sidebar.width(), SIDEBAR_WIDTH)
        self.assertTrue(sidebar.isHidden())
        self.assertEqual(
            [button.text() for button in shell.navigation_buttons.values()],
            [
                "首页",
                "标准库",
                "新建核算",
                "表格导入",
                "核算记录",
                "参数与因子库",
                "设置",
            ],
        )
        self.assertTrue(shell.navigation_buttons[AppRoute.HOME].isChecked())
        self.assertFalse(shell.navigation_buttons[AppRoute.EXCEL_IMPORT].property("reserved"))
        shell.navigate(AppRoute.STANDARDS)
        self.application.processEvents()
        self.assertFalse(sidebar.isHidden())
        settings_y = shell.navigation_buttons[AppRoute.SETTINGS].mapTo(sidebar, QPoint(0, 0)).y()
        factors_y = shell.navigation_buttons[AppRoute.FACTORS].mapTo(sidebar, QPoint(0, 0)).y()
        self.assertGreater(settings_y, factors_y)

    def test_home_is_a_safe_empty_workbench(self) -> None:
        home = self.shell.pages[AppRoute.HOME]
        self.assertEqual(home.findChild(QLabel, "pageTitle").text(), "温室气体排放核算")
        self.assertIsNotNone(home.findChild(QWidget, "primaryWorkspace"))
        self.assertIsNotNone(home.findChild(QWidget, "startPanel"))
        self.assertIsNotNone(home.findChild(QWidget, "recentWorkCard"))
        self.assertIsNotNone(home.findChild(QWidget, "recentProjectsCard"))
        self.assertIsNotNone(home.findChild(QWidget, "recentRecordsCard"))
        self.assertIsNone(home.findChild(QWidget, "recentStandardsCard"))
        self.assertEqual(home.findChild(QLabel, "projectRecentStateTitle").text(), "暂无已保存项目")
        self.assertEqual(home.findChild(QLabel, "recordRecentStateTitle").text(), "暂无核算记录")
        self.assertIn("新建核算", home.findChild(QLabel, "projectRecentStateDescription").text())
        self.assertIn("完成一次正式核算后", home.findChild(QLabel, "recordRecentStateDescription").text())
        self.assertEqual(
            home.findChild(QLabel, "statusSummary").text(),
            "成功核算后可在“核算记录”查看结果与来源依据。",
        )
        all_text = "\n".join(widget.text() for widget in home.findChildren(QLabel))
        self.assertNotIn("企业数量", all_text)
        self.assertNotIn("排行榜", all_text)
        self.assertNotIn("最近使用标准", all_text)

    def test_home_actions_follow_the_five_entry_order_with_settings_separate(self) -> None:
        home = self.shell.pages[AppRoute.HOME]
        self.assertEqual(
            [(route, button.text()) for route, button in home.entry_buttons.items()],
            [
                (AppRoute.STANDARDS, "标准库"),
                (AppRoute.NEW_ACCOUNTING, "新建核算"),
                (AppRoute.EXCEL_IMPORT, "表格导入"),
                (AppRoute.RECORDS, "核算记录"),
                (AppRoute.FACTORS, "参数与因子库"),
            ],
        )
        settings = home.findChild(QPushButton, "homeSettingsButton")
        self.assertIsNotNone(settings)
        assert settings is not None
        self.assertEqual(settings.text(), "设置")
        self.assertNotIn(AppRoute.SETTINGS, home.entry_buttons)
        for button in home.entry_buttons.values():
            self.assertFalse(button.icon().isNull())

    def test_shell_scopes_light_sidebar_styling_without_changing_global_tokens(self) -> None:
        shell_source = Path(shell_module.__file__).read_text(encoding="utf-8")
        self.assertIn("BRAND_AREA_HEIGHT", shell_source)
        self.assertIn("NAV_ITEM_RADIUS", shell_source)
        self.assertIn("_SIDEBAR_BACKGROUND", shell_source)
        self.assertNotIn("setFixedHeight(120)", shell_source)

        brand_area = self.shell.findChild(QWidget, "brandArea")
        self.assertIsNotNone(brand_area)
        assert brand_area is not None
        self.assertEqual(brand_area.height(), BRAND_AREA_HEIGHT)
        sidebar = self.shell.findChild(QWidget, "sidebar")
        self.assertIn("#EAF3FB", sidebar.styleSheet())

    def test_all_routes_are_reachable_and_home_actions_share_routes(self) -> None:
        shell = self.shell
        page_instances = dict(shell.pages)
        sidebar = shell.findChild(QWidget, "sidebar")
        for route in AppRoute:
            shell.navigate(route)
            self.application.processEvents()
            self.assertEqual(shell.current_route, route)
            self.assertIs(shell.page_stack.currentWidget(), page_instances[route])
            self.assertIs(shell.pages[route], page_instances[route])
            self.assertEqual(sidebar.isHidden(), route is AppRoute.HOME)
            if route is not AppRoute.HOME:
                self.assertTrue(shell.navigation_buttons[route].isChecked())

        home = shell.pages[AppRoute.HOME]
        for route in (
            AppRoute.STANDARDS,
            AppRoute.NEW_ACCOUNTING,
            AppRoute.EXCEL_IMPORT,
            AppRoute.RECORDS,
            AppRoute.FACTORS,
        ):
            shell.navigate(AppRoute.HOME)
            home.entry_buttons[route].click()
            self.assertEqual(shell.current_route, route)
            self.assertIs(shell.pages[route], page_instances[route])

        shell.navigate(AppRoute.HOME)
        home.findChild(QPushButton, "homeSettingsButton").click()
        self.assertEqual(shell.current_route, AppRoute.SETTINGS)
        self.assertTrue(shell.navigation_buttons[AppRoute.SETTINGS].isChecked())

    def test_excel_appendix_b_page_exposes_required_context_and_explicit_workflow_controls(self) -> None:
        shell = self.shell
        shell.navigate(AppRoute.EXCEL_IMPORT)
        page = shell.pages[AppRoute.EXCEL_IMPORT]
        self.assertEqual(page.findChild(QLabel, "pageTitle").text(), "表格导入")
        self.assertEqual(AppRoute.EXCEL_IMPORT.value, "excel_import")
        self.assertIn("模板与预览", page.findChild(QLabel, "cardTitle").text())
        self.assertTrue(page.findChild(QPushButton, "templateButton").isEnabled())
        self.assertIn("附录 B", page.findChild(QPushButton, "templateButton").text())
        self.assertNotIn("R2", page.findChild(QPushButton, "templateButton").text())
        self.assertTrue(page.findChild(QPushButton, "selectFileButton").isEnabled())
        self.assertTrue(page.findChild(QTextEdit, "excelImportPreview").isReadOnly())
        self.assertIsNotNone(page.findChild(QComboBox, "importPeriodType"))
        self.assertIsNotNone(page.findChild(QLineEdit, "importPeriodStart"))
        self.assertIsNotNone(page.findChild(QLineEdit, "importPeriodEnd"))
        self.assertIsNotNone(page.findChild(QComboBox, "importRegion"))
        self.assertFalse(page.findChild(QCheckBox, "importBoundaryConfirmed").isChecked())
        self.assertIsNotNone(page.findChild(QPushButton, "saveExcelProjectButton"))
        self.assertIsNotNone(page.findChild(QPushButton, "formalCalculateButton"))
        self.assertIsNotNone(page.findChild(QPushButton, "openUnitRecordButton"))
        self.assertIsNone(page.findChild(QPushButton, "importButton"))

    def test_home_recent_work_lists_only_saved_projects_and_keeps_existing_project_manager(self) -> None:
        workspace = ProjectWorkspaceService.new_workspace("已保存的真实项目")
        self.project_service.save(workspace)
        home = self.shell.pages[AppRoute.HOME]
        home.refresh_recent_records()
        self.application.processEvents()

        project_labels = home.findChildren(QLabel, "recentProjectLabel")
        self.assertEqual([label.text() for label in project_labels], ["已保存的真实项目"])
        self.assertEqual(self.project_service.get(workspace.project_id), workspace)
        self.assertIsNotNone(home.findChild(QLabel, "recordRecentStateTitle"))
        self.assertIsNone(home.findChild(QWidget, "recentStandardsCard"))

    def test_import_context_is_explicit_and_context_edits_invalidate_old_preview(self) -> None:
        self.shell.navigate(AppRoute.EXCEL_IMPORT)
        page = self.shell.pages[AppRoute.EXCEL_IMPORT]
        self.assertIsNone(page.import_period_type.currentData())
        self.assertEqual(page.import_period_start.text(), "")
        self.assertEqual(page.import_period_end.text(), "")
        self.assertFalse(page.import_boundary_confirmed.isChecked())

        page.import_period_type.setCurrentIndex(page.import_period_type.findData(PeriodType.ANNUAL))
        page.import_period_start.setText("2025-01-01")
        page.import_period_end.setText("2025-12-31")
        page.import_boundary_confirmed.setChecked(True)
        page._last_preview = object()
        page._preview_context_key = page._import_context_key()
        self.assertIsNotNone(page._preview_context_key)

        page.import_region.setCurrentIndex(0)
        page.import_boundary_confirmed.setChecked(False)
        self.assertIsNone(page._last_preview)
        self.assertIsNone(page._preview_context_key)
        self.assertIn("重新预览", page.preview_text.toPlainText())

    def test_ambiguous_fuel_path_has_no_default_and_requires_a_user_choice(self) -> None:
        self.shell.navigate(AppRoute.EXCEL_IMPORT)
        page = self.shell.pages[AppRoute.EXCEL_IMPORT]
        error = SimpleNamespace(
            code="EXB01_FUEL_PATH_REQUIRED",
            location="B.2!B4",
            field_label="燃料“其他能源品种”的消耗量单位",
        )
        page._show_fuel_path_choices(
            SimpleNamespace(units=(SimpleNamespace(errors=(error,)),))
        )

        selector = page.fuel_override_panel.findChild(QComboBox, "fuelPathOverride_B_2_B4")
        self.assertIsNotNone(selector)
        self.assertIsNone(selector.currentData())
        retry = page.fuel_override_panel.findChild(QPushButton, "retryFuelPathPreviewButton")
        self.assertFalse(retry.isEnabled())
        selector.setCurrentIndex(selector.findData(FuelPath.MASS))
        self.assertIs(page._fuel_path_from_widget(selector.currentData()), FuelPath.MASS)
        self.assertTrue(retry.isEnabled())

    def test_logo_and_main_content_resize_rules(self) -> None:
        shell = self.shell
        logo = shell.findChild(QLabel, "brandLogo")
        self.assertIsNotNone(logo)
        assert logo is not None
        pixmap = logo.pixmap()
        self.assertIsNotNone(pixmap)
        assert pixmap is not None
        self.assertFalse(pixmap.isNull())
        home_logo = shell.pages[AppRoute.HOME].findChild(QLabel, "homeLogo")
        self.assertIsNotNone(home_logo)
        assert home_logo is not None
        self.assertIsNotNone(home_logo.pixmap())
        self.assertFalse(home_logo.pixmap().isNull())
        self.assertLessEqual(pixmap.width(), 176)
        self.assertLessEqual(pixmap.height(), 44)
        self.assertAlmostEqual(pixmap.width() / pixmap.height(), 4.03, delta=0.15)
        self.assertEqual(shell.main_scroll_area.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assertGreaterEqual(self.window.minimumWidth(), 1180)
        self.assertGreaterEqual(self.window.minimumHeight(), 720)

        self.window.resize(1180, 720)
        self.application.processEvents()
        self.assertEqual(shell.pages[AppRoute.HOME].body_layout.contentsMargins().left(), 24)
        self.window.resize(1920, 1080)
        self.application.processEvents()
        self.assertEqual(shell.pages[AppRoute.HOME].body_layout.contentsMargins().left(), 32)

    def test_product_view_model_has_only_empty_g03_data(self) -> None:
        view_model = carbon_accounting_view_model()
        self.assertEqual(tuple(item.route for item in view_model.navigation), tuple(AppRoute))
        self.assertEqual(view_model.recent_records, ())
        self.assertEqual(view_model.recent_standards, ())
        self.assertNotIn("sqlite", view_model.home_description.lower())


if __name__ == "__main__":
    unittest.main()
