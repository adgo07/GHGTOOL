"""C+A navigation must preserve business state and reveal validation targets."""
import unittest
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QPushButton, QRadioButton, QTreeWidgetItem
from packages.ui.compact_choices import SegmentedChoiceControl
from tests import test_accounting_projects_ui as project_fixture


class SourceDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    setUp = project_fixture.AccountingProjectUiTests.setUp
    tearDown = project_fixture.AccountingProjectUiTests.tearDown
    _new_page = project_fixture.AccountingProjectUiTests._new_page

    def pump(self):
        for _ in range(3):
            self.application.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_directory_switches_preserve_complete_state_and_real_controls(self):
        page = self.page
        for group in ("fuel", "electricity", "calcination"):
            page._toggle_source_group(group)
        fuel = page._fuel_rows[0]
        fuel.activity.setText("123.45")
        fuel.source_reference.setText("检测报告 TEST-001 第3页")
        energy = page._energy_family_rows["electricity"][0]
        energy.amount.setText("234.56")
        material = page._process_rows["calcination"][0]["materials"][0]
        material["mass"].setText("345.67")
        initial = page._capture_form_state()
        for _ in range(3):
            for group in ("fuel", "electricity", "calcination"):
                page.source_directory.buttons[group].click()
                self.pump()
                self.assertEqual(page._capture_form_state(), initial)
        self.assertIs(page._fuel_rows[0], fuel)
        self.assertIs(page._energy_family_rows["electricity"][0], energy)
        self.assertIs(page._process_rows["calcination"][0]["materials"][0], material)
        self.assertTrue(all(isinstance(b, QRadioButton) for b in fuel.path_choices.group.buttons()))
        self.assertTrue(all(isinstance(b, QRadioButton) for b in energy.direction_choices.group.buttons()))

    def test_browse_does_not_enable_and_enable_remains_explicit(self):
        page = self.page
        initial = page._capture_form_state()
        for group in ("fuel", "electricity", "calcination"):
            page.source_directory.select(group)
        self.assertEqual(initial, page._capture_form_state())
        page.source_directory.placeholders["fuel"].findChild(QPushButton).click()
        self.assertTrue(page._source_is_enabled("CAR-SRC-FUEL-001"))
        self.assertFalse(page._source_is_enabled("CAR-SRC-CALCINATION-001"))
        self.assertTrue(page.source_directory.placeholders["fuel"].isHidden())
        page._toggle_source_group("fuel")
        self.assertFalse(page.source_directory.placeholders["fuel"].isHidden())

    def test_validation_reveals_directory_without_changing_state(self):
        page = self.page
        page._toggle_source_group("fuel")
        page.source_directory.select("calcination")
        item = QTreeWidgetItem(["缺少活动量"])
        item.setData(0, Qt.ItemDataRole.UserRole, page._fuel_rows[0].activity.objectName())
        item.setData(0, Qt.ItemDataRole.UserRole + 1, "CAR-SRC-FUEL-001")
        initial = page._capture_form_state()
        page._focus_validation_item(item)
        self.pump()
        self.assertTrue(page.source_directory.buttons["fuel"].isChecked())
        self.assertEqual(initial, page._capture_form_state())

    def test_new_rows_and_conversion_keep_scoped_layout(self):
        page = self.page
        fuel = page._add_fuel_row()
        # Existing creation helpers may return None: inspect the owned final row.
        fuel = page._fuel_rows[-1]
        self.assertEqual(fuel.input_grid.columnCount(), 3)
        material = page._add_material_line(page._process_rows["calcination"][0])
        choices = material["widget"].findChildren(SegmentedChoiceControl)
        self.assertTrue(choices)
        self.assertTrue(all(c._radio_style for c in choices))
        conversion = next(b for b in material["widget"].findChildren(QPushButton) if b.text() == "数据基准与换算")
        material["mass"].setText("17.25")
        conversion.click()
        page.source_directory.select("fuel")
        page.source_directory.select("calcination")
        self.assertTrue(conversion.isChecked())
        self.assertEqual(material["mass"].text(), "17.25")
        heat = page._energy_family_rows["heat"][0]
        self.assertFalse(heat.direction_choices._radio_style)
