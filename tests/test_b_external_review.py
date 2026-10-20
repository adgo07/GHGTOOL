"""PR53复核：真实PR52项目恢复、声明状态、提示与交付环境前置失败。"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from contextlib import contextmanager
from dataclasses import replace, asdict
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from PySide6.QtWidgets import QApplication, QMessageBox, QTreeWidget
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import ProjectWorkspaceService
from packages.application.reporting.model import build_report_model
from packages.infrastructure.reporting import render_report_docx
from packages.persistence import SQLiteProjectWorkspaceRepository, SQLiteRecordRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
from packages.standards.carbon_material_external_co2 import ExternalCO2Input
from packages.excel.templates import template_capabilities
from tests import test_b_material_draft_scope as drafts, test_b_heat_chain as heat
from tests.ui_tree_helpers import tree_texts

FIXTURE = Path(__file__).parent / 'fixtures/pr52_saved_heat_project'

class ExternalReviewTests(unittest.TestCase):
    page = drafts.MaterialDraftScopeTests.page

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @contextmanager
    def restored(self, root, project_id):
        projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root/'projects.sqlite'))
        records = SQLiteRecordRepository(root/'records.sqlite')
        window = create_main_window(AppConfig(catalog_database=root/'catalog.sqlite', records_database=root/'records.sqlite', projects_database=root/'projects.sqlite'), record_repository=records, project_service=projects)
        shell = window.centralWidget()
        shell.navigate(AppRoute.NEW_ACCOUNTING)
        self.app.processEvents()
        page = shell.pages[AppRoute.NEW_ACCOUNTING]
        # Explicitly discard the new unsaved form when opening the saved project.
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Discard):
            page.saved_projects.setCurrentIndex(page.saved_projects.findData(project_id))
            page._open_selected_project()
        self.app.processEvents()
        try:
            yield page, records
        finally:
            with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Discard):
                window.close()
            window.deleteLater()
            self.app.processEvents()

    def test_actual_pr52_sqlite_project_close_reopen_keeps_result_and_frozen_word(self):
        proof = json.loads((FIXTURE/'proof.json').read_text(encoding='utf-8'))
        self.assertEqual(proof['source_commit'], '0f50642544b110ee461f1b32ef8a01091d0f44d0')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('projects.sqlite', 'records.sqlite'):
                self.assertEqual(sha256((FIXTURE/name).read_bytes()).hexdigest(), proof['database_sha256'][name])
                shutil.copy2(FIXTURE/name, root/name)
            build_catalog_database(DEFAULT_SOURCE_PATH, root/'catalog.sqlite')
            original = (root/'records.sqlite').read_bytes()
            for iteration in range(2):
                with self.subTest(reopen=iteration), self.restored(root, proof['project_id']) as (gui, records):
                    self.assertIsNone(gui._input(increment=False).external_co2)
                    self.assertEqual(gui._current_calculation_fingerprint(), proof['calculation_fingerprint'])
                    self.assertEqual(gui._current_business_fingerprint(), proof['input_fingerprint'])
                    self.assertFalse(gui._calculation_result_is_stale(gui._unit()))
                    self.assertFalse(gui.result_card.isHidden())
                    self.assertIn('上次成功结果', gui.unit_result_summary.text())
                    rid = proof['record_id']
                    model = build_report_model(records.get(rid), raw_input_snapshot=records.get_raw_input_snapshot(rid), trace_snapshot=records.get_trace_snapshot(rid), provenance_snapshot=records.get_provenance_snapshot(rid), reporting_snapshot=records.get_reporting_snapshot(rid), report_qualification=records.get_report_qualification(rid), today=date(2026,10,20))
                    self.assertEqual(sha256(repr(model).encode()).hexdigest(), proof['report_model_sha256'])
                    with ZipFile(BytesIO(render_report_docx(model))) as archive:
                        self.assertEqual(sha256(archive.read('word/document.xml')).hexdigest(), proof['word_document_xml_sha256'])
                    self.assertTrue(gui._save_project())
            with self.restored(root, proof['project_id']) as (gui, records):
                row = gui._energy_family_rows['heat'][0]
                row.amount.setText('2')
                self.assertTrue(gui._calculation_result_is_stale(gui._unit()))
                self.assertTrue(gui._save_project())
            with self.restored(root, proof['project_id']) as (gui, records):
                self.assertTrue(gui._calculation_result_is_stale(gui._unit()))
                self.assertTrue(gui.result_card.isHidden())
            self.assertEqual((root/'records.sqlite').read_bytes(), original)

    def test_only_root_missing_supplement_is_compatible_explicit_choices_still_change_fingerprints(self):
        with self.page() as (gui, *_):
            heat.HeatQtTests.prepare(gui)
            value = replace(gui._input(increment=False), external_co2=None)
            legacy = asdict(value)
            legacy.pop('external_co2')
            for scope in ('all', 'calculation'):
                fingerprint = lambda v: gui._fingerprint_business_input(v, scope=scope)
                self.assertEqual(fingerprint(value), fingerprint(legacy))
                self.assertEqual(fingerprint(dict(legacy, external_co2=None)), fingerprint(legacy))
                choices = [replace(value, external_co2=ExternalCO2Input(included=flag)) for flag in (False, True)]
                self.assertEqual(len({fingerprint(value), *(fingerprint(v) for v in choices)}), 3)
                nested = dict(legacy, reporting_data={'external_co2':None})
                if scope == 'all':
                    self.assertNotEqual(fingerprint(nested), fingerprint(dict(legacy, reporting_data={})))

    def test_other_standard_gui_warning_allows_record_and_uses_business_message(self):
        expected = '本次炭素核算可继续；其他行业活动或运输应按相应标准另行核算，符合条件的外部CO₂可单独补充。'
        with self.page() as (gui, projects, root, shell, records):
            heat.HeatQtTests.prepare(gui)
            gui.other_activity_present.setChecked(True)
            gui.transport_present.setChecked(True)
            gui._run_calculation()
            self.assertEqual(len(records.list_all()), 1)
            texts = [text for tree in gui.findChildren(QTreeWidget) for text in tree_texts(tree)]
            self.assertTrue(any(expected in text for text in texts), texts)
            self.assertFalse(any('请改用适用标准核算' in text for text in texts))

    def test_unknown_template_versions_fail_closed_before_parsing(self):
        from packages.excel.appendix_b import AppendixBWorkbookImporter
        for version in ('2.10.0', '3.0.0', '9.9.9', '', '2.9.1'):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, '未登记'):
                template_capabilities(version)
            with self.assertRaisesRegex(ValueError, '未登记'):
                AppendixBWorkbookImporter._parse_external(None, None, [], [], version)

    def test_missing_pip_is_explicit_failure_before_building_not_skip(self):
        import scripts.verify_distribution_templates as verifier
        with tempfile.TemporaryDirectory() as directory, patch.object(verifier.subprocess, 'run', return_value=subprocess.CompletedProcess([],1,'No module named pip')) as run, patch.object(verifier.shutil, 'copytree') as copy:
            with self.assertRaisesRegex(RuntimeError, '前置条件不满足.*pip.*不得跳过'):
                verifier.verify_distribution_templates(Path(__file__).resolve().parents[1], Path(directory)/'out')
            copy.assert_not_called()
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][-3:], ['-m','pip','--version'])

if __name__ == '__main__':
    unittest.main()
