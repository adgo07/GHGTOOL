"""Read-only resource/stack sampling for the original scale child only."""
import os
import sys

if sys.argv and sys.argv[0].replace('\\', '/').endswith('/uir04_scale_acceptance.py') and os.environ.get('QZ_SCALE_PROBE_OUT'):
    import ctypes
    import faulthandler
    import json
    from pathlib import Path
    import threading
    import time
    import traceback

    output = Path(os.environ['QZ_SCALE_PROBE_OUT'])
    output.mkdir(parents=True, exist_ok=True)
    stem = 'child-' + str(os.getpid())
    fault_file = (output/(stem+'.fault.log')).open('w', encoding='utf-8')
    faulthandler.enable(file=fault_file)
    faulthandler.dump_traceback_later(10, repeat=True, file=fault_file)
    main_ident = threading.main_thread().ident
    started = time.monotonic()

    class Memory(ctypes.Structure):
        _fields_ = [('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('page_total',ctypes.c_ulonglong),('page_available',ctypes.c_ulonglong),('virtual_total',ctypes.c_ulonglong),('virtual_available',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]

    def sample():
        while True:
            mem=Memory();mem.length=ctypes.sizeof(mem)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            frame=sys._current_frames().get(main_ident)
            data=dict(elapsed=time.monotonic()-started,cpu=time.process_time(),physical_total_mb=mem.total/1048576,physical_available_mb=mem.available/1048576,system_memory_load=mem.load,
                      stack=traceback.format_stack(frame) if frame else [])
            with (output/(stem+'.samples.jsonl')).open('a',encoding='utf-8') as file:
                file.write(json.dumps(data,ensure_ascii=False)+'\n')
            time.sleep(5)

    threading.Thread(target=sample,daemon=True).start()
