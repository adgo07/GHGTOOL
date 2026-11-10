"""Focused interaction protection for the presentation-only copy cleanup."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QLabel
from packages.ui.business_page_style import InfoTip
from packages.ui.pages import HomePage, RecordLibraryPage
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.ui.view_models import AppRoute
from tests.test_g07_records import _record
from tests.ui_tree_helpers import dispose_test_widget


class CopyPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_info_tip_mouse_keyboard_and_escape_restore_focus(self):
        tip = InfoTip('导出位置说明', '报告与模板共用此文件夹。')
        tip.show()
        self.app.processEvents()
        self.assertEqual(tip.accessibleName(), '导出位置说明')
        self.assertFalse(tip.popup.isVisible())
        QTest.mouseClick(tip, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertTrue(tip.popup.isVisible())
        QTest.keyClick(tip.close_button, Qt.Key.Key_Escape)
        self.app.processEvents()
        self.assertFalse(tip.popup.isVisible())
        self.assertTrue(tip.hasFocus())
        QTest.keyClick(tip, Qt.Key.Key_Space)
        self.app.processEvents()
        self.assertTrue(tip.popup.isVisible())
        QTest.keyClick(tip.close_button, Qt.Key.Key_Space)
        self.app.processEvents()
        self.assertFalse(tip.popup.isVisible())
        dispose_test_widget(tip)

    def test_first_empty_action_uses_existing_new_accounting_route(self):
        routes = []
        page = RecordLibraryPage(InMemoryRecordRepository(), navigate=routes.append)
        self.assertEqual(page.record_list.item(0, 0).text(), '暂无核算记录')
        self.assertEqual(page.empty_action.text(), '新建核算')
        page.empty_action.click()
        self.assertEqual(routes, [AppRoute.NEW_ACCOUNTING])
        dispose_test_widget(page)

    def test_no_matches_clear_only_filters_and_preserve_record(self):
        repo = InMemoryRecordRepository()
        record = _record('copy.record')
        repo.create(record)
        page = RecordLibraryPage(repo)
        page.search_input.setText('没有匹配的企业')
        self.assertEqual(page.record_list.item(0, 0).text(), '没有匹配的记录')
        self.assertEqual(page.empty_action.text(), '清除筛选')
        page.empty_action.click()
        self.assertEqual(len(page._records), 1)
        self.assertEqual(repo.get(record.record_id), record)
        self.assertEqual(len(repo.list_all()), 1)
        dispose_test_widget(page)

    def test_read_failure_is_distinct_and_retry_recovers_without_writing(self):
        repo = InMemoryRecordRepository()
        repo.create(_record('copy.record'))
        with patch.object(repo, 'list_all', side_effect=OSError('isolated read failure')):
            with self.assertLogs('packages.ui.pages', level='ERROR'):
                page = RecordLibraryPage(repo)
        self.assertEqual(page.record_list.item(0, 0).text(), '记录读取失败')
        self.assertEqual(page.empty_action.text(), '重试')
        self.assertEqual(page.result_count.text(), '记录数量暂不可用')
        self.assertFalse(page.delete_button.isEnabled())
        page.empty_action.click()
        self.assertEqual(len(page._records), 1)
        self.assertFalse(page._record_read_failed)
        self.assertEqual(len(repo.list_all()), 1)
        dispose_test_widget(page)

    def test_home_empty_new_action_and_read_failure_retry(self):
        from apps.carbon_accounting_desktop.product import carbon_accounting_view_model
        repo = InMemoryRecordRepository()
        routes = []
        home = HomePage(carbon_accounting_view_model(), routes.append, record_repository=repo)
        home.refresh_recent_records()
        home.findChild(QPushButton, 'recordRecentStateAction').click()
        self.assertEqual(routes, [AppRoute.NEW_ACCOUNTING])
        with patch.object(repo, 'list_all', side_effect=OSError('isolated home read failure')):
            with self.assertLogs('packages.ui.pages', level='ERROR'):
                home.refresh_recent_records()
        self.assertIn('无法读取', home.findChild(QLabel, 'recordRecentStateTitle').text())
        retry = home.findChild(QPushButton, 'recordRecentStateAction')
        self.assertEqual(retry.text(), '重试')
        retry.click()
        self.assertEqual(home.findChild(QLabel, 'recordRecentStateTitle').text(), '暂无核算记录')
        self.assertEqual(len(repo.list_all()), 0)
        dispose_test_widget(home)
