import datetime, hashlib, json, os, subprocess, sys, time
from pathlib import Path

root = Path.cwd()
out = root/'build/ui-v2-integration'
paths = subprocess.check_output(['git','ls-files','-z'], cwd=root).decode().split('\0')
paths = [path for path in paths if path and (path.endswith('.py') or path.startswith('resources/') or path in ('pyproject.toml','requirements-build.txt','platform-lock.json')) and (root/path).is_file()]
def identity():
    return {path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in paths}
before = identity()
meta = dict(command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-t','.','-v'],
    parent_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_test_resource_sha256=before, note='Uncommitted final candidate identified by actual file hashes; documentation excluded from freeze.')
(out/'final-discover-identity.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2),encoding='utf-8')
start = time.monotonic()
with (out/'final-full-tests.log').open('wb') as log:
    run = subprocess.run(meta['command'],cwd=root,env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
after = identity()
meta.update(returncode=run.returncode,elapsed_seconds=time.monotonic()-start,
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    changed_during_run=[path for path in paths if before[path]!=after[path]],
    log_sha256=hashlib.sha256((out/'final-full-tests.log').read_bytes()).hexdigest())
(out/'final-discover-identity.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:meta[key] for key in ('returncode','elapsed_seconds','changed_during_run','log_sha256')}),flush=True)
sys.exit(run.returncode if not meta['changed_during_run'] else 2)
