"""Main-thread-only progress tracing for the original scale script."""
import os
import sys
if sys.argv and sys.argv[0].replace(chr(92),'/').endswith('/uir04_scale_acceptance.py') and os.environ.get('QZ_SCALE_PROBE_OUT'):
    import atexit
    import faulthandler
    import json
    from pathlib import Path
    import time
    import traceback
    output=Path(os.environ['QZ_SCALE_PROBE_OUT']);output.mkdir(parents=True,exist_ok=True)
    stem='child-'+str(os.getpid())
    fault_file=(output/(stem+'.fault.log')).open('w',encoding='utf-8')
    faulthandler.enable(file=fault_file)
    progress=(output/(stem+'.progress.jsonl')).open('w',encoding='utf-8')
    started=time.monotonic();last_stack=started
    target=os.path.abspath(sys.argv[0])
    def trace(frame,event,arg):
        global last_stack
        tick=time.monotonic()
        if event=='call' and tick-last_stack>=5:
            last_stack=tick
            progress.write(json.dumps(dict(elapsed=tick-started,kind='stack',stack=traceback.format_stack(frame)),ensure_ascii=False)+'\n');progress.flush()
        if frame.f_code.co_filename==target:
            if event=='line':
                progress.write(json.dumps(dict(elapsed=tick-started,kind='line',line=frame.f_lineno))+'\n');progress.flush()
            return trace
        return None
    sys.settrace(trace)
    atexit.register(lambda:sys.settrace(None))
