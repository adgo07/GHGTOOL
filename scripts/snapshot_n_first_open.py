"""Offscreen production snapshots and normalized default states, outside all timing runs."""
from pathlib import Path
import hashlib,json,re,shutil,sys,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.measure_n_baseline import compose
from scripts.profile_n_navigation import write,git
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget,QComboBox,QLineEdit,QLabel,QCheckBox,QSpinBox,QDateEdit
from packages.ui.view_models import AppRoute
from packages.standards.carbon_material import EmissionSourceStatus
run=sys.argv[1];folder=ROOT/'tmp/n-first-open'/run;assert not folder.exists();folder.mkdir(parents=True)
for name in ('catalog.sqlite','records.sqlite','projects.sqlite'):shutil.copy2(ROOT/'tmp/n-first-open/seed'/name,folder/name)
errors=[]
def hook(kind,value,tb):errors.append(''.join(traceback.format_exception(kind,value,tb)));sys.__excepthook__(kind,value,tb)
sys.excepthook=hook
app,window,records,projects=compose(folder);app.setCursorFlashTime(0);window.show();shell=window.centralWidget()
def settle():
 for _ in range(4):app.processEvents()
 QTest.qWait(5)
 for _ in range(4):app.processEvents()
settle();shell.navigate(AppRoute.NEW_ACCOUNTING);settle();page=shell._pages[AppRoute.NEW_ACCOUNTING]
def normalize(value):
 if isinstance(value,str):return re.sub(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])','{fresh-id}',value)
 if isinstance(value,dict):return sorted([[normalize(k),normalize(v)] for k,v in value.items()],key=lambda pair:json.dumps(pair,ensure_ascii=False,sort_keys=True))
 if isinstance(value,(tuple,list)):return [normalize(x) for x in value]
 return value
proof={'head':git('rev-parse','HEAD'),'production_diff':git('diff','--','packages/ui'), 'qt_callback_errors':errors,'states':{},'images':[]}
def capture_state(label):
 state=normalize(page._capture_form_state())
 raw=json.dumps(state,ensure_ascii=False,sort_keys=True).encode()
 controls=[]
 for w in page.findChildren(QWidget):
  name=w.objectName()
  if not name:continue
  item={'class':type(w).__name__,'name':normalize(name),'enabled':w.isEnabled(),'hidden':w.isHidden()}
  if isinstance(w,QComboBox):item.update({'items':[w.itemText(i) for i in range(w.count())],'index':w.currentIndex()})
  elif isinstance(w,QLineEdit):item['text']=normalize(w.text())
  elif isinstance(w,QLabel):item['text']=normalize(w.text())
  elif isinstance(w,QCheckBox):item['checked']=w.isChecked()
  elif isinstance(w,QSpinBox):item['value']=w.value()
  elif isinstance(w,QDateEdit):item['date']=w.date().toString('yyyy-MM-dd')
  controls.append(item)
 controls.sort(key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True))
 proof['states'][label]={'normalized_form_state':state,'form_sha256':hashlib.sha256(raw).hexdigest(),'named_controls':controls,
                         'controls_sha256':hashlib.sha256(json.dumps(controls,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                         'dirty':[page._project_dirty,page._input_dirty]}
capture_state('initial')
for width,height in ((1180,720),(1280,800),(1600,900)):
 window.resize(width,height);settle()
 focus=app.focusWidget()
 if focus is not None:focus.clearFocus()
 shell.main_scroll_area.verticalScrollBar().setValue(0);settle()
 image=shell.main_scroll_area.viewport().grab().toImage();name=f'default-{width}.png';image.save(str(folder/name))
 proof['images'].append({'name':name,'size':[image.width(),image.height()],'sha256':hashlib.sha256(bytes(image.constBits())).hexdigest()})
for combo in page._source_statuses.values():combo.setCurrentIndex(combo.findData(EmissionSourceStatus.INVOLVED))
settle();capture_state('all_sources_enabled')
targets=[('top',None)]
for group,label,ids in page._source_toggle_groups:
 target=page._unified_energy_cards.get(group) if group in ('electricity','heat') else page._source_cards[ids[0]]
 targets.append((group,target))
for width,height in ((1180,720),(1280,800),(1600,900)):
 window.resize(width,height);settle()
 for key,target in targets:
  bar=shell.main_scroll_area.verticalScrollBar();bar.setValue(0 if target is None else max(0,target.mapTo(shell.scroll_host,QPoint(0,0)).y()-12));settle()
  image=shell.main_scroll_area.viewport().grab().toImage();name=f'enabled-{width}-{key}.png';image.save(str(folder/name))
  proof['images'].append({'name':name,'size':[image.width(),image.height()],'sha256':hashlib.sha256(bytes(image.constBits())).hexdigest()})
window.hide();assert not errors,errors
write(folder/'proof.json',proof);print(f'states={len(proof["states"])} images={len(proof["images"])} callback_errors={len(errors)}',flush=True)
