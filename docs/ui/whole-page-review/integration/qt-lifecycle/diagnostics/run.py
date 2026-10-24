"""Run real prefix tests plus the unchanged scale test in one parent process."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import threading
import unittest

root=Path.cwd();sys.path.insert(0,str(root))
parser=argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('--modules',nargs='*',default=[])
args=parser.parse_args()
out=root/'build/ui-v2-integration/context-probe'/args.name
out.mkdir(exist_ok=False)
events=out/'events.jsonl'
started=time.monotonic()

class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('page_total',ctypes.c_ulonglong),('page_available',ctypes.c_ulonglong),('virtual_total',ctypes.c_ulonglong),('virtual_available',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
class ProcessMemory(ctypes.Structure):
    _fields_=[('size',ctypes.c_ulong),('faults',ctypes.c_ulong),('peak_working',ctypes.c_size_t),('working',ctypes.c_size_t),('peak_paged',ctypes.c_size_t),('paged',ctypes.c_size_t),('peak_nonpaged',ctypes.c_size_t),('nonpaged',ctypes.c_size_t),('pagefile',ctypes.c_size_t),('peak_pagefile',ctypes.c_size_t),('private',ctypes.c_size_t)]

ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
ctypes.windll.kernel32.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(Memory)]
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessMemory),ctypes.c_ulong]

def process_memory(handle):
    process=ProcessMemory();process.size=ctypes.sizeof(process)
    success=ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(process),process.size)
    return dict(memory_read_ok=bool(success),private_mb=process.private/1048576 if success else None,working_mb=process.working/1048576 if success else None,page_faults=process.faults if success else None)

def resource():
    memory=Memory();memory.length=ctypes.sizeof(memory)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    result=dict(physical_total_mb=memory.total/1048576,physical_available_mb=memory.available/1048576,memory_load=memory.load,cpu=time.process_time(),**process_memory(ctypes.windll.kernel32.GetCurrentProcess()))
    if 'PySide6.QtWidgets' in sys.modules:
        from PySide6.QtWidgets import QApplication
        app=QApplication.instance()
        if app:
            widgets=app.topLevelWidgets()
            result.update(top_levels=len(widgets),visible_top_levels=sum(w.isVisible() for w in widgets),main_windows=sum(w.metaObject().className()=='CarbonAccountingMainWindow' for w in widgets))
    return result

def event(kind,**values):
    data=dict(kind=kind,elapsed=time.monotonic()-started,**values,resources=resource())
    with events.open('a',encoding='utf-8') as file:file.write(json.dumps(data,ensure_ascii=False)+'\n')

def flatten(suite):
    for value in suite:
        if isinstance(value,unittest.TestSuite):yield from flatten(value)
        else:yield value

# Full normal discovery imports, then a declared prefix segment for diagnosis.
all_tests=list(flatten(unittest.defaultTestLoader.discover('tests',top_level_dir='.')))
target='tests.test_uir04_finalization.UIR04FinalizationTests.test_common_windows_scale_factors_keep_controls_visible'
selected=[test for test in all_tests if type(test).__module__ in args.modules or (type(test).__module__=='tests.test_uir04_finalization' and test.id()<=target)]
assert any(test.id()==target for test in selected)
(out/'selection.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),test_ids=[test.id() for test in selected],timeout_unchanged=60,note='Diagnostic prefix subset; not full regression evidence. Original scale data/assertions unchanged; sitecustomize samples child stacks/resources only.',page_sha256=hashlib.sha256((root/'packages/ui/carbon_material_page.py').read_bytes()).hexdigest()),indent=2),encoding='utf-8')

original_run=subprocess.run
original_popen=subprocess.Popen
monitors=[]
def observed_popen(command,*a,**kw):
    process=original_popen(command,*a,**kw)
    if isinstance(command,list) and any(str(value).replace('\\','/').endswith('/uir04_scale_acceptance.py') for value in command):
        stop=threading.Event()
        def sample():
            while not stop.is_set():
                # Win32 counters only; no Qt calls from the monitoring thread.
                mem=Memory();mem.length=ctypes.sizeof(mem)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
                data=dict(elapsed=time.monotonic()-started,pid=process.pid,physical_available_mb=mem.available/1048576,system_load=mem.load,**process_memory(int(process._handle)))
                with (out/('child-'+str(process.pid)+'.resources.jsonl')).open('a',encoding='utf-8') as file:file.write(json.dumps(data)+'\n')
                stop.wait(5)
        thread=threading.Thread(target=sample,daemon=True);thread.start()
        monitors.append((stop,thread))
    return process
subprocess.Popen=observed_popen
def observed_run(command,*a,**kw):
    if isinstance(command,list) and any(str(value).replace('\\','/').endswith('/uir04_scale_acceptance.py') for value in command):
        child_env=kw['env'].copy()
        child_env['PYTHONPATH']=str(root/'build/ui-v2-integration/context-probe/hook')+os.pathsep+child_env.get('PYTHONPATH','')
        child_env['QZ_SCALE_PROBE_OUT']=str(out)
        kw['env']=child_env
        event('child_start',command=command,timeout=kw.get('timeout'))
        tick=time.monotonic()
        try:
            try:
                run=original_run(command,*a,**kw)
            except subprocess.TimeoutExpired as error:
                event('child_timeout',command=command,seconds=time.monotonic()-tick)
                for suffix,value in (('stdout',error.stdout),('stderr',error.stderr)):
                    if value is not None:(out/('timeout.'+suffix+'.log')).write_bytes(value.encode() if isinstance(value,str) else value)
                raise
        finally:
            for stop,thread in monitors:stop.set();thread.join(timeout=1)
            monitors.clear()
        event('child_done',command=command,seconds=time.monotonic()-tick,returncode=run.returncode)
        return run
    return original_run(command,*a,**kw)
subprocess.run=observed_run

class Result(unittest.TextTestResult):
    def startTest(self,test):
        event('test_start',test=test.id());super().startTest(test)
    def stopTest(self,test):
        super().stopTest(test);event('test_stop',test=test.id())

event('suite_start',count=len(selected))
with (out/'tests.log').open('w',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(unittest.TestSuite(selected))
event('suite_done',count=result.testsRun,failures=len(result.failures),errors=len(result.errors))
print(json.dumps(dict(count=result.testsRun,failures=len(result.failures),errors=len(result.errors))),flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
