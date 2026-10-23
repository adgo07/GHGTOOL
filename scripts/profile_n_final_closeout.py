"""One bounded final-parent candidate; independent ABBA processes, no business caches."""
from __future__ import annotations
import argparse,ast,hashlib,json,shutil,subprocess,sys,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.profile_n_first_open import worker
from scripts.profile_n_navigation import environment,git,write
BASE='59cab091aab0df44b147f2bba3b960085dbae168'
CHANGES={
 '_build_source_cards':('card = SourceCard(source_id, SOURCE_LABELS[source_id], self)','card = SourceCard(source_id, SOURCE_LABELS[source_id], parent_layout.parentWidget())'),
 '_build_unified_energy_section':('card = QFrame(self)','card = QFrame(parent_layout.parentWidget())'),
 '_add_unified_energy_row':('row = _UnifiedEnergyRow(self._energy_row_serial, family, self._remove_unified_energy_row, self)','row = _UnifiedEnergyRow(self._energy_row_serial, family, self._remove_unified_energy_row, rows_layout.parentWidget())'),
 '_add_process_row':('host = QWidget(self)','host = QWidget(self._process_rows_layout[prefix].parentWidget())'),
}
def install(strategy):
 import packages.ui.carbon_material_page as module
 source=subprocess.check_output(['git','show',BASE+':packages/ui/carbon_material_page.py'],cwd=ROOT).decode('utf-8')
 tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CarbonMaterialAccountingPage')
 hashes={}
 for name,(old,new) in CHANGES.items():
  node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
  method=textwrap.dedent('\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]))
  assert method.count(old)==1,(name,method.count(old))
  if strategy=='final_parent':method=method.replace(old,new)
  namespace=dict(vars(module));exec(compile('from __future__ import annotations\n'+method,'<n-final-'+name+'>','exec'),namespace)
  setattr(module.CarbonMaterialAccountingPage,name,namespace[name]);hashes[name]=hashlib.sha256(method.encode()).hexdigest()
 return hashes

def production_hash():
 digest=hashlib.sha256()
 for name in git('ls-files','apps','packages','resources','pyproject.toml','platform-lock.json').splitlines():digest.update(name.encode());digest.update((ROOT/name).read_bytes())
 return digest.hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--pairs',type=int,default=2);parser.add_argument('--strategy',choices=('legacy_parent','final_parent'));parser.add_argument('--worker',action='store_true');a=parser.parse_args()
 folder=ROOT/'tmp/n-final-closeout'/a.run
 if a.worker:
  hashes=install(a.strategy);result=worker(folder);result['candidate_method_sha256']=hashes;write(folder/'worker.json',result);return
 assert not folder.exists(),'Never overwrite evidence';folder.mkdir(parents=True)
 seed=ROOT/'tmp/n-first-open/seed';names=('catalog.sqlite','records.sqlite','projects.sqlite')
 result={'kind':'independent bounded-candidate ABBA control','base':BASE,'head':git('rev-parse','HEAD'),'pairs':a.pairs,'changes':CHANGES,'production_diff':git('diff',BASE,'--','apps','packages'),'production_sha256':production_hash(),'worker_script_sha256':hashlib.sha256((ROOT/'scripts/profile_n_first_open.py').read_bytes()).hexdigest(),'control_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seed_sha256':{n:hashlib.sha256((seed/n).read_bytes()).hexdigest() for n in names},'environment_before':environment(),'workers':[],'failures':[]}
 for pair in range(a.pairs):
  order=('legacy_parent','final_parent') if pair%2==0 else ('final_parent','legacy_parent')
  for index,strategy in enumerate(order):
   name=f'pair-{pair:02d}-{index}-{strategy}';session=folder/name;session.mkdir()
   for n in names:shutil.copy2(seed/n,session/n)
   p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--run',a.run+'/'+name,'--worker','--strategy',strategy],cwd=ROOT,capture_output=True,timeout=180)
   (session/'stdout.txt').write_bytes(p.stdout);(session/'stderr.txt').write_bytes(p.stderr)
   if p.returncode:result['failures'].append({'pair':pair,'strategy':strategy,'exit':p.returncode,'stderr':p.stderr.decode('utf-8',errors='replace')})
   else:
    item=json.loads((session/'worker.json').read_bytes());item.update(pair=pair,order_index=index,strategy=strategy);result['workers'].append(item)
   write(folder/'raw.json',result)
  print(f'pair {pair+1}/{a.pairs}; failures={len(result["failures"])}',flush=True)
 result['environment_after']=environment();assert result['seed_sha256']=={n:hashlib.sha256((seed/n).read_bytes()).hexdigest() for n in names};write(folder/'raw.json',result);assert not result['failures']
if __name__=='__main__':main()
