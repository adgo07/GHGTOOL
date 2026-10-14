"""Presentation choices retain typed state, disabled legacy values and keyboard access."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox
from packages.ui.compact_choices import TwoChoiceControl

class CompactChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_keyboard_and_restored_value_use_the_same_typed_adapter(self):
        combo = QComboBox()
        for label, value in (("质量", "MASS"), ("体积", "VOLUME"), ("", "HEAT")):
            combo.addItem(label, value)
        control = TwoChoiceControl(combo)
        control.show()
        self.app.processEvents()
        first, second = control.group.buttons()
        first.setFocus()
        QTest.keyClick(first, Qt.Key.Key_Right)
        self.assertTrue(second.isChecked())
        self.assertEqual(combo.currentData(), "VOLUME")
        combo.setCurrentIndex(0)
        self.assertTrue(first.isChecked())
        combo.setCurrentIndex(2)
        self.assertFalse(first.isChecked())
        self.assertFalse(second.isChecked())
        self.assertEqual(combo.currentData(), "HEAT")
        combo.setEnabled(False)
        self.assertFalse(first.isEnabled())
        self.assertFalse(second.isEnabled())
        control.close()

    def test_segment_buttons_stay_connected_in_a_wide_field(self):
        combo = QComboBox()
        combo.addItem("缺省值", "STANDARD_DEFAULT")
        combo.addItem("计算值", "CALCULATED")
        combo.addItem("实测值", "MEASURED")
        from packages.ui.compact_choices import SegmentedChoiceControl
        control = SegmentedChoiceControl(combo)
        control.resize(600,60)
        control.show()
        self.app.processEvents()
        first, second, third = control.group.buttons()
        self.assertEqual(first.geometry().right()+1,second.geometry().left())
        self.assertEqual(second.geometry().right()+1,third.geometry().left())
        self.assertEqual(control.row.spacing(),0)
        control.close()
