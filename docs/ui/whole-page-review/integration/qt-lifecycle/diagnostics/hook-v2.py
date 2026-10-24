"""Minimal C-level faulthandler timer; no Python sampling thread in child."""
import os
import sys
if sys.argv and sys.argv[0].replace(chr(92),'/').endswith('/uir04_scale_acceptance.py') and os.environ.get('QZ_SCALE_PROBE_OUT'):
    import atexit
    import faulthandler
    from pathlib import Path
    output=Path(os.environ['QZ_SCALE_PROBE_OUT']);output.mkdir(parents=True,exist_ok=True)
    fault_file=(output/('child-'+str(os.getpid())+'.fault.log')).open('w',encoding='utf-8')
    faulthandler.enable(file=fault_file)
    faulthandler.dump_traceback_later(10,repeat=True,file=fault_file)
    atexit.register(faulthandler.cancel_dump_traceback_later)
