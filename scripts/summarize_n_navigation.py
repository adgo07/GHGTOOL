"""Deterministic raw-data comparison; no Qt/test process is started."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/performance/n-navigation'
def read(name): return json.loads((OUT/name).read_bytes())
def stats(values):
    values=sorted(values)
    return {'n':len(values),'median_ns':statistics.median(values),'p95_nearest_rank_ns':values[math.ceil(.95*len(values))-1], 'min_ns':min(values),'max_ns':max(values)} if values else {'n':0}
def groups(raw):
    result=defaultdict(list)
    for worker in raw['workers']:
        for sample in worker['samples']:
            assert sample['correct_page'] and sample['total_ns']==sample['navigate_ns']+sample['event_pump_ns']
            result[(sample['kind'],sample['route'])].append(sample)
    assert not raw['failures'] and len(raw['workers'])==3
    return result
before,after=read('before.json'),read('after.json')
assert before['script_sha256']==after['script_sha256']
bg,ag=groups(before),groups(after)
assert bg.keys()==ag.keys()
result={'before_head':before['head'],'after_head':after['head'],
        'worker_script_sha256':before['script_sha256'], 'groups':[],
        'raw_file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name not in ('COMPARISON.json','VALIDATION.json')},
        'seed_database_sha256':after['seed_database_sha256']}
query_mismatches=[]
for key in bg:
    left,right=bg[key],ag[key]
    assert len(left)==len(right)==(3 if key[0]=='first_use' else 30)
    bs,ass=stats([s['total_ns'] for s in left]),stats([s['total_ns'] for s in right])
    result['groups'].append({'kind':key[0],'route':key[1],'before':bs,'after':ass,
        'median_reduction_percent':100*(1-ass['median_ns']/bs['median_ns']),
        'before_parts_median_ns':{k:statistics.median(s['parts_ns'].get(k,0) for s in left) for k in sorted({k for s in left for k in s['parts_ns']})},
        'after_parts_median_ns':{k:statistics.median(s['parts_ns'].get(k,0) for s in right) for k in sorted({k for s in right for k in s['parts_ns']})},
        'paint_before':stats([s['first_paint_ns'] for s in left if s['first_paint_ns'] is not None]),
        'paint_after':stats([s['first_paint_ns'] for s in right if s['first_paint_ns'] is not None])})
    for i,(a,b) in enumerate(zip(left,right)):
        for name in set(a['calls'])|set(b['calls']):
            if 'query' in name and a['calls'].get(name,0)!=b['calls'].get(name,0):
                query_mismatches.append([*key,i,name,a['calls'].get(name,0),b['calls'].get(name,0)])
result['query_call_mismatches']=query_mismatches
assert not query_mismatches,query_mismatches
(OUT/'COMPARISON.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
lines=['| 路线 | 改前 median / p95 ms | 改后 median / p95 ms | median 降幅 |','|---|---:|---:|---:|']
for row in result['groups']:
    if row['kind']!='steady_home_reset':continue
    b,a=row['before'],row['after']
    lines.append(f"| {row['route']} | {b['median_ns']/1e6:.3f} / {b['p95_nearest_rank_ns']/1e6:.3f} | {a['median_ns']/1e6:.3f} / {a['p95_nearest_rank_ns']/1e6:.3f} | {row['median_reduction_percent']:.1f}% |")
print('\n'.join(lines))
for row in result['groups']:
    if row['kind']!='steady_home_reset': print(row['kind'],row['route'],row['before']['median_ns']/1e6,row['after']['median_ns']/1e6)
