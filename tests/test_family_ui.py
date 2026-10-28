"""Focused presentation regressions for the Owner's family UI baseline."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPointF, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QFontDatabase, QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QTableWidgetItem
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.core.models import Settings, SettingEntry
from packages.persistence import SQLiteSettingsRepository
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.ui.branding import BrandLogo
from packages.ui.business_page_style import ReadableTable
from packages.ui.export_location import ExportLocationService
from packages.ui.icons import load_tinted_icon
from packages.ui.view_models import AppRoute
from packages.ui.window_geometry import KEY, WindowGeometry, bounded_geometry

class FamilyUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        # Offscreen Qt does not enumerate installed Windows Chinese fonts.
        for name in ('msyh.ttc', 'msyhbd.ttc', 'seguisym.ttf'):
            QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repo = SQLiteSettingsRepository(Path(self.directory.name)/'user.sqlite')
        self.window = create_main_window(record_repository=InMemoryRecordRepository(),
            export_location_service=ExportLocationService(self.repo))
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.hide()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def test_small_screen_and_missing_screen_fit_including_frame(self):
        for area in (QRect(0,0,1920,1040), QRect(0,0,1024,768), QRect(-800,0,800,560)):
            rect=bounded_geometry(QRect(9000,5000,1280,800),area,16,39)
            self.assertTrue(area.contains(QRect(rect.topLeft(), QSize(rect.width()+16,rect.height()+39))))

    def test_first_launch_and_restore_normal_and_maximized(self):
        self.assertFalse(self.window.isMaximized())
        self.assertTrue(self.window.screen().availableGeometry().contains(self.window.frameGeometry()))
        self.window.move(20,30)
        self.window.window_geometry.save()
        saved=json.loads(next(e.value for e in self.repo.load().entries if e.key==KEY))
        self.assertFalse(saved['maximized'])
        self.window.showMaximized(); self.app.processEvents()
        self.window.window_geometry.save()
        saved=json.loads(next(e.value for e in self.repo.load().entries if e.key==KEY))
        self.assertTrue(saved['maximized'])
        restored=__import__('PySide6.QtWidgets',fromlist=['QMainWindow']).QMainWindow()
        controller=WindowGeometry(restored,self.repo)
        restored.show(); controller.shown(); self.app.processEvents()
        self.assertTrue(restored.isMaximized())
        restored.hide(); restored.deleteLater()

    def test_corrupt_preferences_never_break_window_startup(self):
        for raw in ('[1,2]', '1', '"text"', '{"normal":null}', '{"normal":[0,0,1e90,4]}', 'broken'):
            with self.subTest(raw=raw):
                self.repo.save(Settings('user.settings',(SettingEntry(KEY,raw),)))
                controller=WindowGeometry(self.window,self.repo)
                self.assertTrue(controller._first_launch)
                controller.deleteLater()

    def test_settings_retains_entry_context_and_safe_return(self):
        shell=self.window.centralWidget()
        shell.navigate(AppRoute.SETTINGS); self.app.processEvents()
        self.assertTrue(shell._sidebar.isHidden())
        settings=shell.pages[AppRoute.SETTINGS]
        self.assertTrue(settings.home_back_button.isVisible())
        settings.home_back_button.click(); self.assertEqual(shell.current_route,AppRoute.HOME)
        shell.navigate(AppRoute.STANDARDS); shell.navigate(AppRoute.SETTINGS); self.app.processEvents()
        self.assertFalse(shell._sidebar.isHidden())
        self.assertFalse(settings.home_back_button.isVisible())
        self.assertTrue(all(b.height()==46 for b in shell.navigation_buttons.values()))

    def test_shared_input_outer_size_precision_focus_and_wheel(self):
        shell=self.window.centralWidget(); shell.navigate(AppRoute.NEW_ACCOUNTING)
        page=shell.pages[AppRoute.NEW_ACCOUNTING]; page.project_unit_toggle.setChecked(True)
        self.app.processEvents()
        for name in ('accountingProjectName','accountingUnitSelector','enterpriseNameInput','accountingPeriodYear','accountingPeriodType','externalAmount'):
            widget=page.findChild(__import__('PySide6.QtWidgets',fromlist=['QWidget']).QWidget,name)
            with self.subTest(name=name): self.assertEqual(widget.height(),40)
        field=page.findChild(QLineEdit,'externalAmount')
        text='123.1234567890123456789012345678901234567'
        field.setText(text); field.setFocus(); self.app.processEvents()
        self.assertEqual(field.text(),text); self.assertEqual(field.height(),40)
        field.clear(); self.assertEqual(field.text(),'')
        combo=page.findChild(QComboBox,'accountingPeriodType'); index=combo.currentIndex()
        event=QWheelEvent(QPointF(4,4),QPointF(4,4),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
        QApplication.sendEvent(combo,event); self.assertEqual(combo.currentIndex(),index)

    def test_primary_disabled_and_focus_keep_geometry_and_color(self):
        button=QPushButton('开始核算',self.window.centralWidget()); button.setObjectName('primaryButton')
        button.show(); button.ensurePolished(); button.adjustSize()
        height=button.height(); self.assertEqual(height,40)
        button.setEnabled(False); self.app.processEvents(); self.assertEqual(button.height(),height)
        # Disabled primary must resolve to gray rather than white text on blue.
        color=button.palette().buttonText().color().name()
        self.assertEqual(color,'#8798a6')
        button.setEnabled(True); button.setFocus(); self.app.processEvents(); self.assertEqual(button.height(),height)

    def test_wrapped_chinese_rows_grow_without_clipping(self):
        table=ReadableTable(self.window.centralWidget()); table.setColumnCount(1); table.setRowCount(1)
        table.setColumnWidth(0,180); table.setItem(0,0,QTableWidgetItem('这是需要完整显示的中文标准名称与核算说明'*8))
        table.resizeRowsToContents()
        self.assertGreater(table.rowHeight(0),48)
        self.assertGreaterEqual(table.rowHeight(0),table.sizeHintForRow(0))
        table.deleteLater()

    def test_compact_directory_navigation_preserves_business_source_state(self):
        shell=self.window.centralWidget(); shell.navigate(AppRoute.NEW_ACCOUNTING)
        page=shell.pages[AppRoute.NEW_ACCOUNTING]
        self.window.setMinimumWidth(0); self.window.resize(600,600)
        for _ in range(4): self.app.processEvents()
        directory=page.source_directory
        self.assertTrue(directory.compact_selector.isVisible())
        self.assertTrue(directory.navigation_panel.isHidden())
        self.assertGreater(directory.editor_scroll.horizontalScrollBar().maximum(),0)
        before={key:widget.currentIndex() for key,widget in page._source_statuses.items()}
        saved_form=page._capture_form_state()
        dirty=(page._project_dirty,page._input_dirty)
        index=directory.compact_selector.findData('fume')
        directory.compact_selector.activated.emit(index)
        self.app.processEvents()
        self.assertEqual(directory._selected,'fume')
        self.assertEqual(before,{key:widget.currentIndex() for key,widget in page._source_statuses.items()})
        self.assertEqual(saved_form,page._capture_form_state())
        self.assertEqual(dirty,(page._project_dirty,page._input_dirty))
        self.assertNotIn('compactSourceDirectory',saved_form)

    def test_logo_original_hash_and_vector_dpr(self):
        import hashlib
        logo_path=AppConfig().logo_path()
        self.assertEqual(hashlib.sha256(logo_path.read_bytes()).hexdigest(),'db557a6374a928b46bd3ab499c0a295ef147e87d79a273d1fde1f2d61f8bc24d')
        logo=BrandLogo(logo_path)
        with patch.object(BrandLogo,'devicePixelRatioF',return_value=2.0), patch.object(BrandLogo,'setPixmap',wraps=logo.setPixmap) as setter:
            logo.refresh_pixmap()
            rendered=setter.call_args.args[0]
            self.assertEqual(rendered.width(),360)
            self.assertEqual(rendered.devicePixelRatioF(),2.0)
        icon=load_tinted_icon(AppConfig().icons_directory()/'home.svg','#116FAE')
        pixmap=icon.pixmap(QSize(18,18),2.0)
        self.assertEqual(pixmap.size(),QSize(36,36)); self.assertEqual(pixmap.devicePixelRatioF(),2.0)
        self.assertEqual(pixmap.toImage().pixelColor(0,0).alpha(),0)
        logo.deleteLater()

if __name__=='__main__': unittest.main()
