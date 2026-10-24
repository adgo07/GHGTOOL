"""Background isolation: rendering parity, hidden-page events and input routing."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QMainWindow, QVBoxLayout, QWidget
from apps.carbon_accounting_desktop.config import AppConfig
from apps.carbon_accounting_desktop.product import carbon_accounting_view_model
from packages.ui.design_tokens import HOME_CANVAS_GRADIENT, PAGE_BACKGROUND, application_stylesheet
from packages.ui.shell import AppShell
from packages.ui.source_cards import SourceCard
from packages.standards.carbon_material import EmissionSourceStatus
from packages.ui.view_models import AppRoute
from tests.ui_tree_helpers import dispose_test_widget

class NavigationBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = QMainWindow()
        self.window.setStyleSheet(application_stylesheet())
        self.inputs = {}
        def page_factory(route, _model, _navigate, parent):
            page = QWidget(parent)
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel('导航背景等价检查', page))
            field = QLineEdit(page); field.setText('保留草稿')
            self.inputs[route] = field; layout.addWidget(field); layout.addStretch(1)
            layout.addSpacing(1600 if route is AppRoute.NEW_ACCOUNTING else 200)
            return page
        config = AppConfig()
        self.shell = AppShell(carbon_accounting_view_model(), config.logo_path(), config.icons_directory(), page_factory=page_factory)
        self.window.setCentralWidget(self.shell)
        self.window.resize(1280,800); self.window.show(); self.settle()

    def tearDown(self):
        self.window.close()
        dispose_test_widget(self.window)
        self.settle()

    def settle(self):
        for _ in range(4): self.app.processEvents()

    def test_pending_geometry_callback_is_cancelled_when_shell_is_destroyed(self):
        errors = []
        config = AppConfig()
        window = QMainWindow()
        shell = AppShell(
            carbon_accounting_view_model(), config.logo_path(), config.icons_directory(),
            page_factory=lambda _route, _model, _navigate, parent: QWidget(parent),
        )
        window.setCentralWidget(shell)
        # Destroy before the constructor's first queued geometry callback.
        with patch("sys.excepthook", side_effect=lambda kind, value, trace:
                   errors.append(f"{kind.__name__}: {value}")):
            dispose_test_widget(window)
            self.settle()
        self.assertEqual(errors, [])

    def test_source_card_geometry_callback_is_cancelled_with_its_owner(self):
        errors = []
        config = AppConfig()
        window = QMainWindow()
        shell = AppShell(
            carbon_accounting_view_model(), config.logo_path(), config.icons_directory(),
            page_factory=lambda _route, _model, _navigate, parent: QWidget(parent),
        )
        window.setCentralWidget(shell)
        card = SourceCard("callback-test", "排放源回调", shell.page_stack.currentWidget())
        status = QComboBox(card)
        status.addItem("未启用", EmissionSourceStatus.NOT_INVOLVED)
        status.addItem("已启用", EmissionSourceStatus.INVOLVED)
        card.set_status_widget(status, not_involved_value=EmissionSourceStatus.NOT_INVOLVED,
                                   involved_value=EmissionSourceStatus.INVOLVED)
        status.setCurrentIndex(1)
        with patch("sys.excepthook", side_effect=lambda kind, value, trace:
                   errors.append(f"{kind.__name__}: {value}")):
            dispose_test_widget(window)
            self.settle()
        self.assertEqual(errors, [])

    def test_background_changes_do_not_restyle_hidden_editors(self):
        class Probe(QObject):
            changes = 0
            def eventFilter(self, watched, event):
                if event.type() == QEvent.Type.StyleChange: self.changes += 1
                return False
        probe = Probe(self.shell)
        page = self.shell.pages[AppRoute.NEW_ACCOUNTING]
        for widget in (page, *page.findChildren(QWidget)): widget.installEventFilter(probe)
        for route in (AppRoute.STANDARDS, AppRoute.RECORDS, AppRoute.HOME, AppRoute.FACTORS, AppRoute.HOME):
            self.shell.navigate(route); self.settle()
        self.assertEqual(probe.changes,0)
        self.assertEqual(self.inputs[AppRoute.NEW_ACCOUNTING].text(),'保留草稿')

    def test_pixels_match_legacy_background_at_sizes_and_scroll_positions(self):
        # Same already-built UI, same stylesheet token; only background placement differs.
        old_blink = self.app.cursorFlashTime(); self.app.setCursorFlashTime(0)
        try:
            host = self.shell.scroll_host
            canvas = host.background_layer
            # QWidget subclasses need this flag to reproduce the legacy plain QWidget QSS paint.
            host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            for width in (1180,1280,1600):
                self.window.resize(width,800); self.settle()
                for route in (AppRoute.HOME, AppRoute.NEW_ACCOUNTING, AppRoute.RECORDS):
                    self.shell.navigate(route); self.settle()
                    background = HOME_CANVAS_GRADIENT if route is AppRoute.HOME else PAGE_BACKGROUND
                    for bottom in (False,True):
                        bar = self.shell.main_scroll_area.verticalScrollBar()
                        bar.setValue(bar.maximum() if bottom else bar.minimum()); self.settle()
                        canvas.hide()
                        host.setStyleSheet(f'QWidget#scrollHost {{ background: {background}; }}')
                        self.settle()
                        legacy = self.shell.main_scroll_area.viewport().grab().toImage()
                        host.setStyleSheet(''); canvas.show(); host.set_background(background)
                        self.settle()
                        isolated = self.shell.main_scroll_area.viewport().grab().toImage()
                        with self.subTest(width=width,route=route.value,bottom=bottom):
                            self.assertEqual(isolated,legacy)
                            self.assertEqual(canvas.geometry(),host.rect())
        finally:
            self.app.setCursorFlashTime(old_blink)

    def test_background_does_not_intercept_input_or_scroll(self):
        self.shell.navigate(AppRoute.NEW_ACCOUNTING); self.settle()
        canvas = self.shell.scroll_host.background_layer
        self.assertTrue(canvas.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        field = self.inputs[AppRoute.NEW_ACCOUNTING]
        QTest.mouseClick(field,Qt.MouseButton.LeftButton)
        self.assertTrue(field.hasFocus())
        QTest.keyClicks(field,'-edited')
        edited = field.text()
        self.shell.navigate(AppRoute.HOME); self.settle()
        self.shell.navigate(AppRoute.NEW_ACCOUNTING); self.settle()
        self.assertEqual(field.text(),edited)
        bar = self.shell.main_scroll_area.verticalScrollBar(); bar.setValue(bar.maximum()); self.settle()
        self.assertGreater(bar.value(),0)
        self.assertEqual(canvas.geometry(),self.shell.scroll_host.rect())

if __name__ == '__main__': unittest.main()
