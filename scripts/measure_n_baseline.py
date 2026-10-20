"""Serial, source-only N baseline. No production implementation is modified."""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
from io import BytesIO
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
EXPECTED_HEAD = '348077cd972a27b6eeb80b77b712e7cb35375988'
OUT = ROOT / 'docs/performance/n-baseline'
TEMP = ROOT / 'tmp/n-baseline'
PRODUCTION = ('apps', 'packages', 'resources', 'pyproject.toml', 'platform-lock.json')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def production_digest():
    names = git('ls-files', *PRODUCTION).splitlines()
    dig = hashlib.sha256()
    for name in names:
        dig.update(name.encode()); dig.update((ROOT/name).read_bytes())
    return {'tracked_files': len(names), 'sha256_paths_and_contents': dig.hexdigest(),
            'diff_against_frozen_head': git('diff', EXPECTED_HEAD, '--', *PRODUCTION)}


def compose(folder):
    from PySide6.QtWidgets import QApplication
    from apps.carbon_accounting_desktop.app import create_main_window
    from apps.carbon_accounting_desktop.config import AppConfig
    from packages.application import ProjectWorkspaceService
    from packages.persistence import SQLiteProjectWorkspaceRepository, SQLiteRecordRepository
    app = QApplication.instance() or QApplication([])
    records = SQLiteRecordRepository(folder/'records.sqlite')
    projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(folder/'projects.sqlite'))
    config = AppConfig(catalog_database=folder/'catalog.sqlite', records_database=folder/'records.sqlite',
                       projects_database=folder/'projects.sqlite', user_database=folder/'user.sqlite',
                       log_directory=folder/'logs')
    window = create_main_window(config, record_repository=records, project_service=projects)
    return app, window, records, projects


def startup_worker(folder, output):
    started = time.perf_counter_ns()
    app, window, records, projects = compose(folder)
    returned = time.perf_counter_ns()
    # One queued callback proves event loop dispatch; no claim about visible first frame.
    from PySide6.QtCore import QTimer
    ready = []
    def mark_ready():
        ready.append(time.perf_counter_ns()); app.quit()
    window.show()
    QTimer.singleShot(0, mark_ready)
    app.exec()
    output.write_text(json.dumps({'create_return_ns': returned-started,
                                 'event_loop_ready_ns': ready[0]-started}), encoding='utf-8')
    window.hide()


def summarize(values):
    ordered = sorted(values)
    return {'n': len(values), 'median_ns': statistics.median(values),
            'p95_nearest_rank_ns': ordered[math.ceil(.95*len(values))-1],
            'min_ns': min(values), 'max_ns': max(values)} if values else {'n': 0}


def main():
    assert git('remote', 'get-url', 'origin') == 'https://github.com/adgo07/GHGTOOL.git'
    assert git('rev-parse', 'HEAD') == EXPECTED_HEAD, 'Refuse a different production HEAD'
    TEMP.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    before = production_digest(); assert not before['diff_against_frozen_head']
    seed = TEMP/'seed'; seed.mkdir(exist_ok=True)
    from packages.persistence import build_catalog_database, SQLiteRecordRepository, SQLiteProjectWorkspaceRepository
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.application import ProjectWorkspaceService
    from tests.benchmark_navigation import make_record
    from packages.excel.templates import ExcelTemplateService
    from openpyxl import load_workbook
    # Build and seed outside all measured intervals. Copy DBs rather than use user stores.
    build_catalog_database(DEFAULT_SOURCE_PATH, seed/'catalog.sqlite')
    records = SQLiteRecordRepository(seed/'records.sqlite')
    assert not records.list_all(), 'Use a new tmp/n-baseline directory for every run'
    for i in range(200): records.create(make_record(i))
    projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(seed/'projects.sqlite'))
    for i in range(20): projects.save(projects.new_workspace(f'合成性能项目{i:02d}'))
    workbook = load_workbook(BytesIO(ExcelTemplateService.default().read_bytes()))
    for cell, value in {'B3':'饱和蒸汽','C3':1,'F3':2800,'H3':'已知焓','I3':'缺省值','J3':'边界外'}.items():
        workbook['B.9'][cell] = value
    workbook['软件补充']['B4']='纳入'; workbook['软件补充']['B5']=20
    workbook['软件补充']['B6']='合成其他活动'
    workbook_path = TEMP/'synthetic-v11.xlsx'; workbook.save(workbook_path); workbook.close()
    data = {'production_head': EXPECTED_HEAD, 'started_utc': datetime.now(timezone.utc).isoformat(),
            'environment': {'os': platform.platform(), 'machine': platform.machine(),
                            'python': platform.python_version(), 'cpu': platform.processor(),
                            'logical_cpu_count': os.cpu_count(), 'qt_platform': 'offscreen',
                            'dependencies': {name:version(name) for name in ('PySide6','shiboken6','openpyxl','python-docx','lxml','CoolProp','numpy')},
                            'runtime_role': 'CPython 3.12 Windows x64; existing dependencies; source checkout'},
            'data': {'synthetic_navigation_records':200, 'saved_projects':20, 'business_units':1,
                     'workbook_bytes':workbook_path.stat().st_size,
                     'workbook_sha256':hashlib.sha256(workbook_path.read_bytes()).hexdigest(),
                     'business_fixture':'v11/2.9.0; B.9 purchased saturated steam 1t, known enthalpy 2800kJ/kg; external CO2 20t; annual 2026'},
            'production_before':before, 'scenarios':{}, 'execution_order':[], 'failures':[]}
    def add(name, samples, warmups, checks=None):
        data['scenarios'][name]={'warmup_ns':warmups,'samples_ns':samples,'statistics':summarize(samples),
                                 'failure_count':sum(f['scenario']==name for f in data['failures']), 'checks':checks or {}}
        data['execution_order'].append(name)
    starts = []; returns = []; dispatch = []
    for i in range(6):
        folder=TEMP/f'startup-{i}'; folder.mkdir()
        for filename in ('records.sqlite','projects.sqlite','catalog.sqlite'): shutil.copy2(seed/filename,folder/filename)
        output=folder/'ready.json'; started=time.perf_counter_ns()
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--startup-worker',str(folder),str(output)],
                              cwd=ROOT, capture_output=True, text=True, timeout=120)
        duration=time.perf_counter_ns()-started
        if result.returncode:
            raise RuntimeError(f'startup worker {i} failed ({result.returncode})')
        value=json.loads(output.read_text()); starts.append(duration); returns.append(value['create_return_ns']); dispatch.append(value['event_loop_ready_ns'])
    add('startup_fresh_process_total',starts[1:],starts[:1],{'includes':'process launch through normal child termination'})
    add('startup_create_main_window_return',returns[1:],returns[:1],{'includes':'business imports, QApplication, SQLite repository initialization, create_main_window'})
    add('startup_event_loop_ready',dispatch[1:],dispatch[:1],{'includes':'same start as create_return, show and first queued Qt callback'})
    folder=TEMP/'session'; folder.mkdir()
    for filename in ('records.sqlite','projects.sqlite','catalog.sqlite'): shutil.copy2(seed/filename,folder/filename)
    app,window,records,projects=compose(folder); shell=window.centralWidget(); window.show();app.processEvents()
    from packages.ui.view_models import AppRoute
    from packages.application.carbon_accounting import CarbonAccountingUseCase
    from packages.application.reporting.service import build_saved_record_report
    from packages.infrastructure.reporting import render_report_docx
    from packages.ui.report_export import write_report_atomically
    from tests.test_b_heat_chain import HeatQtTests
    from PySide6.QtCore import qVersion
    data['environment']['qt_version']=qVersion()
    # Warm each route once; the first-use value remains visible, excluded from statistics.
    for route in AppRoute:
        def navigate(target=route):
            shell.navigate(target); app.processEvents()
            assert shell.page_stack.currentWidget() is shell._pages[target]
        samples=[]
        for i in range(6):
            shell.navigate(AppRoute.STANDARDS if route is AppRoute.HOME else AppRoute.HOME);app.processEvents()
            t=time.perf_counter_ns();navigate();samples.append(time.perf_counter_ns()-t)
        add('navigation_'+route.value,samples[1:],samples[:1],{'programmatic_route_and_event_pump':True})
    gui=shell.pages[AppRoute.NEW_ACCOUNTING]; HeatQtTests.prepare(gui)
    excel=shell.pages[AppRoute.EXCEL_IMPORT]
    context=excel.excel_adapter.context(period=gui._period(),boundary_confirmed=True,enterprise_name='合成性能企业')
    previews=[];samples=[]; count_before=len(records.list_all())
    for i in range(6):
        t=time.perf_counter_ns();preview=excel.excel_adapter.import_preview(workbook_path,context);elapsed=time.perf_counter_ns()-t
        assert preview.units[0].can_calculate, str(preview.units[0].errors)
        previews.append(preview);samples.append(elapsed)
    assert len(records.list_all())==count_before
    add('excel_import_preview',samples[1:],samples[:1],{'records_added':0,'valid_units':len(preview.units)})
    unit=preview.units[0];canonical=unit.input_value
    provenance=excel._build_ingress_provenance(preview,unit)
    workspace=projects.list_all()[0]
    workspace=replace(workspace,units=(replace(workspace.units[0],canonical_input=canonical,ingress_provenance=provenance),))
    projects.save(workspace)
    samples=[]
    for i in range(6):
        shell.navigate(AppRoute.EXCEL_IMPORT);app.processEvents()
        t=time.perf_counter_ns();opened=excel.open_project(workspace.project_id);app.processEvents();elapsed=time.perf_counter_ns()-t
        assert opened and excel._workspace.units[0].canonical_input==canonical
        samples.append(elapsed)
    add('project_open_canonical',samples[1:],samples[:1],{'saved_projects':len(projects.list_all()),'canonical_restored':True})
    use_case=CarbonAccountingUseCase(gui.calculator,records);samples=[];ids=[]
    for i in range(6):
        t=time.perf_counter_ns();outcome=use_case.calculate(canonical,ingress_provenance=provenance);elapsed=time.perf_counter_ns()-t
        assert outcome.successful and outcome.record is not None,str(outcome.problems)
        ids.append(outcome.record.record_id);samples.append(elapsed)
    assert len(set(ids))==6 and len(records.list_all())==count_before+6
    add('formal_application_calculation_append',samples[1:],samples[:1],{'records_added_including_warmup':6,'distinct_record_ids':6,'total_tco2':str(outcome.result.total_amount)})
    # Reopen frozen record using actual reporting stack. Save bytes; no export dialog/audit/UI timing.
    record=records.get(ids[-1]); db_before=hashlib.sha256((folder/'records.sqlite').read_bytes()).hexdigest();samples=[];sizes=[]
    for i in range(6):
        target=folder/f'report-{i}.docx';t=time.perf_counter_ns()
        model=build_saved_record_report(records,record);document=render_report_docx(model);write_report_atomically(target,document)
        elapsed=time.perf_counter_ns()-t
        assert target.is_file() and target.read_bytes()==document
        samples.append(elapsed);sizes.append(len(document))
    assert hashlib.sha256((folder/'records.sqlite').read_bytes()).hexdigest()==db_before
    add('word_frozen_record_model_render_save',samples[1:],samples[:1],{'records_database_unchanged':True,'document_bytes':sizes,'report_schema':model.schema_version})
    window.hide()
    data['production_after']=production_digest()
    assert data['production_after']==before
    data['finished_utc']=datetime.now(timezone.utc).isoformat()
    data['failure_count']=len(data['failures'])
    (OUT/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v['statistics'] for k,v in data['scenarios'].items()},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--startup-worker',nargs=2);args=parser.parse_args()
    if args.startup_worker: startup_worker(*(Path(p) for p in args.startup_worker))
    else: main()
