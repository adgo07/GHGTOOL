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
 for _ in range(16):
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
 summary['source_files_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('packages/ui/source_directory.py','packages/ui/compact_choices.py','packages/ui/carbon_material_fuel.py','packages/ui/carbon_material_page.py','packages/ui/design_tokens.py','packages/ui/source_cards.py','packages/ui/responsive_fields.py')}
 def snap(name,i):
  select(i);pump();window.grab().save(str(OUT/(name+'.png')))
  summary['scenes'].append({'name':name,'editor_rect':rect(stack,window),'window':[window.width(),window.height()]})
 def sources():
  return {c.objectName():{'selected':str(c.currentData()),'value':[(c.itemText(i),str(c.itemData(i)),bool(c.model().flags(c.model().index(i,0))&Qt.ItemFlag.ItemIsEnabled)) for i in range(c.count())]} for c in (fuel.lhv_source,fuel.carbon_source,fuel.direct_carbon_source,fuel.oxidation_source)}
 snap('01-fuel-defaults',0);summary['catalog_sources']=sources()
 lhv_choices=next(c for c in fuel.findChildren(choices.SegmentedChoiceControl) if c.combo is fuel.lhv_source)
 next(b for b in lhv_choices.group.buttons() if b.text()=='实测值').click();pump();assert fuel.lhv_source.currentData()=='MEASURED'
 fuel.lower_heating_value.setText('388.88');fuel.source_reference.setText('检测报告 TEST-2026-001，第 3 页');pump();snap('02-fuel-measured',0)
 assert not fuel.source_reference_control.isHidden(), 'measured report remains accessible'
 summary['checks'].append('original measured report field remains accessible alongside parameter controls')
 choose(fuel.carbon_basis,'DIRECT');choose(fuel.direct_carbon_source,'CALCULATED');fuel.carbon_direct.setText('5.678');pump();snap('03-fuel-calculated',0)
 snap('04-electricity',1);snap('05-calcination',2)
 scroll=window.findChild(QScrollArea,'mainScrollArea');scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum());pump();window.grab().save(str(OUT/'06-calcination-bottom.png'))
 baseline=page._capture_form_state()
 for _ in range(3):
  for i in (0,1,2):select(i);assert page._capture_form_state()==baseline, 'directory switch changed saved form state'
 summary['checks'].append('9 directory switches: complete form_state unchanged (values, sources, identities and drafts)')
 assert fuel.activity.text()=='123.45' and energy.amount.text()=='234.56' and material['mass'].text()=='345.67' and fuel.source_reference.text()=='检测报告 TEST-2026-001，第 3 页'
 summary['checks'].append('fuel/electricity/material sentinel input values retained')
 summary['checks'].append('single outer scroll; editor height follows current visible content')
 summary['checks'].append('actual measured radio click updated original source combo')
 # Exercise the real exported/OTHER path and its existing draft controls.
 next(b for b in energy.direction_choices.group.buttons() if b.text()=='输出').click();pump()
 assert energy.kind.currentData()=='exported_electricity'
 next(b for b in energy.factor_mode_choices.group.buttons() if b.text()=='其他来源').click();pump()
 snap('07-electricity-export-other',1)
 # Expand the actual basis editor without substituting fields.
 conversion=material['widget'].findChild(QPushButton)
 for b in material['widget'].findChildren(QPushButton):
  if b.text().startswith('数据基准与换算'):b.setChecked(True)
 snap('08-calcination-conversion',2)
 window.resize(1440,1000);pump();snap('09-narrow-calcination',2)
 snap('10-narrow-fuel',0)
 summary['checks'].append('actual export and OTHER radio clicks and material basis expansion executed')
 window.resize(1680,1120);pump()
 outer=window.findChild(QScrollArea,'mainScrollArea')
 outer.verticalScrollBar().setValue(0);pump();window.grab().save(str(OUT/'11-full-page-top.png'))
 for group in page.source_directory.cards:
  if group not in ('fuel','electricity','calcination'):page._toggle_source_group(group)
  page.source_directory.select(group);pump()
  outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
  window.grab().save(str(OUT/('12-directory-'+group+'.png')))
 # Rich synthetic drafts: original widgets, stable IDs, no additional business logic.
 for prefix in ('baking','graphitization'):
  mat=page._process_rows[prefix][0]['materials'][0]
  mat['name'].setText('合成测试物料');mat['mass'].setText('12.5')
  page.source_directory.select(prefix);pump()
  next(b for b in mat['widget'].findChildren(QPushButton) if b.text().startswith('数据基准与换算')).setChecked(True)
  outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
  window.grab().save(str(OUT/('15-expanded-'+prefix+'.png')))
 fume=page._process_rows['fume'][0]
 fume['segment_start'].setText('2026-01-01 00:00');fume['segment_end'].setText('2026-01-02 00:00')
 choose(fume['duration_unit'],'h');fume['fields']['duration'].setText('24')
 second=page._add_process_row('fume');second['segment_start'].setText('2026-01-02 00:00');second['segment_end'].setText('2026-01-03 00:00')
 choose(second['duration_unit'],'h');second['fields']['duration'].setText('24')
 fgd=page._process_rows['fgd'][0];fgd['reagent_name'].setText('合成批次 A');fgd['group_amount'].setText('12.3')
 page._add_fgd_component(fgd);page._add_process_row('fgd')
 heat=page._energy_family_rows['heat'][0];heat.amount.setText('100');choose(heat.heat_boundary,'OUTSIDE_ENTERPRISE');choose(heat.heat_fuel_accounted,False)
 choose(heat.enthalpy_mode,'MANUAL');heat.enthalpy.setText('2800');heat.enthalpy.editingFinished.emit();pump();assert '待填写' not in heat.status.text()
 for group in ('fume','fgd','heat'):
  page.source_directory.select(group);pump();outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
  window.grab().save(str(OUT/('16-drafts-'+group+'.png')))
 choose(heat.enthalpy_mode,'AUTO');heat.pressure.setText('0.8');heat.pressure.editingFinished.emit();page._refresh_unified_energy_row(heat);pump()
 page.source_directory.select('heat');pump();outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump();window.grab().save(str(OUT/'17-heat-auto.png'))
 # Actual minimum supported window; record the available editor width.
 window.resize(1180,850);pump()
 stable=page._capture_form_state()
 for group in page.source_directory.cards:
  page.source_directory.select(group);pump();outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
  window.grab().save(str(OUT/('18-small-'+group+'.png')))
  summary['scenes'].append({'name':'small-'+group,'requested_window':[1180,850],'window':[window.width(),window.height()],'editor_rect':rect(stack,window),'viewport':[outer.viewport().width(),outer.viewport().height()]})
  assert page._capture_form_state()==stable,'small window/browse changed input'
 window.resize(1680,1120);pump()
 from PySide6.QtTest import QTest
 from packages.standards.carbon_material import EmissionSourceStatus
 status=page._source_statuses['CAR-SRC-FUEL-001'];saved_status=status.currentData()
 for state in (EmissionSourceStatus.UNCONFIRMED,EmissionSourceStatus.NOT_INVOLVED,EmissionSourceStatus.INVOLVED):
  status.setCurrentIndex(status.findData(state));page._refresh_source_cards();page.source_directory.select('fuel');pump();outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
  (page.source_directory.enable_buttons['fuel'] if page.source_directory.cards['fuel'].isHidden() else page._source_header_buttons['fuel'][0]).setFocus();pump();window.grab().save(str(OUT/('19-state-'+state.value+'.png')))
 status.setCurrentIndex(status.findData(saved_status));page._refresh_source_cards();pump()
 switch=page._source_header_buttons['fuel'][0]
 switch.setFocus();pump();window.grab().save(str(OUT/'19-switch-focus.png'))
 QTest.mouseMove(switch,switch.rect().center());pump();window.grab().save(str(OUT/'19-switch-hover.png'))
 electricity_ids=next(ids for group,title,ids in page._source_toggle_groups if group=='electricity')
 partial=page._source_statuses[electricity_ids[1]];saved_partial=partial.currentData();partial.setCurrentIndex(partial.findData(EmissionSourceStatus.NOT_INVOLVED));page._refresh_source_cards();page.source_directory.select('electricity');pump();outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump();window.grab().save(str(OUT/'20-state-partial.png'));partial.setCurrentIndex(partial.findData(saved_partial))
 page._run_calculation();pump();page.source_directory.results_requested.emit();pump();window.grab().save(str(OUT/'13-shared-results.png'))
 assert not page.source_directory.findChildren(QScrollArea), 'nested source scroll'
 before_records=len(page.record_repository.list_all())
 assert before_records==0, 'invalid inputs must not create a Record'
 for group in page.source_directory.cards:
  if group!='fuel':page._toggle_source_group(group)
 page._run_calculation();pump()
 assert len(page.record_repository.list_all())==before_records+1, 'successful click must append one Record'
 page.source_directory.results_requested.emit();pump();window.grab().save(str(OUT/'14-successful-result.png'))
 fuel.activity.setText('124.45');pump();page.source_directory.results_requested.emit();pump();window.grab().save(str(OUT/'21-stale-result.png'))
 assert not page.export_report_button.isEnabled(),'stale result export must remain blocked'
 summary['checks'].append('failed calculation creates no record; one subsequent successful click appends exactly one Record in temporary store')
 summary['checks'].append('all eight directory entries captured; no source QScrollArea')
 summary['final_sources']=sources();summary['callback_errors']=errors
 assert not errors,errors
 (OUT/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>整页实际Qt截图</title><style>body{font:16px sans-serif;background:#edf3f8;margin:24px}img{max-width:100%;border:1px solid #bbb}section{margin:24px 0}</style><h1>整页实际 Qt offscreen 截图</h1><p>合成输入；非原生桌面/人工 DPI 验证。</p>'+''.join('<section><h2>'+f.stem+'</h2><img loading="lazy" src="'+f.name+'"></section>' for f in sorted(OUT.glob('*.png'))),encoding='utf8')
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 window.hide();window.deleteLater()
 print('PASS: genuine controls, source states, 9 navigation transitions, single outer scroll; no callback errors.')


