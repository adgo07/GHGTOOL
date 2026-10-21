"""Runtime-only candidates; diagnostic results are never primary samples."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.profile_n_first_open import worker,write,git
import packages.ui.shell as shell_module
from packages.ui.view_models import AppRoute
from packages.ui.carbon_material_page import CarbonMaterialAccountingPage as Page
variant=sys.argv[1];run=sys.argv[2]
assert variant in ('parent_stack','early_style','both')
if variant in ('parent_stack','both'):
    original_create=shell_module.create_page
    def create(route,view_model,navigate,parent=None,**kwargs):
        if route is AppRoute.NEW_ACCOUNTING and isinstance(parent,shell_module.AppShell):parent=parent.page_stack
        return original_create(route,view_model,navigate,parent,**kwargs)
    shell_module.create_page=create
if variant in ('early_style','both'):
    original_build=Page._build_page;original_style=Page._apply_accounting_style
    def build(self):
        original_style(self);self._n_early_style=True
        return original_build(self)
    def style(self):
        if not getattr(self,'_n_early_style',False):original_style(self)
    Page._build_page=build;Page._apply_accounting_style=style
folder=ROOT/'tmp/n-first-open'/run;assert not folder.exists();folder.mkdir(parents=True)
for name in ('catalog.sqlite','records.sqlite','projects.sqlite'):shutil.copy2(ROOT/'tmp/n-first-open/seed'/name,folder/name)
result=worker(folder);result.update({'diagnostic_variant':variant,'head':git('rev-parse','HEAD'),'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
write(folder/'raw.json',result)
for sample in result['samples']:print(variant,sample['kind'],round(sample['total_ns']/1e6,3),flush=True)
