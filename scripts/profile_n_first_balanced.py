"""ABBA fresh-process mechanism control, separate from sequential production samples."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.profile_n_first_open import worker
from scripts.profile_n_navigation import environment,git,write

def control_worker(folder,strategy):
    import packages.ui.shell as shell_module
    from packages.ui.view_models import AppRoute
    from PySide6.QtCore import QObject,QEvent
    original_create=shell_module.create_page
    original_add=shell_module.CurrentPageStack.addWidget
    mechanism={'add_widget_ns':[],'parent_changes':0,'style_changes':0,'constructor_parent_class':None,'final_parent_class':None}
    probes=[]
    class Probe(QObject):
        def eventFilter(self,watched,event):
            if event.type()==QEvent.Type.ParentChange:mechanism['parent_changes']+=1
            if event.type()==QEvent.Type.StyleChange:mechanism['style_changes']+=1
            return False
    def create(route,model,navigate,parent=None,**kwargs):
        if route is AppRoute.NEW_ACCOUNTING:
            owner=parent
            while owner is not None and not isinstance(owner,shell_module.AppShell):owner=owner.parentWidget()
            assert owner is not None
            parent=owner if strategy=='legacy_parent' else owner.page_stack
        page=original_create(route,model,navigate,parent,**kwargs)
        if route is AppRoute.NEW_ACCOUNTING:
            mechanism['constructor_parent_class']=type(page.parentWidget()).__name__
            probe=Probe(page);page.installEventFilter(probe);probes.append(probe)
        return page
    def add(self,page):
        if page.objectName()!='page_new_accounting':return original_add(self,page)
        started=time.perf_counter_ns()
        result=original_add(self,page)
        mechanism['add_widget_ns'].append(time.perf_counter_ns()-started)
        mechanism['final_parent_class']=type(page.parentWidget()).__name__
        return result
    shell_module.create_page=create;shell_module.CurrentPageStack.addWidget=add
    result=worker(folder);result['mechanism']=mechanism;return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--strategy',choices=('legacy_parent','final_parent'));parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    folder=ROOT/'tmp/n-first-open'/args.run
    if args.worker:write(folder/'worker.json',control_worker(folder,args.strategy));return
    assert not folder.exists();folder.mkdir(parents=True)
    seed=ROOT/'tmp/n-first-open/seed';names=('catalog.sqlite','records.sqlite','projects.sqlite')
    data={'kind':'ABBA mechanism control, not pooled with sequential production samples','head':git('rev-parse','HEAD'),
          'worker_script_sha256':hashlib.sha256((ROOT/'scripts/profile_n_first_open.py').read_bytes()).hexdigest(),
          'control_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'seed_sha256':{n:hashlib.sha256((seed/n).read_bytes()).hexdigest() for n in names},
          'environment_before':environment(),'workers':[],'failures':[]}
    for pair in range(20):
        order=('legacy_parent','final_parent') if pair%2==0 else ('final_parent','legacy_parent')
        for order_index,strategy in enumerate(order):
            name=f'pair-{pair:02d}-{order_index}-{strategy}';session=folder/name;session.mkdir()
            for n in names:shutil.copy2(seed/n,session/n)
            process=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker','--run',args.run+'/'+name,'--strategy',strategy],cwd=ROOT,capture_output=True,timeout=180)
            if process.returncode:data['failures'].append({'pair':pair,'strategy':strategy,'exit':process.returncode,'stderr':process.stderr.decode('utf-8',errors='replace')})
            else:
                item=json.loads((session/'worker.json').read_bytes());item.update({'pair':pair,'order_index':order_index,'strategy':strategy});data['workers'].append(item)
            write(folder/'raw.json',data)
        print(f'pair {pair+1}/20; failures={len(data["failures"])}',flush=True)
    data['environment_after']=environment();write(folder/'raw.json',data);assert not data['failures']
if __name__=='__main__':main()
