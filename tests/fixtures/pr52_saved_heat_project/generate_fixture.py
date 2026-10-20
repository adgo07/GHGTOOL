import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from hashlib import sha256
import json,shutil
from datetime import date
from io import BytesIO
from zipfile import ZipFile
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox
from tests.test_b_material_draft_scope import MaterialDraftScopeTests
from tests.test_b_heat_chain import HeatQtTests
from packages.application.reporting.model import build_report_model
from packages.infrastructure.reporting import render_report_docx
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage
out=Path(os.environ['B_EXTERNAL_OLD_FIXTURE_OUT']);out.mkdir(parents=True,exist_ok=True)
app=QApplication.instance() or QApplication([]);case=MaterialDraftScopeTests();case.app=app
with case.page() as (gui,projects,root,shell,records):
 HeatQtTests.prepare(gui);gui.project_name.setText('PR52历史项目合成');gui._run_calculation()
 assert len(records.list_all())==1
 assert gui._save_project()
 workspace=projects.get(gui._workspace.project_id);unit=workspace.units[0];rid=unit.record_ids[-1]
 assert not gui._calculation_result_is_stale(unit)
 assert not hasattr(gui._input(increment=False),'external_co2')
 model=build_report_model(records.get(rid),raw_input_snapshot=records.get_raw_input_snapshot(rid),trace_snapshot=records.get_trace_snapshot(rid),provenance_snapshot=records.get_provenance_snapshot(rid),reporting_snapshot=records.get_reporting_snapshot(rid),report_qualification=records.get_report_qualification(rid),today=date(2026,10,20))
 word=render_report_docx(model);(out/'record.docx').write_bytes(word)
 with ZipFile(BytesIO(word)) as z:body=z.read('word/document.xml')
 for name in ('projects.sqlite','records.sqlite'):shutil.copy2(root/name,out/name)
 proof={'source_commit':'0f50642544b110ee461f1b32ef8a01091d0f44d0','generator':'actual PR52 GUI _run_calculation/_save_project, no external field deletion or hash reconstruction','source_page_sha256':sha256(Path(CarbonMaterialAccountingPage._fingerprint_business_input.__func__.__code__.co_filename).read_bytes()).hexdigest(),'project_id':workspace.project_id,'unit_id':unit.unit_id,'record_id':rid,'input_fingerprint':unit.input_fingerprint,'calculation_fingerprint':unit.result_snapshot['calculation_fingerprint'],'reporting_fingerprint':unit.result_snapshot['reporting_fingerprint'],'word_document_xml_sha256':sha256(body).hexdigest(),'report_model_sha256':sha256(repr(model).encode()).hexdigest(),'database_sha256':{name:sha256((out/name).read_bytes()).hexdigest() for name in ('projects.sqlite','records.sqlite')}}
 (out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,ensure_ascii=False))
