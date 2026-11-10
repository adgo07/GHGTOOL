"""Local paint classes keep native event and FieldSpec behavior."""
import sys,unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest,QSignalSpy
from PySide6.QtWidgets import QApplication,QCheckBox,QStyle,QStyleOptionSpinBox
from packages.ui.business_page_style import BusinessCheckBox
from packages.ui.accounting_controls import AccountingSpinBox
from packages.ui.typed_inputs import create_typed_input
from packages.ui.field_specs import get_field_spec


class AccountingControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.errors=[];self.old_hook=sys.excepthook
        sys.excepthook=lambda kind,value,trace:self.errors.append(f'{kind.__name__}: {value}')
    def tearDown(self):
        self.app.processEvents();sys.excepthook=self.old_hook
        self.assertEqual(self.errors,[])

    def test_checkbox_paint_class_keeps_metadata_and_native_keyboard(self):
        spec=get_field_spec('other_activity_present')
        normal=create_typed_input(None,spec,'normal')
        local=create_typed_input(None,spec,'local',checkbox_type=BusinessCheckBox)
        try:
            self.assertIs(type(normal),QCheckBox)
            self.assertIsInstance(local,QCheckBox)
            for key in ('fieldSpecKey','fieldDataType'):
                self.assertEqual(local.property(key),normal.property(key))
            self.assertEqual(local.toolTip(),normal.toolTip())
            spy=QSignalSpy(local.toggled)
            local.show();local.setFocus();QTest.keyClick(local,Qt.Key.Key_Space)
            self.assertTrue(local.isChecked());self.assertEqual(spy.count(),1)
        finally:normal.close();local.close();normal.deleteLater();local.deleteLater()

    def test_spin_paint_keeps_native_buttons_range_and_keyboard(self):
        spin=AccountingSpinBox();spin.setRange(1900,2100);spin.setValue(2026);spin.resize(140,40);spin.show();self.app.processEvents()
        try:
            option=QStyleOptionSpinBox();spin.initStyleOption(option)
            for control,expected in ((QStyle.SubControl.SC_SpinBoxUp,2027),(QStyle.SubControl.SC_SpinBoxDown,2026)):
                rect=spin.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,control,spin)
                self.assertFalse(rect.isEmpty());QTest.mouseClick(spin,Qt.MouseButton.LeftButton,pos=rect.center());self.assertEqual(spin.value(),expected)
            QTest.keyClick(spin,Qt.Key.Key_Up);self.assertEqual(spin.value(),2027)
            self.assertEqual((spin.minimum(),spin.maximum()),(1900,2100))
        finally:spin.close();spin.deleteLater()
