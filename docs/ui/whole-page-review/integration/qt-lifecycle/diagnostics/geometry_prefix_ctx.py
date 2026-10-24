import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
out=Path('build/ui-v2-integration/context-probe')/sys.argv[1];out.mkdir(exist_ok=False)
from tests.test_uat02_geometry import UAT02GeometryTests
original=UAT02GeometryTests._assert_scroll_geometry_matches_page
records=[];errors=[];old_hook=sys.excepthook
def snapshot(test):
    return dict(host=test.shell.scroll_host.height(),expected=max(test.shell.main_scroll_area.viewport().height(),test.shell.page_stack.sizeHint().height()),scroll_max=test.shell.main_scroll_area.verticalScrollBar().maximum(),rows=len(test.page._fuel_rows))
def observed(test):
    try:original(test)
    except AssertionError:
        samples=[snapshot(test)]
        for _ in range(16):test.application.processEvents();samples.append(snapshot(test))
        records.append(samples)
        raise
UAT02GeometryTests._assert_scroll_geometry_matches_page=observed
def hook(kind,value,tb):
    errors.append(f'{kind.__name__}: {value}');old_hook(kind,value,tb)
sys.excepthook=hook
command=json.loads(Path('build/ui-v2-integration/context-probe/plain-callers-command.json').read_text())
names=[x for x in command if x.startswith('tests.')][:6]
(out/'selection.json').write_text(json.dumps(names,indent=2),encoding='utf-8')
with (out/'tests.log').open('x',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
(out/'after-failure.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(out/'callback-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
print('tests',result.testsRun,'failures',len(result.failures),'errors',len(result.errors),'post-failure-observations',len(records),'Qt callback errors',len(errors),flush=True)
sys.exit(0 if result.wasSuccessful() and not errors else 1)
