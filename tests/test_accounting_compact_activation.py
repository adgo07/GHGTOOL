"""Small-screen user activation and programmatic navigation stay distinct."""
import unittest
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from PySide6.QtTest import QTest
from tests import test_accounting_projects_ui as fixture


class CompactActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AccountingProjectUiTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.AccountingProjectUiTests.tearDownClass.__func__(cls)

    setUp = fixture.AccountingProjectUiTests.setUp
    tearDown = fixture.AccountingProjectUiTests.tearDown
    _new_page = fixture.AccountingProjectUiTests._new_page

    def test_compact_user_selection_enables_but_navigation_and_supplement_do_not(self):
        page = self.page
        page.resize(570, 800)
        page.show()
        for _ in range(8):
            self.application.processEvents()
        directory = page.source_directory
        self.assertTrue(directory.compact_selector.isVisible())
        combo = directory.compact_selector
        self.assertFalse(directory.navigation_panel.isVisible())
        self.assertEqual(combo.count(), 9)
        page._fuel_rows[0].activity.setText('17.25')
        before = page._capture_form_state()
        directory.select('calcination')
        combo.setCurrentIndex(combo.findData('fuel'))
        self.assertEqual(page._capture_form_state(), before)
        # Use the native popup and Return to emit its user-only activated signal.
        combo.setFocus()
        combo.showPopup()
        view = combo.view()
        view.setCurrentIndex(combo.model().index(combo.findData('fuel'), 0))
        QTest.keyClick(view, Qt.Key.Key_Return)
        for _ in range(8):
            self.application.processEvents()
        self.assertEqual(directory._selected, 'fuel')
        self.assertTrue(page._source_is_enabled('CAR-SRC-FUEL-001'))
        self.assertEqual(page._fuel_rows[0].activity.text(), '17.25')
        saved = page._capture_form_state()
        directory.select('external')
        self.assertEqual(combo.currentData(), 'external')
        self.assertFalse(page.external_included.isChecked())
        self.assertEqual(page._capture_form_state(), saved)
        page.resize(1200, 800)
        for _ in range(16):
            self.application.processEvents()
        self.assertTrue(directory.navigation_panel.isVisible())
        self.assertFalse(combo.isVisible())
        self.assertFalse(self.records.list_all())
