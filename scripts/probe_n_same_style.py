"""Diagnostic only: same-QSS guard applied at runtime without production edits."""
from pathlib import Path
import hashlib
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.profile_n_navigation import worker, write, git
from packages.ui.shell import AppShell
original_build = AppShell._build_main_content
def build(self):
    result = original_build(self)
    original_set = self.scroll_host.setStyleSheet
    def set_if_changed(style):
        if style != self.scroll_host.styleSheet(): original_set(style)
    self.scroll_host.setStyleSheet = set_if_changed
    return result
AppShell._build_main_content = build
folder = ROOT/'tmp/n-navigation/guard-01'
assert not folder.exists()
folder.mkdir(parents=True)
import shutil
for name in ('records.sqlite','projects.sqlite','catalog.sqlite'):
    shutil.copy2(ROOT/'tmp/n-navigation/before-01/seed'/name, folder/name)
result = worker(folder,1)
result['kind'] = 'diagnostic-runtime-same-stylesheet-guard'
result['head'] = git('rev-parse','HEAD')
result['probe_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
write(folder/'raw.json', result)
for sample in result['samples']:
    print(sample['kind'],sample['route'],round(sample['total_ns']/1e6,3),round(sample['parts_ns'].get('ancestor_stylesheet',0)/1e6,3),flush=True)
