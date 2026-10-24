import hashlib, json, os, sys, tempfile
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import QPoint,QCoreApplication,QEvent,qVersion
from PySide6.QtGui import QFont,QFontDatabase
from PySide6.QtWidgets import QApplication,QAbstractButton,QComboBox,QLineEdit,QScrollArea
from apps.carbon_accounting_desktop.app import create_main_window
from apps.carbon_accounting_desktop.config import AppConfig
from packages.persistence import build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.ui.view_models import AppRoute
from packages.standards.carbon_material import FuelType
from packages.ui.compact_choices import SegmentedChoiceControl
out=root/'docs/ui/whole-page-review/integration/fuel-capture'
app=QApplication([])
for name in ('msyh.ttc','msyhbd.ttc','seguisym.ttf'):
    QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/name))
app.setFont(QFont('Microsoft YaHei',9))
errors=[]
sys.excepthook=lambda kind,value,trace:errors.append(f'{kind.__name__}: {value}')
def pump():
    for _ in range(16):
        app.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
with tempfile.TemporaryDirectory(prefix='qz-direct-expanded-') as tmp:
    os.environ['LOCALAPPDATA']=tmp
    db=build_catalog_database(DEFAULT_SOURCE_PATH,Path(tmp)/'catalog.sqlite')
    window=create_main_window(AppConfig(catalog_database=db,log_directory=Path(tmp)/'logs'))
    window.resize(1680,1120);window.show()
    window.centralWidget().navigate(AppRoute.NEW_ACCOUNTING)
    page=window.centralWidget().pages[AppRoute.NEW_ACCOUNTING];pump()
    page._toggle_source_group('fuel');page.source_directory.select('fuel')
    fuel=page._fuel_rows[0]
    fuel.fuel_type.setCurrentIndex(fuel.fuel_type.findData(FuelType.NATURAL_GAS));fuel.fuel_type.confirm_name(force=True)
    fuel.carbon_basis.setCurrentIndex(fuel.carbon_basis.findData('DIRECT'))
    direct=next(c for c in fuel.findChildren(SegmentedChoiceControl) if c.combo is fuel.direct_carbon_source)
    next(b for b in direct.group.buttons() if fuel.direct_carbon_source.itemData(direct.group.id(b))=='CALCULATED').click()
    fuel.carbon_direct.setText('5.678');fuel.source_reference.setText('检测报告 EXPANDED-2026-001，第 3 页')
    fuel.inactive_parameters_toggle.setChecked(True);pump()
    original=page._capture_form_state();scenes=[]
    for width,height in ((1680,1120),(1180,850)):
        window.resize(width,height);pump()
        outer=window.findChild(QScrollArea,'mainScrollArea')
        outer.verticalScrollBar().setValue(page.source_directory.mapTo(outer.widget(),QPoint(0,0)).y());pump()
        assert page._capture_form_state()==original
        for name in ('lhv_source','carbon_source'):
            combo=getattr(fuel,name)
            choice=next(c for c in fuel.findChildren(SegmentedChoiceControl) if c.combo is combo)
            assert choice.isVisibleTo(fuel) and combo.isHidden()
            assert all(not button.isEnabled() for button in choice.group.buttons())
        for control in fuel.findChildren(QLineEdit)+fuel.findChildren(QAbstractButton)+fuel.findChildren(QComboBox):
            if control.isVisibleTo(fuel):
                assert control.parentWidget().rect().contains(control.geometry()),(control.objectName(),control.geometry())
        name=f'22-direct-expanded-{width}.png'
        assert window.grab().save(str(out/name))
        scenes.append(dict(name=name,window=[window.width(),window.height()],editor_width=page.source_directory.stack.width()))
    assert not errors,errors
    assert len(page.record_repository.list_all())==0
    hashes={path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in json.loads((out/'summary.json').read_text(encoding='utf-8'))['source_files_sha256']}
    (out/'expanded-summary.json').write_text(json.dumps(dict(qt=qVersion(),platform=app.platformName(),source_files_sha256=hashes,scenes=scenes,callback_errors=errors,checks=['DIRECT expanded LHV/FCh proxies visible and disabled; raw combos hidden','visible controls inside parents','resize retains complete form_state','zero Records']),ensure_ascii=False,indent=2),encoding='utf-8')
    window.hide();window.deleteLater();pump()
print('PASS: expanded actual DIRECT controls and boundaries, wide/narrow, zero Records.')
