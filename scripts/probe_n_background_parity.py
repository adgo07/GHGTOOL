"""Same-state offscreen parity against legacy ancestor QSS, using real production pages."""
from pathlib import Path
import hashlib
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.profile_n_navigation import write, git
from scripts.measure_n_baseline import compose
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from packages.ui.design_tokens import HOME_CANVAS_GRADIENT, PAGE_BACKGROUND
from packages.ui.view_models import AppRoute
folder=ROOT/'tmp/n-navigation/production-parity-01'
assert not folder.exists()
folder.mkdir(parents=True)
for name in ('records.sqlite','projects.sqlite','catalog.sqlite'):
    shutil.copy2(ROOT/'tmp/n-navigation/before-01/seed'/name,folder/name)
app,window,records,projects=compose(folder)
app.setCursorFlashTime(0)
shell=window.centralWidget();window.show()
def settle():
    for _ in range(4): app.processEvents()
settle()
host=shell.scroll_host;canvas=host.background_layer
# Original host was plain QWidget; enable its QSS painting on this QWidget subclass.
host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
proof={'head':git('rev-parse','HEAD'),'production_diff':git('diff','--','packages/ui/shell.py'),
       'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'scope':'offscreen/same-state; actual full-catalog production pages; not native DPI acceptance', 'cases':[]}
for width,height in ((1180,720),(1600,900)):
    window.resize(width,height);settle()
    for route in AppRoute:
        shell.navigate(route);settle()
        background=HOME_CANVAS_GRADIENT if route is AppRoute.HOME else PAGE_BACKGROUND
        positions=(False,True) if route is AppRoute.NEW_ACCOUNTING else (False,)
        for bottom in positions:
            bar=shell.main_scroll_area.verticalScrollBar();bar.setValue(bar.maximum() if bottom else bar.minimum());settle()
            canvas.hide();host.setStyleSheet(f'QWidget#scrollHost {{ background: {background}; }}');settle()
            legacy=shell.main_scroll_area.viewport().grab().toImage()
            host.setStyleSheet('');canvas.show();host.set_background(background);settle()
            isolated=shell.main_scroll_area.viewport().grab().toImage()
            same=legacy==isolated
            proof['cases'].append({'viewport':[width,height],'route':route.value,'bottom':bottom,'pixels_equal':same,
                'legacy_sha256':hashlib.sha256(bytes(legacy.constBits())).hexdigest(),
                'isolated_sha256':hashlib.sha256(bytes(isolated.constBits())).hexdigest(),
                'canvas_matches_host':canvas.geometry()==host.rect()})
            if not same:
                legacy.save(str(folder/f'{width}-{route.value}-{bottom}-legacy.png'))
                isolated.save(str(folder/f'{width}-{route.value}-{bottom}-isolated.png'))
            print(width,route.value,bottom,same,flush=True)
write(folder/'proof.json',proof)
window.hide()
assert all(c['pixels_equal'] and c['canvas_matches_host'] for c in proof['cases'])
