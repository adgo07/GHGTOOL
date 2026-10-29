"""Repeat-item disclosure retains original input/identity and reveals errors."""
import unittest
from PySide6.QtWidgets import QApplication, QPushButton
from tests import test_accounting_projects_ui as project_fixture


class RepeatedEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_fixture.AccountingProjectUiTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        project_fixture.AccountingProjectUiTests.tearDownClass.__func__(cls)
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

    def test_adding_child_refreshes_only_owned_parent_count_and_disclosure_name(self):
        page = self.page
        first = page._process_rows['fgd'][0]
        second = page._add_process_row('fgd')
        second_title = second['title'].text()
        button = first['widget'].findChild(QPushButton, 'add_fgd_component_' + first['instance_id'])
        self.assertIsNotNone(button)
        button.click()
        self.assertEqual(len(first['components']), 2)
        self.assertEqual(len(second['components']), 1)
        self.assertIn('2 种组分', first['title'].text())
        self.assertEqual(second_title, second['title'].text())
        self.assertIn(first['title'].text(), first['widget']._entry_toggle.accessibleName())
        self.assertEqual(len(self.records.list_all()), 0)

    def test_old_aggregate_restores_editable_values_without_creating_material_rows(self):
        page = self.page
        page._toggle_source_group('calcination')
        saved = page._capture_form_state()
        saved['process_instances']['calcination'][0]['material_ids'] = []
        saved['calcination_gc'] = '100'
        saved['calcination_wfc'] = '80'
        page._restore_form_state(saved)
        row = page._process_rows['calcination'][0]
        self.assertEqual(row['materials'], [])
        self.assertEqual(row['fields']['gc'].text(), '100')
        self.assertIn('旧项目汇总值', row['material_summary'].text())
        self.assertIn('100', row['material_summary'].text())
        self.assertFalse(row['fields']['gc'].isReadOnly())
        self.assertTrue(row['legacy_toggle'].isChecked())
        self.assertFalse(row['legacy_editor'].isHidden())
        self.assertTrue(page._save_project())
        project_id = page._workspace.project_id
        self.assertTrue(page.open_project_from_home(project_id))
        row = page._process_rows['calcination'][0]
        self.assertEqual(row['materials'], [])
        self.assertEqual(row['fields']['gc'].text(), '100')
        self.assertIn('旧项目汇总值', row['material_summary'].text())
        self.assertIn('100', row['material_summary'].text())
        before = page._capture_form_state()
        page._project_dirty = page._input_dirty = False
        row['legacy_toggle'].setChecked(False)
        row['legacy_toggle'].setChecked(True)
        self.assertEqual(before, page._capture_form_state())
        self.assertFalse(page._project_dirty)
        self.assertFalse(page._input_dirty)
        row['fields']['gc'].clear()
        row['fields']['wfc'].clear()
        self.assertTrue(row['legacy_toggle'].isHidden())
        self.assertNotIn('旧项目汇总值', row['material_summary'].text())
        self.assertEqual(row['materials'], [])
        self.assertEqual(len(self.records.list_all()), 0)

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
