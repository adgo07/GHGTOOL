"""Repeat the unchanged navigation worker using byte-identical databases from a prior run."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.profile_n_navigation import write, git, environment
name=sys.argv[1]
source=ROOT/'tmp/n-navigation/before-01/seed'
folder=ROOT/'tmp/n-navigation'/name
assert not folder.exists()
folder.mkdir(parents=True)
seed=folder/'seed';shutil.copytree(source,seed)
production=hashlib.sha256()
for path in git('ls-files','apps','packages','resources','pyproject.toml','platform-lock.json').splitlines():
    production.update(path.encode());production.update((ROOT/path).read_bytes())
script=ROOT/'scripts/profile_n_navigation.py'
data={'schema':1,'base':'e186b5116f16861bc65fbb939abec750a39d7f0e','head':git('rev-parse','HEAD'),
      'production_sha256':production.hexdigest(),'production_diff':git('diff','e186b5116f16861bc65fbb939abec750a39d7f0e','--','apps','packages'),
      'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
      'seed_copy_orchestrator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'environment_before':environment(),'data':{'synthetic_records':200,'projects':20,'viewport':'1280x800','platform':'offscreen'},
      'seed_database_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in seed.glob('*.sqlite')},
      'seed_source':'before-01/seed; byte-identical copies','workers':[],'failures':[]}
for i in range(3):
    session=folder/f'worker-{i}';shutil.copytree(seed,session)
    started=time.perf_counter_ns()
    process=subprocess.run([sys.executable,'-B',str(script),'--worker','--run',f'{name}/worker-{i}','--repeats','10'],cwd=ROOT,capture_output=True,timeout=900)
    if process.returncode:
        data['failures'].append({'worker':i,'exit':process.returncode,'stderr':process.stderr.decode('utf-8',errors='replace')})
    else:
        import json
        item=json.loads((session/'worker.json').read_bytes());item['process_total_ns']=time.perf_counter_ns()-started;data['workers'].append(item)
    write(folder/'raw.json',data)
    print(f'worker {i+1}/3 complete; failures={len(data["failures"])}',flush=True)
data['environment_after']=environment();write(folder/'raw.json',data)
assert not data['failures']
