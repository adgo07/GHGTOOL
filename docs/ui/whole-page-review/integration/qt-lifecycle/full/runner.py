"""Plain full unittest CLI with file identity and external memory observations."""
import ctypes,datetime,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
root=Path.cwd();out=root/'build/ui-v2-integration/final-after-lifecycle'
out.mkdir(exist_ok=False)
paths=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
paths=[p for p in paths if p and (p.endswith('.py') or p.startswith('resources/') or p in ('pyproject.toml','requirements-build.txt','platform-lock.json')) and (root/p).is_file()]
def identity():return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
before=identity()
meta=dict(command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-t','.','-v'],parent_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_test_resource_sha256=before,note='Unmodified unittest CLI and test subprocesses. Only this external parent observes process/system memory. Documentation excluded from code freeze.')
(out/'identity.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('page_total',ctypes.c_ulonglong),('page_available',ctypes.c_ulonglong),('virtual_total',ctypes.c_ulonglong),('virtual_available',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
class ProcessMemory(ctypes.Structure):
    _fields_=[('size',ctypes.c_ulong),('faults',ctypes.c_ulong),('peak_working',ctypes.c_size_t),('working',ctypes.c_size_t),('peak_paged',ctypes.c_size_t),('paged',ctypes.c_size_t),('peak_nonpaged',ctypes.c_size_t),('nonpaged',ctypes.c_size_t),('pagefile',ctypes.c_size_t),('peak_pagefile',ctypes.c_size_t),('private',ctypes.c_size_t)]
ctypes.windll.kernel32.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(Memory)]
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessMemory),ctypes.c_ulong]
tick=time.monotonic()
with (out/'full-tests.log').open('xb') as log:
    child=subprocess.Popen(meta['command'],cwd=root,env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
    with (out/'resources.jsonl').open('x',encoding='utf-8') as observations:
        while child.poll() is None:
            mem=Memory();mem.length=ctypes.sizeof(mem)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            proc=ProcessMemory();proc.size=ctypes.sizeof(proc)
            ok=ctypes.windll.psapi.GetProcessMemoryInfo(int(child._handle),ctypes.byref(proc),proc.size)
            observations.write(json.dumps(dict(elapsed=time.monotonic()-tick,pid=child.pid,physical_available_mb=mem.available/1048576,system_memory_load=mem.load,memory_read_ok=bool(ok),private_mb=proc.private/1048576 if ok else None,working_mb=proc.working/1048576 if ok else None,page_faults=proc.faults if ok else None))+'\n');observations.flush()
            time.sleep(10)
after=identity();raw=(out/'full-tests.log').read_bytes();text=raw.decode('utf-8','replace')
counts=re.findall(r'Ran (\d+) tests in ([0-9.]+)s',text)
qt_errors=re.findall(r'^.*(?:RuntimeError|TypeError):.*Internal C\+\+ object.*already deleted.*$',text,re.M)
meta.update(returncode=child.returncode,elapsed_seconds=time.monotonic()-tick,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),changed_during_run=[p for p in paths if before[p]!=after[p]],log_sha256=hashlib.sha256(raw).hexdigest(),test_summary=counts[-1] if counts else None,unhandled_deleted_qt_object_errors=qt_errors)
(out/'identity.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:meta[key] for key in ('returncode','elapsed_seconds','changed_during_run','test_summary','unhandled_deleted_qt_object_errors','log_sha256')}),flush=True)
exit_code=child.returncode
if meta['changed_during_run'] or qt_errors or not counts or counts[-1][0]!='1074':exit_code=exit_code or 3
sys.exit(exit_code)
