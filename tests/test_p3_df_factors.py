"""D regression: read-only presentation and complete, reachable provenance."""
import gc
import os
import tempfile
import unittest
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QAbstractItemView, QLabel, QToolButton
from packages.application.catalog_queries import CatalogQueryService
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.catalog_pages import ParameterFactorLibraryPage

class P3DFFactorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.temp = tempfile.TemporaryDirectory()
        cls.service = CatalogQueryService(SQLiteCatalogRepository(
            build_catalog_database(DEFAULT_SOURCE_PATH, Path(cls.temp.name) / "catalog.sqlite")))

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        cls.temp.cleanup()

    def setUp(self):
        self.page = ParameterFactorLibraryPage(self.service, lambda *_: None)
        self.page.resize(1000, 700)
        self.page.show()
        self.app.processEvents()

    def tearDown(self):
        self.page.hide()
        self.page.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        del self.page
        gc.collect()

    def test_registered_source_table_is_read_only_and_full_text_reachable(self):
        page = self.page
        page.source_filter.setCurrentIndex(page.source_filter.findData("SRC-32151-34-2024"))
        page.table_filter.setCurrentIndex(page.table_filter.findText("C.1", Qt.MatchFlag.MatchContains))
        self.assertGreater(page.factor_table.rowCount(), 20)
        self.assertEqual(page.factor_table.editTriggers(), QAbstractItemView.EditTrigger.NoEditTriggers)
        for row in range(page.factor_table.rowCount()):
            for col in range(page.factor_table.columnCount()):
                cell = page.factor_table.item(row, col)
                self.assertEqual(cell.toolTip(), cell.text())
                self.assertFalse(cell.flags() & Qt.ItemFlag.ItemIsEditable)

    def test_search_value_unit_condition_and_keyboard_reachable_trace(self):
        page = self.page
        page.view_mode_filter.setCurrentIndex(page.view_mode_filter.findData("search"))
        page.search_input.setText("0.11")
        self.app.processEvents()
        index = next(i for i, result in enumerate(page._search_results)
                     if result.asset is not None and result.value_text == "0.11")
        result = page._search_results[index]
        page.search_result_table.selectRow(index)
        self.app.processEvents()
        self.assertEqual(page.search_result_table.item(index, 2).text(), result.value_text)
        self.assertEqual(page.search_result_table.item(index, 3).text(), result.unit)
        self.assertIn("适用", page.search_result_table.item(index, 4).text())
        self.assertEqual(page.search_result_table.editTriggers(), QAbstractItemView.EditTrigger.NoEditTriggers)
        toggle = page.findChild(QToolButton, "parameterDetailTraceToggle")
        self.assertIsNotNone(toggle)
        self.assertFalse(toggle.isChecked())
        toggle.setFocus()
        QTest.keyClick(toggle, Qt.Key.Key_Space)
        self.app.processEvents()
        self.assertTrue(toggle.isChecked())
        text = "\n".join(label.text() for label in page.factor_detail_host.findChildren(QLabel))
        for expected in ("0.11", result.unit, "7.5.6", "来源有效期", "数据类型", "原始值"):
            self.assertIn(expected, text)
        self.assertTrue(page.factor_detail_scroll.widgetResizable())
        self.assertGreaterEqual(page.factor_detail_scroll.width(), 320)

    def test_source_filter_and_empty_search_do_not_leave_stale_detail(self):
        page = self.page
        page.view_mode_filter.setCurrentIndex(page.view_mode_filter.findData("search"))
        page.search_input.setText("0.11")
        self.assertGreater(page.search_result_table.rowCount(), 0)
        page.search_input.setText("不存在的参数-P3-DF-空态")
        self.app.processEvents()
        self.assertEqual(page.search_result_table.rowCount(), 0)
        self.assertIn("0", page.result_summary.text())
        labels = page.factor_detail_host.findChildren(QLabel, "emptyStateDescription")
        self.assertTrue(labels)
        self.assertIn("没有找到", labels[-1].text())
