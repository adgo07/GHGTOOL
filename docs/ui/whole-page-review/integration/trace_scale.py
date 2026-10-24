import json, os, subprocess, sys, time
from pathlib import Path
root=Path.cwd();out=root/'build/ui-v2-integration'
child="""import faulthandler,runpy,sys,time
faulthandler.enable()
faulthandler.dump_traceback_later(10,repeat=True)
started=time.monotonic();cpu=time.process_time()
sys.argv=['scripts/uir04_scale_acceptance.py','--scale','1.0']
try:
 runpy.run_path('scripts/uir04_scale_acceptance.py',run_name='__main__')
finally:
 print('TRACE_TIMING',time.monotonic()-started,time.process_time()-cpu,flush=True)
 faulthandler.cancel_dump_traceback_later()
"""
env=os.environ.copy();env.update(QT_QPA_PLATFORM='offscreen',QT_AUTO_SCREEN_SCALE_FACTOR='0',QT_SCALE_FACTOR='1.0')
started=time.monotonic()
try:
 run=subprocess.run([sys.executable,'-B','-c',child],cwd=root,env=env,capture_output=True,timeout=60)
 code,stdout,stderr=run.returncode,run.stdout,run.stderr
except subprocess.TimeoutExpired as error:
 code,stdout,stderr='TIMEOUT',error.stdout or b'',error.stderr or b''
(out/'scale-trace.stdout.log').write_bytes(stdout)
(out/'scale-trace.stderr.log').write_bytes(stderr)
meta=dict(command=[sys.executable,'-B','-c','faulthandler enabled runpy original scale script 1.0'],timeout_seconds=60,elapsed_seconds=time.monotonic()-started,returncode=code,note='Diagnostic instrumentation only; no timeout/script/production changes; not the unchanged wrapper result.')
(out/'scale-trace.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta),flush=True)
sys.exit(0 if code==0 else 1)
