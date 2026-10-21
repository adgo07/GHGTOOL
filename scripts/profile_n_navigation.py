"""Serial offscreen navigation decomposition; synthetic stores only, immutable run folders."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
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
BASE = 'e186b5116f16861bc65fbb939abec750a39d7f0e'

def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def environment():
    power = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True).stdout.decode('mbcs', errors='replace').strip()
    # Read-only process CPU totals: snapshots are context, not system utilization percentages.
    ps = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Process | Sort-Object CPU -Descending | Select-Object -First 8 ProcessName,Id,CPU | ConvertTo-Json -Compress'], capture_output=True, text=True)
    return {'utc': datetime.now(timezone.utc).isoformat(), 'os': platform.platform(),
            'python': platform.python_version(), 'cpu': platform.processor(), 'logical_cpus': os.cpu_count(),
            'power_plan': power, 'top_process_cumulative_cpu': ps.stdout.strip(), 'background_probe_exit': ps.returncode}

def worker(folder, repeats):
    from scripts.measure_n_baseline import compose
    from PySide6.QtCore import QObject, QEvent, qVersion
    from packages.ui.view_models import AppRoute
    from packages.ui.shell import AppShell
    collector = {'current': None}
    def wrap(target, name, key):
        original = getattr(target, name)
        def measured(*args, **kwargs):
            start = time.perf_counter_ns()
            try:
                return original(*args, **kwargs)
            finally:
                sample = collector['current']
                if sample is not None:
                    sample['parts_ns'][key] += time.perf_counter_ns()-start
                    sample['calls'][key] += 1
        setattr(target, name, measured)
    wrap(AppShell, '_show_route', 'show_route')
    t = time.perf_counter_ns()
    app, window, records, projects = compose(folder)
    compose_ns = time.perf_counter_ns()-t
    shell = window.centralWidget()
    window.show(); app.processEvents()
    for target, method, key in ((shell, '_apply_content_geometry', 'geometry'),
                                (shell.scroll_host, 'setStyleSheet', 'ancestor_stylesheet'),
                                (records, 'list_all', 'records_full_query'),
                                (records, 'list_summaries', 'records_summary_query'),
                                (projects, 'list_all', 'projects_full_query'),
                                (projects, 'list_updated_at_by_project_id', 'project_revision_query')):
        wrap(target, method, key)
    class PaintProbe(QObject):
        def eventFilter(self, watched, event):
            sample = collector['current']
            if sample is not None and event.type() == QEvent.Type.Paint and sample['first_paint_ns'] is None:
                sample['first_paint_ns'] = time.perf_counter_ns()-sample['_start']
            return False
    probes = []
    original_ensure = shell._ensure_page
    def ensure(route):
        fresh = route not in shell._pages
        t = time.perf_counter_ns(); page = original_ensure(route)
        sample = collector['current']
        if sample is not None:
            sample['parts_ns']['ensure_page'] += time.perf_counter_ns()-t
            sample['calls']['ensure_page'] += 1
            sample['created'] = fresh
        if not getattr(page, '_n_probe_installed', False):
            probe = PaintProbe(page); page.installEventFilter(probe); probes.append(probe)
            page._n_probe_installed = True
        return page
    shell._ensure_page = ensure
    results = []
    def transition(route, kind, iteration, via_home=True):
        if via_home:
            shell.navigate(AppRoute.STANDARDS if route is AppRoute.HOME else AppRoute.HOME)
            app.processEvents()
        sample = {'route': route.value, 'kind': kind, 'iteration': iteration,
                  'parts_ns': defaultdict(int), 'calls': defaultdict(int), 'first_paint_ns': None}
        sample['_start'] = time.perf_counter_ns(); collector['current'] = sample
        shell.navigate(route)
        returned = time.perf_counter_ns()
        app.processEvents()
        ended = time.perf_counter_ns(); collector['current'] = None
        sample['navigate_ns'] = returned-sample['_start']; sample['event_pump_ns'] = ended-returned
        sample['total_ns'] = ended-sample.pop('_start')
        sample['correct_page'] = shell.page_stack.currentWidget() is shell._pages[route]
        assert sample['correct_page']
        sample['parts_ns'] = dict(sample['parts_ns']); sample['calls'] = dict(sample['calls'])
        results.append(sample)
    for route in AppRoute:
        transition(route, 'first_use', 0)
    for i in range(repeats):
        for route in AppRoute:
            transition(route, 'steady_home_reset', i)
        for route in (AppRoute.STANDARDS, AppRoute.RECORDS, AppRoute.FACTORS, AppRoute.SETTINGS):
            transition(route, 'steady_business_direct', i, False)
    window.hide()
    return {'compose_ns': compose_ns, 'qt': qVersion(), 'samples': results,
            'environment_after': environment()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--repeats', type=int, default=10)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    folder = ROOT/'tmp/n-navigation'/args.run
    if args.worker:
        write(folder/'worker.json', worker(folder, args.repeats)); return
    assert git('remote','get-url','origin') == 'https://github.com/adgo07/GHGTOOL.git'
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'], cwd=ROOT, check=True)
    assert not folder.exists(), 'Use a unique run name; never overwrite samples'
    folder.mkdir(parents=True)
    seed = folder/'seed'; seed.mkdir()
    from packages.persistence import build_catalog_database, SQLiteRecordRepository, SQLiteProjectWorkspaceRepository
    from packages.reference_data import DEFAULT_SOURCE_PATH
    from packages.application import ProjectWorkspaceService
    from tests.benchmark_navigation import make_record
    build_catalog_database(DEFAULT_SOURCE_PATH, seed/'catalog.sqlite')
    records = SQLiteRecordRepository(seed/'records.sqlite')
    for i in range(200): records.create(make_record(i))
    projects = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(seed/'projects.sqlite'))
    for i in range(20): projects.save(projects.new_workspace(f'合成性能项目{i:02d}'))
    production = hashlib.sha256()
    for name in git('ls-files','apps','packages','resources','pyproject.toml','platform-lock.json').splitlines():
        production.update(name.encode()); production.update((ROOT/name).read_bytes())
    data = {'schema': 1, 'base': BASE, 'head': git('rev-parse','HEAD'),
            'production_sha256': production.hexdigest(), 'production_diff': git('diff',BASE,'--','apps','packages'),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'environment_before': environment(), 'data': {'synthetic_records': 200, 'projects':20, 'viewport':'1280x800', 'platform':'offscreen'},
            'workers':[], 'failures':[]}
    for i in range(args.workers):
        session = folder/f'worker-{i}'; session.mkdir()
        for filename in ('records.sqlite','projects.sqlite','catalog.sqlite'):
            shutil.copy2(seed/filename, session/filename)
        relative = f'{args.run}/worker-{i}'
        command = [sys.executable,'-B',str(Path(__file__).resolve()),'--worker','--run',relative,'--repeats',str(args.repeats)]
        start = time.perf_counter_ns()
        process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=900)
        if process.returncode:
            data['failures'].append({'worker':i,'exit':process.returncode,'stderr':process.stderr.decode('utf-8',errors='replace')})
        else:
            result = json.loads((session/'worker.json').read_bytes())
            result['process_total_ns'] = time.perf_counter_ns()-start
            data['workers'].append(result)
        write(folder/'raw.json',data)
        print(f'worker {i+1}/{args.workers} complete; failures={len(data["failures"])}', flush=True)
    data['environment_after'] = environment()
    write(folder/'raw.json',data)
    for kind in ('first_use','steady_home_reset','steady_business_direct'):
        grouped = defaultdict(list)
        for item in data['workers']:
            for s in item['samples']:
                if s['kind'] == kind: grouped[s['route']].append(s)
        for route, samples in grouped.items():
            values = sorted(s['total_ns']/1e6 for s in samples)
            parts = {key:round(statistics.median(s['parts_ns'].get(key,0)/1e6 for s in samples),3) for key in {k for s in samples for k in s['parts_ns']}}
            print(kind,route,len(values),'median_ms',round(statistics.median(values),3),'p95_ms',round(values[math.ceil(.95*len(values))-1],3),parts,flush=True)
    assert not data['failures'], data['failures']

if __name__ == '__main__':
    main()
