"""Read-only current/main Qt geometry diagnosis; never forces product refresh."""
import sys, json, gc, hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from tests.test_uat02_usability import UAT02UsabilityTests as Case
import packages.ui.carbon_material_page as product
out=Path(sys.argv[1]); identity=sys.argv[2]
errors=[];sys.excepthook=lambda kind,value,trace:errors.append(f'{kind.__name__}: {value}')
Case.setUpClass(); assert QApplication.platformName()=='offscreen'
report={'identity':identity,'product_module':product.__file__,'product_sha256':hashlib.sha256(Path(product.__file__).read_bytes()).hexdigest(),'normal_events_only':True}
def sample(case):
 page=case.page;host=page.fuel_rows_host;bar=case.shell.main_scroll_area.verticalScrollBar()
 rows=list(page._fuel_rows)
 return {'outer_height':case.shell.scroll_host.height(),'scroll_max':bar.maximum(),'fuel_host':[host.width(),host.height()],
 'rows':len(rows),'all_rows_inside_host':all(host.rect().contains(row.geometry()) for row in rows),
 'all_rows_meet_minimum':all(row.height()>=row.minimumSizeHint().height() for row in rows),
 'no_row_overlap':all(rows[i-1].geometry().bottom()<row.geometry().top() for i,row in enumerate(rows) if i),
 'first':rows[0].geometry().getRect(),'last':rows[-1].geometry().getRect()}
def normal(case):
 values=[]
 for _ in range(24):
  case.application.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
  values.append(sample(case))
 return {'samples':values,'settled_last_three':values[-1]==values[-2]==values[-3],'final':values[-1]}
case=Case('test_twenty_dynamic_rows_expand_and_shrink_scroll_host');case.setUp()
try:
 try:
  case.test_twenty_dynamic_rows_expand_and_shrink_scroll_host();report['original_test']={'status':'PASS'}
 except AssertionError as exc:
  report['original_test']={'status':'FAIL','message':str(exc),'at_assertion':sample(case)}
 report['after_original_normal_events']=normal(case)
finally:
 case.tearDown();case=None;gc.collect()
case=Case('test_twenty_dynamic_rows_expand_and_shrink_scroll_host');case.setUp()
try:
 case.page._source_toggle_buttons['fuel'].click();report['steady_baseline']=normal(case)
 for _ in range(20):case.page._add_fuel_row()
 report['steady_grown']=normal(case)
 removed=case.page._fuel_rows[10];remaining=[row for row in case.page._fuel_rows if row is not removed]
 case.page._remove_fuel_row(removed);report['steady_shrunk']=normal(case)
 report['remaining_identity_preserved']=case.page._fuel_rows==remaining
 a=report['steady_baseline']['final'];b=report['steady_grown']['final'];c=report['steady_shrunk']['final']
 report['normal_growth_and_shrink']=(b['outer_height']>a['outer_height'] and c['outer_height']<b['outer_height'] and c['scroll_max']<b['scroll_max'])
finally:
 case.tearDown();case=None;gc.collect();Case.application.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
 Case.tearDownClass()
report['callback_errors']=errors
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'identity':identity,'original':report['original_test'],'normal_growth_and_shrink':report['normal_growth_and_shrink'],
 'baseline':a,'grown':b,'shrunk':c,'callback_errors':errors},ensure_ascii=False))
