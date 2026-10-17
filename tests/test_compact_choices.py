"""Presentation choices retain typed state, disabled legacy values and keyboard access."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from enum import Enum
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLabel
from packages.ui.compact_choices import SegmentedChoiceControl, TwoChoiceControl

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
        control = SegmentedChoiceControl(combo)
        control.resize(600,60)
        control.show()
        self.app.processEvents()
        first, second, third = control.group.buttons()
        self.assertEqual(first.geometry().right()+1,second.geometry().left())
        self.assertEqual(second.geometry().right()+1,third.geometry().left())
        self.assertEqual(control.row.spacing(),0)
        self.assertEqual(first.height(), second.height())
        self.assertEqual(second.height(), third.height())
        self.assertEqual(first.property("segmentPosition"), "first")
        self.assertEqual(second.property("segmentPosition"), "middle")
        self.assertEqual(third.property("segmentPosition"), "last")
        control.close()

    def test_policy_update_preserves_legacy_value_and_requires_explicit_confirmation(self):
        combo = QComboBox()
        for label, value in (
            ("缺省值", "STANDARD_DEFAULT"),
            ("计算值", "CALCULATED"),
            ("实测值", "MEASURED"),
            ("历史自定义", "USER_DEFINED"),
        ):
            combo.addItem(label, value)
        combo.setCurrentIndex(3)
        control = SegmentedChoiceControl(combo)
        control.show()
        self.app.processEvents()

        class Source(Enum):
            CALCULATED = "CALCULATED"

        control.set_allowed_values((Source.CALCULATED,))
        self.app.processEvents()
        self.assertEqual(combo.currentData(), "USER_DEFINED")
        self.assertEqual(control.notice.text(), "历史来源不适用，请确认")
        self.assertEqual(control.notice.toolTip(), "历史自定义")
        self.assertEqual(len(control.group.buttons()), 1)
        self.assertEqual(control.group.buttons()[0].text(), "计算值")
        allowed_button = control.group.buttons()[0]
        control.set_allowed_values(("CALCULATED",))
        self.assertIs(control.group.buttons()[0], allowed_button)

        control.group.buttons()[0].click()
        self.app.processEvents()
        self.assertEqual(combo.currentData(), "CALCULATED")
        self.assertEqual(control.group.buttons(), [])
        label = control.findChild(QLabel, "singleAllowedChoiceLabel")
        self.assertIsNotNone(label)
        assert label is not None
        self.assertTrue(label.isVisible())
        self.assertEqual(label.text(), "计算值")

        control.set_allowed_values(("MEASURED",))
        self.app.processEvents()
        self.assertEqual(combo.currentData(), "CALCULATED")
        self.assertEqual(len(control.group.buttons()), 1)
        self.assertEqual(control.group.buttons()[0].text(), "实测值")
        control.close()

    def test_no_allowed_source_is_visible_without_changing_combo_state(self):
        combo = QComboBox()
        combo.addItem("缺省值", "STANDARD_DEFAULT")
        combo.setCurrentIndex(0)
        control = SegmentedChoiceControl(combo, values=())
        control.show()
        self.app.processEvents()
        label = control.findChild(QLabel, "singleAllowedChoiceLabel")
        self.assertIsNotNone(label)
        assert label is not None
        self.assertTrue(label.isVisible())
        self.assertFalse(label.isEnabled())
        self.assertEqual(label.text(), "暂无适用来源")
        self.assertEqual(combo.currentData(), "STANDARD_DEFAULT")
        control.close()
