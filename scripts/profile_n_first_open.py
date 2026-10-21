"""Serial first-editor-open profiling with a fixed, byte-identical synthetic seed."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.environ['QT_QPA_PLATFORM']='offscreen'
BASE='bb28ffe4c4c2733de57a3c6be8a63ee8c3b1b9ec'
from scripts.profile_n_navigation import environment, git, write

def worker(folder):
    from scripts.measure_n_baseline import compose
    from PySide6.QtCore import QObject,QEvent
    from PySide6.QtWidgets import QWidget
    from packages.ui.view_models import AppRoute
    from packages.ui.shell import AppShell
    from packages.ui.carbon_material_page import CarbonMaterialAccountingPage as Page
    from packages.application.catalog_queries import CatalogQueryService
    from packages.core.parameter_resolution import ParameterResolver
    from packages.persistence.catalog_repository import SQLiteCatalogRepository
    callback_errors=[]
    import traceback
    def capture_callback_error(kind,value,tb):
        callback_errors.append(''.join(traceback.format_exception(kind,value,tb)))
        sys.__excepthook__(kind,value,tb)
    sys.excepthook=capture_callback_error
    current={'sample':None,'stack':[]}
    def wrap(target,name,label):
        original=getattr(target,name)
        def measured(*args,**kwargs):
            sample=current['sample']
            if sample is None:return original(*args,**kwargs)
            key=label
            if name=='_build_process_section':key+='.'+str(args[3])
            entry=[time.perf_counter_ns(),0];current['stack'].append(entry)
            try:return original(*args,**kwargs)
            finally:
                elapsed=time.perf_counter_ns()-entry[0];current['stack'].pop()
                if current['stack']:current['stack'][-1][1]+=elapsed
                item=sample['parts'].setdefault(key,{'calls':0,'inclusive_ns':0,'self_ns':0})
                item['calls']+=1;item['inclusive_ns']+=elapsed;item['self_ns']+=elapsed-entry[1]
        parameters=list(inspect.signature(original).parameters.values())
        if len(parameters)==1 and parameters[0].name=='self':
            # PySide6 uses the Python callable's arity to discard extra signal arguments.
            def no_argument_slot(self):return measured(self)
            setattr(target,name,no_argument_slot)
        else:
            setattr(target,name,measured)
    names=('__init__','_build_page','_build_project_unit_controls','_build_source_cards','_build_unified_energy_section',
           '_build_fuel_section','_build_process_section','_build_material_controls','_build_electricity_section',
           '_build_output_electricity_section','_build_heat_section','_build_output_heat_section',
           '_apply_accounting_style','_refresh_source_cards','_refresh_enterprise_candidates',
           '_refresh_energy_region_options','_refresh_energy_factor_options','_refresh_heat_factor_details',
           '_capture_form_state','_install_dirty_tracking','_refresh_content_geometry')
    for name in names:wrap(Page,name,'page.'+name)
    for name in ('_ensure_page','_show_route','_apply_content_geometry'):wrap(AppShell,name,'shell.'+name)
    wrap(ParameterResolver,'resolve','resolver.resolve')
    for target,prefix in ((CatalogQueryService,'catalog_service'),(SQLiteCatalogRepository,'catalog_repository')):
        for name,member in list(target.__dict__.items()):
            if name.startswith(('list_','get_','search_','standard_')) and inspect.isfunction(member):wrap(target,name,prefix+'.'+name)
    app,window,records,projects=compose(folder);shell=window.centralWidget();window.show();app.processEvents()
    for target,name,label in ((records,'list_all','records.list_all'),(records,'list_summaries','records.list_summaries'),
                              (projects,'list_all','projects.list_all'),(projects,'list_updated_at_by_project_id','projects.revisions')):
        wrap(target,name,label)
    class PaintProbe(QObject):
        def eventFilter(self,watched,event):
            sample=current['sample']
            if sample is not None and event.type()==QEvent.Type.Paint and sample['paint_ns'] is None:
                sample['paint_ns']=time.perf_counter_ns()-sample['_start']
            return False
    probes=[];original_ensure=shell._ensure_page
    def ensure(route):
        page=original_ensure(route)
        if route is AppRoute.NEW_ACCOUNTING and not probes:
            probe=PaintProbe(page);page.installEventFilter(probe);probes.append(probe)
        return page
    shell._ensure_page=ensure
    samples=[]
    def transition(kind):
        sample={'kind':kind,'parts':{},'paint_ns':None};sample['_start']=time.perf_counter_ns();current['sample']=sample
        shell.navigate(AppRoute.NEW_ACCOUNTING);returned=time.perf_counter_ns();app.processEvents();ended=time.perf_counter_ns()
        current['sample']=None
        sample['navigate_ns']=returned-sample['_start'];sample['event_pump_ns']=ended-returned;sample['total_ns']=ended-sample.pop('_start')
        sample['correct_page']=shell.page_stack.currentWidget() is shell._pages[AppRoute.NEW_ACCOUNTING];assert sample['correct_page']
        samples.append(sample)
    transition('first_open')
    page=shell._pages[AppRoute.NEW_ACCOUNTING]
    initial={'qwidgets':len(page.findChildren(QWidget)),'source_cards':len(page._source_cards),'fields':len(page._fields),
             'project_dirty':page._project_dirty,'input_dirty':page._input_dirty,'default_form_state_keys':len(page._default_form_state)}
    for i in range(2):
        shell.navigate(AppRoute.HOME);app.processEvents();transition('cached_return')
    window.hide()
    assert not callback_errors,callback_errors
    return {'qt_callback_errors':callback_errors,'samples':samples,'initial_state':initial,'environment_after':environment()}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--workers',type=int,default=20);parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    folder=ROOT/'tmp/n-first-open'/args.run
    if args.worker:write(folder/'worker.json',worker(folder));return
    assert git('remote','get-url','origin')=='https://github.com/adgo07/GHGTOOL.git'
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    assert not folder.exists(),'Use unique run directory; never overwrite samples'
    folder.mkdir(parents=True);seed=ROOT/'tmp/n-first-open/seed'
    names=('catalog.sqlite','records.sqlite','projects.sqlite')
    seed_sha={name:hashlib.sha256((seed/name).read_bytes()).hexdigest() for name in names}
    production=hashlib.sha256()
    for name in git('ls-files','apps','packages','resources','pyproject.toml','platform-lock.json').splitlines():production.update(name.encode());production.update((ROOT/name).read_bytes())
    result={'schema':1,'base':BASE,'head':git('rev-parse','HEAD'),'worker_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'production_sha256':production.hexdigest(),'production_diff':git('diff',BASE,'--','apps','packages'),
            'seed_sha256':seed_sha,'data':{'records':200,'projects':20,'requested_window':[1280,800],'qt_platform':'offscreen'},
            'environment_before':environment(),'workers':[],'failures':[]}
    for i in range(args.workers):
        session=folder/f'worker-{i:02d}';session.mkdir()
        for name in names:shutil.copy2(seed/name,session/name)
        start=time.perf_counter_ns();process=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker','--run',f'{args.run}/{session.name}'],cwd=ROOT,capture_output=True,timeout=180)
        if process.returncode:result['failures'].append({'worker':i,'exit':process.returncode,'stderr':process.stderr.decode('utf-8',errors='replace')})
        else:
            value=json.loads((session/'worker.json').read_bytes());value['batch']=i//10;value['process_total_ns']=time.perf_counter_ns()-start;result['workers'].append(value)
        write(folder/'raw.json',result);print(f'worker {i+1}/{args.workers}; failures={len(result["failures"])}',flush=True)
    assert seed_sha=={name:hashlib.sha256((seed/name).read_bytes()).hexdigest() for name in names}
    result['environment_after']=environment();write(folder/'raw.json',result);assert not result['failures']
if __name__=='__main__':main()
