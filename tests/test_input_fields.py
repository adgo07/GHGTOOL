from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit

from packages.ui.input_fields import (
    FIELD_TITLE_OBJECT_NAME,
    FIELD_UNIT_HINT_OBJECT_NAME,
    labeled_field,
    set_labeled_field_visible,
)


class LabeledFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_title_is_a_visible_label_separate_from_control_hint(self) -> None:
        control = QLineEdit()
        control.setPlaceholderText("输入压力")
        field = labeled_field("蒸汽绝压", control, "kPa")
        field.show()
        self.application.processEvents()

        title = field.findChild(QLabel, FIELD_TITLE_OBJECT_NAME)
        unit = field.findChild(QLabel, FIELD_UNIT_HINT_OBJECT_NAME)
        self.assertIsNotNone(title)
        self.assertEqual(title.text(), "蒸汽绝压")
        self.assertIs(title.buddy(), control)
        self.assertEqual(unit.text(), "kPa")
        self.assertNotEqual(title.text(), control.placeholderText())
        self.assertTrue(title.isVisible())
        self.assertTrue(control.isVisible())
        field.close()

    def test_hiding_and_showing_the_field_keeps_title_and_control_together(self) -> None:
        control = QLineEdit()
        field = labeled_field("炉窑温度", control)
        field.show()
        self.application.processEvents()
        title = field.findChild(QLabel, FIELD_TITLE_OBJECT_NAME)

        set_labeled_field_visible(field, False)
        self.assertFalse(field.isVisible())
        self.assertFalse(title.isVisible())
        self.assertFalse(control.isVisible())

        set_labeled_field_visible(field, True)
        self.application.processEvents()
        self.assertTrue(field.isVisible())
        self.assertTrue(title.isVisible())
        self.assertTrue(control.isVisible())
        field.close()

    def test_empty_title_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            labeled_field("  ", QLineEdit())


if __name__ == "__main__":
    unittest.main()
