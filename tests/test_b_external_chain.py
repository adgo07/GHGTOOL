"""真实Qt/SQLite恢复及不可变Record→共享报告/Word的软件补充链。"""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from contextlib import ExitStack
from dataclasses import replace
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from PySide6.QtWidgets import QApplication
from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.application.reporting.model import build_report_model
from packages.infrastructure.reporting import render_report_docx
from packages.application.project_workspaces import ProjectWorkspaceService
from packages.persistence import SQLiteProjectWorkspaceRepository, SQLiteRecordRepository
from packages.standards.carbon_material import CarbonMaterialCalculator
from packages.standards.carbon_material_external_co2 import ExternalCO2Input
from tests import test_b_material_draft_scope as drafts
from tests import test_b_heat_chain as heat_chain

class ExternalChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    page=drafts.MaterialDraftScopeTests.page

    def test_gui_disabled_invalid_draft_project_reopen_and_statement_preservation(self):
        with self.page() as (gui,projects,root,shell,records):
            heat_chain.HeatQtTests.prepare(gui)
            gui.external_included.setChecked(True)
            gui.external_amount.setText('NaN')
            gui.external_label.setText('企业已核算草稿')
            gui.other_activity_present.setChecked(True);gui.transport_present.setChecked(True)
            gui.external_included.setChecked(False)
            state=gui._capture_form_state();workspace=projects.new_workspace('外部补充草稿')
            projects.save(replace(workspace,units=(replace(workspace.units[0],form_state=state),)))
            recovered=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root/'projects.sqlite')).get(workspace.project_id)
            gui._restore_form_state(recovered.units[0].form_state)
            self.assertFalse(gui.external_included.isChecked());self.assertEqual(gui.external_amount.text(),'NaN')
            self.assertFalse(gui.external_amount.isEnabled());self.assertEqual(gui.external_label.text(),'企业已核算草稿')
            gui._acknowledge_out_of_scope_activities()
            self.assertTrue(gui.other_activity_present.isChecked());self.assertTrue(gui.transport_present.isChecked())
            disabled=CarbonAccountingUseCase(gui.calculator,records).calculate(gui._input(increment=False))
            self.assertTrue(disabled.successful,disabled.problems)
            gui.external_included.setChecked(True)
            invalid=CarbonAccountingUseCase(gui.calculator,records).calculate(gui._input(increment=False))
            self.assertFalse(invalid.successful);self.assertEqual(len(records.list_all()),1)
            gui.external_amount.clear()
            pending=CarbonAccountingUseCase(gui.calculator,records).calculate(gui._input(increment=False))
            self.assertTrue(pending.successful,pending.problems)
            gui.external_amount.setText('0')
            explicit_zero=CarbonAccountingUseCase(gui.calculator,records).calculate(gui._input(increment=False))
            self.assertTrue(explicit_zero.successful)
            nodes=[records.get_trace_snapshot(r.record.record_id)['software_supplement'] for r in (disabled,pending,explicit_zero)]
            self.assertEqual([n['status'] for n in nodes],['NOT_INCLUDED','PENDING','COMPLETED_ZERO'])

    def test_gui_legacy_missing_state_stays_missing_until_explicit_choice(self):
        with self.page() as (gui,projects,root,shell,records):
            heat_chain.HeatQtTests.prepare(gui)
            state=gui._capture_form_state()
            state.pop('external_state_recorded')
            for key in ('externalIncluded','externalAmount','externalLabel'):state.pop(key,None)
            gui._restore_form_state(state)
            self.assertIsNone(gui._input(increment=False).external_co2)
            self.assertFalse(gui._capture_form_state()['external_state_recorded'])
            gui.external_included.setChecked(True)
            self.assertIsNotNone(gui._input(increment=False).external_co2)

    def test_actual_gui_calculation_twice_appends_and_reads_frozen_sum(self):
        with self.page() as (gui,projects,root,shell,records):
            heat_chain.HeatQtTests.prepare(gui)
            gui.external_included.setChecked(True);gui.external_amount.setText('20')
            for count in (1,2):
                gui._run_calculation()
                self.assertEqual(len(records.list_all()),count)
                self.assertIn('20.31',gui.external_result_summary.text())
                self.assertIn('0.308',gui.result_total.text())
            gui.external_amount.setText('-1');gui._run_calculation()
            self.assertEqual(len(records.list_all()),2)

    def test_formal_record_report_word_never_recompute_supplement(self):
        with self.page() as (gui,projects,root,shell,records):
            heat_chain.HeatQtTests.prepare(gui)
            gui.external_included.setChecked(True);gui.external_amount.setText('20')
            value=gui._input(increment=False)
            result=CarbonAccountingUseCase(gui.calculator,records).calculate(value)
            self.assertTrue(result.successful,result.problems)
            rid=result.record.record_id;original=(root/'records.sqlite').read_bytes()
            raw=records.get_raw_input_snapshot(rid);trace=records.get_trace_snapshot(rid)
            import packages.standards.carbon_material as domain
            with ExitStack() as stack:
                stack.enter_context(patch.object(CarbonMaterialCalculator,'calculate',side_effect=AssertionError('no recalc')))
                stack.enter_context(patch.object(gui._parameter_resolver,'resolve',side_effect=AssertionError('no resolver')))
                stack.enter_context(patch.object(domain,'evaluate_external_co2_supplement',side_effect=AssertionError('no supplement summation')))
                model=build_report_model(records.get(rid),raw_input_snapshot=raw,trace_snapshot=trace,
                    provenance_snapshot=records.get_provenance_snapshot(rid),reporting_snapshot=records.get_reporting_snapshot(rid),report_qualification=records.get_report_qualification(rid))
                word=render_report_docx(model);gui._set_external_result(rid)
            section=next(s for s in model.sections if s.section_id=='software-supplement')
            text=str(section)
            self.assertIn('20.31',text);self.assertIn('20.00',text)
            self.assertNotIn('B.10',text)
            self.assertIn('20.31',gui.external_result_summary.text())
            with ZipFile(BytesIO(word)) as z:xml=z.read('word/document.xml').decode()
            self.assertIn('软件补充合计',xml);self.assertIn('20.31',xml)
            self.assertEqual((root/'records.sqlite').read_bytes(),original)
            self.assertEqual(records.get_raw_input_snapshot(rid),raw);self.assertEqual(records.get_trace_snapshot(rid),trace)
