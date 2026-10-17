"""PR49 F02/F03 actual offscreen regressions; no native UI claim."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.application import ProjectWorkspaceService
from packages.persistence import SQLiteProjectWorkspaceRepository,SQLiteRecordRepository,build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from packages.standards.carbon_material_normalization import MaterialDataSource as Source

class MaterialDraftScopeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 @contextmanager
 def page(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);catalog=build_catalog_database(DEFAULT_SOURCE_PATH,root/'catalog.sqlite')
   projects=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root/'projects.sqlite'))
   records=SQLiteRecordRepository(root/'records.sqlite')
   window=create_main_window(AppConfig(catalog_database=catalog,records_database=root/'records.sqlite',projects_database=root/'projects.sqlite'),record_repository=records,project_service=projects)
   shell=window.centralWidget();shell.navigate(AppRoute.NEW_ACCOUNTING);self.app.processEvents();page=shell.pages[AppRoute.NEW_ACCOUNTING]
   try:yield page,projects,root,shell,records
   finally:
    with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No):window.close()
    window.deleteLater();self.app.processEvents()
 @staticmethod
 def drafts(row,measured,calculated):
  source=row['fixed_carbon_source'];row['fixed_carbon'].setText(measured)
  source.setCurrentIndex(source.findData(Source.CHEMICAL_CALCULATION));row['fixed_carbon'].setText(calculated)
  source.setCurrentIndex(source.findData(Source.MEASURED))
 def test_same_local_id_separate_instances_sqlite_and_source_roundtrip(self):
  with self.page() as (page,projects,root,*_):
   for identity,m,c in [('A','40','60'),('B','80','30')]:
    process=page._add_process_row('calcination',instance_id=identity,material_ids=('feed-local',),default_material_categories=False)
    row=process['materials'][0];row['name'].setText('同名');self.drafts(row,m,c)
   first=next(p for p in page._process_rows['calcination'] if p['instance_id']=='A')
   middle=page._add_material_line(first,line_id='remove-middle')
   survivor=page._add_material_line(first,line_id='same-name-other-id');survivor['name'].setText('同名');self.drafts(survivor,'77','88')
   page._remove_material_line(first,middle['line_id'])
   state=page._capture_form_state();workspace=projects.new_workspace('实例隔离')
   projects.save(replace(workspace,units=(replace(workspace.units[0],form_state=state),)))
   reopened=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root/'projects.sqlite')).get(workspace.project_id)
   page._restore_form_state(reopened.units[0].form_state)
   for identity,m,c in [('A','40','60'),('B','80','30')]:
    row=next(p for p in page._process_rows['calcination'] if p['instance_id']==identity)['materials'][0]
    self.assertEqual(row['fixed_carbon'].text(),m)
    row['fixed_carbon_source'].setCurrentIndex(row['fixed_carbon_source'].findData(Source.CHEMICAL_CALCULATION));self.assertEqual(row['fixed_carbon'].text(),c)
    row['fixed_carbon_source'].setCurrentIndex(row['fixed_carbon_source'].findData(Source.MEASURED));self.assertEqual(row['fixed_carbon'].text(),m)

   first=next(p for p in page._process_rows['calcination'] if p['instance_id']=='A')
   survivor=next(r for r in first['materials'] if r['line_id']=='same-name-other-id')
   self.assertEqual(survivor['fixed_carbon'].text(),'77')
   survivor['fixed_carbon_source'].setCurrentIndex(survivor['fixed_carbon_source'].findData(Source.CHEMICAL_CALCULATION))
   self.assertEqual(survivor['fixed_carbon'].text(),'88')
 def test_unique_legacy_line_drafts_and_flat_values_restore(self):
  with self.page() as (page,*_):
   process=page._process_rows['calcination'][0];row=process['materials'][0];self.drafts(row,'12','34')
   state=page._capture_form_state();scope=f"calcination_{process['instance_id']}_"
   for key in list(state):
    if key.startswith(scope) and str(row['line_id']) in key:state[key.replace(scope,'calcination_',1)]=state.pop(key)
   state['material_source_drafts']={str(row['line_id']):{'fixed_carbon_source':{'MEASURED':'12','CHEMICAL_CALCULATION':'34'}}}
   page._restore_form_state(state);row=page._process_rows['calcination'][0]['materials'][0]
   self.assertEqual(row['fixed_carbon'].text(),'12')
   row['fixed_carbon_source'].setCurrentIndex(row['fixed_carbon_source'].findData(Source.CHEMICAL_CALCULATION));self.assertEqual(row['fixed_carbon'].text(),'34')
   self.assertFalse(page._capture_form_state()['material_source_drafts']['unresolved'])
 def test_ambiguous_legacy_drafts_preserved_without_pasting_over_input(self):
  with self.page() as (page,projects,root,*_):
   for identity,value in [('A','40'),('B','80')]:
    process=page._add_process_row('calcination',instance_id=identity,material_ids=('local',),default_material_categories=False)
    process['materials'][0]['fixed_carbon'].setText(value)
   state=page._capture_form_state();old={'local':{'fixed_carbon_source':{'MEASURED':'999','CHEMICAL_CALCULATION':'888'}}}
   state['material_source_drafts']=old;state['calcination_materialFixedCarbon_local']='777'
   page._restore_form_state(state)
   for identity,value in [('A','40'),('B','80')]:
    row=next(p for p in page._process_rows['calcination'] if p['instance_id']==identity)['materials'][0]
    self.assertEqual(row['fixed_carbon'].text(),value)
    self.assertIn('未自动采用',row['fixed_carbon_source'].toolTip())
   captured=page._capture_form_state();self.assertEqual(captured['material_source_drafts']['unresolved'],old)
   self.assertEqual(captured['material_legacy_values_unresolved']['calcination_materialFixedCarbon_local'],'777')
   workspace=projects.new_workspace('歧义保留');projects.save(replace(workspace,units=(replace(workspace.units[0],form_state=captured),)))
   reopened=ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(root/'projects.sqlite')).get(workspace.project_id)
   page._restore_form_state(reopened.units[0].form_state)
   self.assertEqual(page._capture_form_state()['material_source_drafts']['unresolved'],old)
