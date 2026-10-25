"""Repeat-item disclosure retains original input/identity and reveals errors."""
import unittest
from PySide6.QtWidgets import QApplication
from tests import test_accounting_projects_ui as project_fixture


class RepeatedEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
    setUp = project_fixture.AccountingProjectUiTests.setUp
    tearDown = project_fixture.AccountingProjectUiTests.tearDown
    _new_page = project_fixture.AccountingProjectUiTests._new_page

    def test_disclosure_preserves_form_and_participation_for_all_families(self):
        page = self.page
        hosts = [page._fuel_rows[0], *page._energy_rows,
                 *(rows[0]['widget'] for rows in page._process_rows.values())]
        page._fuel_rows[0].activity.setText('17.25')
        before = page._capture_form_state()
        page._project_dirty = page._input_dirty = False
        for host in hosts:
            host._entry_toggle.setChecked(False)
            self.assertTrue(host._entry_body.isHidden())
        for host in hosts:
            host._entry_toggle.setChecked(True)
            self.assertFalse(host._entry_body.isHidden())
        self.assertEqual(before, page._capture_form_state())
        self.assertFalse(page._project_dirty)
        self.assertFalse(page._input_dirty)

    def test_child_ownership_and_display_titles_survive_delete_and_add(self):
        page = self.page
        first = page._process_rows['calcination'][0]
        second = page._add_process_row('calcination')
        child = page._add_material_line(second)
        child['name'].setText('待核实石油焦')
        child['mass'].setText('17.25')
        identity = child['line_id']
        page._refresh_entry_titles()
        self.assertTrue(second['widget'].isAncestorOf(child['mass']))
        self.assertFalse(first['widget'].isAncestorOf(child['mass']))
        self.assertIn('待核实石油焦', child['title'].text())
        sibling = page._add_material_line(second)
        page._remove_material_line(second, sibling['line_id'])
        replacement = page._add_material_line(second)
        self.assertNotEqual(sibling['line_id'], replacement['line_id'])
        self.assertEqual(child['line_id'], identity)
        self.assertEqual(child['mass'].text(), '17.25')
        self.assertIn(child, second['materials'])
        self.assertNotIn(child, first['materials'])

    def test_error_reveal_opens_parent_child_and_conversion_without_rewriting(self):
        page = self.page
        page._toggle_source_group('calcination')
        process = page._process_rows['calcination'][0]
        material = process['materials'][0]
        process['widget']._entry_toggle.setChecked(False)
        material['widget']._entry_toggle.setChecked(False)
        material['mass'].setText('17.25')
        before = page._capture_form_state()
        page._project_dirty = page._input_dirty = False
        page._scroll_to_widget(material['mass'], focus=True)
        self.assertTrue(process['widget']._entry_toggle.isChecked())
        self.assertTrue(material['widget']._entry_toggle.isChecked())
        self.assertEqual(before, page._capture_form_state())
        self.assertFalse(page._project_dirty)
        self.assertFalse(page._input_dirty)
