import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from tests.test_uat02_geometry import UAT02GeometryTests
original=UAT02GeometryTests._assert_scroll_geometry_matches_page
records=[]
def snapshot(test):
    return dict(host=test.shell.scroll_host.height(),expected=max(test.shell.main_scroll_area.viewport().height(),test.shell.page_stack.sizeHint().height()),scroll_max=test.shell.main_scroll_area.verticalScrollBar().maximum(),rows=len(test.page._fuel_rows))
def observed(test):
    try:original(test)
    except AssertionError:
        samples=[snapshot(test)]
        for _ in range(16):
            test.application.processEvents();samples.append(snapshot(test))
        records.append(samples)
        raise
UAT02GeometryTests._assert_scroll_geometry_matches_page=observed
names=['tests.test_navigation_background.NavigationBackgroundTests.test_pending_geometry_callback_is_cancelled_when_shell_is_destroyed','tests.test_uat02_geometry.UAT02GeometryTests.test_dynamic_fuel_rows_resize_scroll_host_across_source_toggle']
with Path('build/ui-v2-integration/context-probe/lifecycle-geometry-before.log').open('w',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
Path('build/ui-v2-integration/context-probe/geometry-after-failure.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('tests',result.testsRun,'failures',len(result.failures),'errors',len(result.errors),'post-failure-observations',len(records),flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
