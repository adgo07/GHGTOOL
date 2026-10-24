import json,os,pstats,subprocess,sys,time
from pathlib import Path
root=Path.cwd();out=root/'build/ui-v2-integration/context-probe'
name=sys.argv[1]
profile=out/(name+'.prof')
code="""import cProfile,runpy,sys
p=cProfile.Profile();sys.argv=['scripts/uir04_scale_acceptance.py','--scale','1.0']
counter=0
def checkpoint(frame,event,arg):
 global counter
 if frame.f_code.co_filename.replace(chr(92),'/').endswith('uir04_scale_acceptance.py'):
  if event=='line' and frame.f_lineno in (55,62,86,91,92,93,94,95,96,100,103,139,153):
   counter+=1;p.dump_stats(PROFILE_PREFIX+'-part-'+str(counter).zfill(3)+'.prof')
  return checkpoint
 return None
sys.settrace(checkpoint);p.enable()
try:runpy.run_path('scripts/uir04_scale_acceptance.py',run_name='__main__')
finally:sys.settrace(None);p.disable();p.dump_stats(sys.argv_profile)
""".replace('sys.argv_profile',repr(str(profile))).replace('PROFILE_PREFIX',repr(str(out/name)))
env=os.environ.copy();env.update(QT_QPA_PLATFORM='offscreen',QT_AUTO_SCREEN_SCALE_FACTOR='0',QT_SCALE_FACTOR='1.0')
tick=time.monotonic()
try:
    run=subprocess.run([sys.executable,'-B','-c',code],cwd=root,env=env,capture_output=True,timeout=60)
    code,stdout,stderr=run.returncode,run.stdout,run.stderr
except subprocess.TimeoutExpired as error:
    code,stdout,stderr='TIMEOUT',error.stdout or b'',error.stderr or b''
(out/(name+'.stdout.log')).write_bytes(stdout)
(out/(name+'.stderr.log')).write_bytes(stderr)
partials=sorted(out.glob(name+'-part-*.prof'))
chosen=profile if profile.exists() else (partials[-1] if partials else None)
print(json.dumps(dict(returncode=code,seconds=time.monotonic()-tick,profile_exists=profile.exists(),partial_profiles=len(partials))),flush=True)
if chosen:
    with (out/(name+'.stats.log')).open('w',encoding='utf-8') as file:
        pstats.Stats(str(chosen),stream=file).sort_stats('cumulative').print_stats(45)
