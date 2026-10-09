"""Verify labels stay attached and six fume inputs reflow without overlap."""
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QLineEdit
from packages.ui.responsive_fields import ResponsiveFieldGrid

class ResponsiveFumeFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_six_inputs_use_two_rows_wide_and_three_rows_narrow(self):
        grid = ResponsiveFieldGrid()
        fields = [QLineEdit() for _ in range(6)]
        for index, field in enumerate(fields):
            grid.add_field(f"焚烧参数{index+1}", field)
        grid.show()
        for width, expected_rows, expected_columns in ((1100, 2, 3), (600, 3, 2), (1100, 2, 3)):
            grid.resize(width, grid.sizeHint().height())
            self.app.processEvents()
            grid.resize(width, grid.sizeHint().height())
            self.app.processEvents()
            cells = [field.parentWidget() for field in fields]
            self.assertEqual(len({cell.y() for cell in cells}), expected_rows)
            self.assertEqual(len({cell.x() for cell in cells}), expected_columns)
            for index, cell in enumerate(cells):
                self.assertLessEqual(cell.geometry().right(), grid.width())
                self.assertLessEqual(cell.geometry().bottom(), grid.height())
                for other in cells[index+1:]:
                    self.assertFalse(cell.geometry().intersects(other.geometry()))
        grid.close()
