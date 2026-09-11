from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QWidget,
)

from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.product import carbon_accounting_view_model
from packages.ui.design_tokens import SIDEBAR_WIDTH
from packages.ui.shell import AppShell
from packages.ui.view_models import AppRoute


class G03ShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = create_main_window()
        self.window.show()
        self.application.processEvents()
        self.shell = self.window.centralWidget()
        self.assertIsInstance(self.shell, AppShell)

    def tearDown(self) -> None:
        self.window.close()
        self.application.processEvents()

    def test_shell_uses_frozen_sidebar_and_navigation_order(self) -> None:
        shell = self.shell
        sidebar = shell.findChild(QWidget, "sidebar")
        self.assertIsNotNone(sidebar)
        assert sidebar is not None
        self.assertEqual(sidebar.width(), SIDEBAR_WIDTH)
        self.assertEqual(
            [button.text() for button in shell.navigation_buttons.values()],
            [
                "首页",
                "标准库",
                "新建核算",
                "Excel 导入（暂未开放）",
                "核算记录",
                "参数与因子库",
                "设置",
            ],
        )
        self.assertTrue(shell.navigation_buttons[AppRoute.HOME].isChecked())
        self.assertTrue(shell.navigation_buttons[AppRoute.EXCEL_IMPORT].property("reserved"))
        settings_y = shell.navigation_buttons[AppRoute.SETTINGS].mapTo(sidebar, QPoint(0, 0)).y()
        factors_y = shell.navigation_buttons[AppRoute.FACTORS].mapTo(sidebar, QPoint(0, 0)).y()
        self.assertGreater(settings_y, factors_y)

    def test_home_is_a_safe_empty_workbench(self) -> None:
        home = self.shell.pages[AppRoute.HOME]
        self.assertEqual(home.findChild(QLabel, "pageTitle").text(), "温室气体排放核算")
        self.assertIsNotNone(home.findChild(QWidget, "primaryWorkspace"))
        self.assertIsNotNone(home.findChild(QWidget, "startPanel"))
        self.assertIsNotNone(home.findChild(QWidget, "recentWorkCard"))
        self.assertIsNotNone(home.findChild(QWidget, "recentStandardsCard"))
        self.assertEqual(home.findChild(QLabel, "emptyStateTitle").text(), "尚无核算记录")
        self.assertEqual(home.findChild(QLabel, "emptyStateDescription").text().splitlines()[0], "可以通过“新建核算”手工开始。")
        self.assertEqual(home.findChild(QLabel, "statusSummary").text(), "暂无核算记录 · 暂无企业 · 暂无待处理事项")
        all_text = "\n".join(widget.text() for widget in home.findChildren(QLabel))
        self.assertNotIn("企业数量", all_text)
        self.assertNotIn("排行榜", all_text)

    def test_all_routes_are_reachable_and_home_actions_share_routes(self) -> None:
        shell = self.shell
        for route in AppRoute:
            shell.navigate(route)
            self.application.processEvents()
            self.assertEqual(shell.current_route, route)
            self.assertIs(shell.page_stack.currentWidget(), shell.pages[route])

        shell.navigate(AppRoute.HOME)
        home = shell.pages[AppRoute.HOME]
        home.findChild(QPushButton, "primaryButton").click()
        self.assertEqual(shell.current_route, AppRoute.NEW_ACCOUNTING)
        shell.navigate(AppRoute.HOME)
        home.findChild(QPushButton, "secondaryButton").click()
        self.assertEqual(shell.current_route, AppRoute.STANDARDS)
        shell.navigate(AppRoute.HOME)
        home.findChild(QPushButton, "reservedButton").click()
        self.assertEqual(shell.current_route, AppRoute.EXCEL_IMPORT)

    def test_excel_placeholder_has_no_enabled_import_control(self) -> None:
        shell = self.shell
        shell.navigate(AppRoute.EXCEL_IMPORT)
        page = shell.pages[AppRoute.EXCEL_IMPORT]
        self.assertIn("功能预留，当前版本暂未开放", page.findChild(QLabel, "cardTitle").text())
        controls = page.findChild(QWidget, "disabledImportControls")
        self.assertIsNotNone(controls)
        assert controls is not None
        self.assertFalse(controls.isEnabled())
        for widget in (
            *page.findChildren(QLineEdit),
            *page.findChildren(QComboBox),
            *page.findChildren(QPushButton),
        ):
            self.assertFalse(widget.isEnabled(), widget.objectName())
            self.assertEqual(widget.focusPolicy(), Qt.FocusPolicy.NoFocus)

    def test_logo_and_main_content_resize_rules(self) -> None:
        shell = self.shell
        logo = shell.findChild(QLabel, "brandLogo")
        self.assertIsNotNone(logo)
        assert logo is not None
        pixmap = logo.pixmap()
        self.assertIsNotNone(pixmap)
        assert pixmap is not None
        self.assertFalse(pixmap.isNull())
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
