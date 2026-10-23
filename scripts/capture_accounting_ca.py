"""Capture the implemented C+A business page offscreen with synthetic inputs."""
import os,sys,json,tempfile,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt,QPoint,qVersion,QCoreApplication,QEvent
from PySide6.QtGui import QFont,QFontDatabase
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QRadioButton,QScrollArea,QStackedWidget,QComboBox,QLineEdit,QFrame
import packages.ui.compact_choices as choices
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.persistence import build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from packages.standards.carbon_material import FuelType
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
app=QApplication([])
for n in ('msyh.ttc','msyhbd.ttc','seguisym.ttf'):QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/n))
app.setFont(QFont('Microsoft YaHei',9))
errors=[];sys.excepthook=lambda t,v,tb:(errors.append(f'{t.__name__}: {v}'),sys.__excepthook__(t,v,tb))
def pump():
 for _ in range(5):
  app.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
def choose(combo,value):
 i=combo.findData(value);assert i>=0,(combo.objectName(),value);combo.setCurrentIndex(i);pump()
def rect(w,window):
 p=w.mapTo(window,QPoint(0,0));return [p.x(),p.y(),w.width(),w.height()]
with tempfile.TemporaryDirectory(prefix='qz-ca-preview-') as tmp:
 os.environ['LOCALAPPDATA']=tmp;root=Path(tmp)
 catalog=build_catalog_database(DEFAULT_SOURCE_PATH,root/'catalog.sqlite')
 window=create_main_window(AppConfig(catalog_database=catalog,log_directory=root/'logs'));window.resize(1680,1120);window.show()
 shell=window.centralWidget();shell.navigate(AppRoute.NEW_ACCOUNTING);page=shell.pages[AppRoute.NEW_ACCOUNTING];pump()
 for group in ('fuel','electricity','calcination'):page._toggle_source_group(group)
 fuel=page._fuel_rows[0];fuel.fuel_type.setCurrentIndex(fuel.fuel_type.findData(FuelType.NATURAL_GAS));fuel.fuel_type.confirm_name(force=True);pump()
 fuel.activity.setText('123.45')
 energy=page._energy_family_rows['electricity'][0];energy.amount.setText('234.56')
 process=page._process_rows['calcination'][0];material=process['materials'][0]
 material['name'].setText('样板石油焦（合成测试）');material['mass'].setText('345.67');pump()
 cards=[page._source_cards['CAR-SRC-FUEL-001'],page._unified_energy_cards['electricity'],page._source_cards['CAR-SRC-CALCINATION-001']]
 original_ids=[[id(x) for x in c.findChildren(QComboBox)+c.findChildren(QLineEdit)] for c in cards]
 stack=page.source_directory.stack
 def select(i):
  page.source_directory.select(('fuel','electricity','calcination')[i]);pump()
  scroll=window.findChild(QScrollArea,'mainScrollArea')
  scroll.verticalScrollBar().setValue(page.source_directory.mapTo(scroll.widget(),QPoint(0,0)).y());pump()
 select(0)
 assert original_ids==[[id(x) for x in c.findChildren(QComboBox)+c.findChildren(QLineEdit)] for c in cards], 'real widget identity changed'
 summary={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'qt':qVersion(),'platform':app.platformName(),'real_widgets_preserved':True,'scenes':[],'checks':[]}
 summary['source_files_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('packages/ui/source_directory.py','packages/ui/compact_choices.py','packages/ui/carbon_material_fuel.py','packages/ui/carbon_material_page.py','packages/ui/design_tokens.py')}
 def snap(name,i):
  select(i);page.source_directory.scrollers[('fuel','electricity','calcination')[i]].verticalScrollBar().setValue(0);pump();window.grab().save(str(OUT/(name+'.png')))
  summary['scenes'].append({'name':name,'editor_rect':rect(stack,window),'window':[window.width(),window.height()]})
 def sources():
  return {c.objectName():{'selected':str(c.currentData()),'value':[(c.itemText(i),str(c.itemData(i)),bool(c.model().flags(c.model().index(i,0))&Qt.ItemFlag.ItemIsEnabled)) for i in range(c.count())]} for c in (fuel.lhv_source,fuel.carbon_source,fuel.direct_carbon_source,fuel.oxidation_source)}
 snap('01-fuel-defaults',0);summary['catalog_sources']=sources()
 lhv_choices=next(c for c in fuel.findChildren(choices.SegmentedChoiceControl) if c.combo is fuel.lhv_source)
 next(b for b in lhv_choices.group.buttons() if b.text()=='实测值').click();pump();assert fuel.lhv_source.currentData()=='MEASURED'
 fuel.lower_heating_value.setText('388.88');fuel.source_reference.setText('检测报告 TEST-2026-001，第 3 页');pump();snap('02-fuel-measured',0)
 assert abs(rect(fuel.source_reference,window)[1]-rect(fuel.calculated_carbon_label,window)[1])<=2, 'report input not aligned with corresponding row'
 summary['checks'].append('shared measured report and carbon input aligned within 2 pixels')
 choose(fuel.carbon_basis,'DIRECT');choose(fuel.direct_carbon_source,'CALCULATED');fuel.carbon_direct.setText('5.678');pump();snap('03-fuel-calculated',0)
 snap('04-electricity',1);snap('05-calcination',2)
 scroll=page.source_directory.scrollers['calcination'];scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum());pump();window.grab().save(str(OUT/'06-calcination-bottom.png'))
 baseline=page._capture_form_state()
 for _ in range(3):
  for i in (0,1,2):select(i);assert page._capture_form_state()==baseline, 'directory switch changed saved form state'
 summary['checks'].append('9 directory switches: complete form_state unchanged (values, sources, identities and drafts)')
 assert fuel.activity.text()=='123.45' and energy.amount.text()=='234.56' and material['mass'].text()=='345.67' and fuel.source_reference.text()=='检测报告 TEST-2026-001，第 3 页'
 summary['checks'].append('fuel/electricity/material sentinel input values retained')
 assert len({tuple(s['editor_rect'][:2]) for s in summary['scenes']})==1
 summary['checks'].append('all scenes share the exact editor origin')
 summary['checks'].append('actual measured radio click updated original source combo')
 # Exercise the real exported/OTHER path and its existing draft controls.
 next(b for b in energy.direction_choices.group.buttons() if b.text()=='输出').click();pump()
 assert energy.kind.currentData()=='exported_electricity'
 next(b for b in energy.factor_mode_choices.group.buttons() if b.text()=='其他来源').click();pump()
 snap('07-electricity-export-other',1)
 # Expand the actual basis editor without substituting fields.
 conversion=material['widget'].findChild(QPushButton)
 for b in material['widget'].findChildren(QPushButton):
  if b.text()=='数据基准与换算':b.setChecked(True)
 snap('08-calcination-conversion',2)
 window.resize(1440,1000);pump();snap('09-narrow-calcination',2)
 snap('10-narrow-fuel',0)
 summary['checks'].append('actual export and OTHER radio clicks and material basis expansion executed')
 summary['final_sources']=sources();summary['callback_errors']=errors
 assert not errors,errors
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 window.hide();window.deleteLater()
 print('PASS: genuine controls, source states, 9 navigation transitions, exact editor origin; no callback errors.')


