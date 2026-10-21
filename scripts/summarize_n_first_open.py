"""Recompute sequential results and separate ABBA mechanism controls from retained JSON."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math,statistics
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/performance/n-first-open'
def read(name):return json.loads((OUT/name).read_bytes())
def stats(values):
    values=sorted(values)
    return {'n':len(values),'median_ns':statistics.median(values),'p95_nearest_rank_ns':values[math.ceil(.95*len(values))-1],'min_ns':min(values),'max_ns':max(values)} if values else {'n':0}
def samples(data,kind):return [s for w in data['workers'] for s in w['samples'] if s['kind']==kind]
def query_calls(s):return {k:v['calls'] for k,v in s['parts'].items() if k.startswith(('resolver.','catalog_','records.','projects.'))}
def check_worker(w):
    assert not w['qt_callback_errors']
    for s in w['samples']:assert s['correct_page'] and s['total_ns']==s['navigate_ns']+s['event_pump_ns']
def group(data,kind):
    ss=samples(data,kind)
    keys=sorted({key for s in ss for key in s['parts']})
    return {'total':stats([s['total_ns'] for s in ss]),'paint':stats([s['paint_ns'] for s in ss if s['paint_ns'] is not None]),
            'parts':{k:{'median_inclusive_ns':statistics.median(s['parts'].get(k,{}).get('inclusive_ns',0) for s in ss),
                        'median_self_ns':statistics.median(s['parts'].get(k,{}).get('self_ns',0) for s in ss)} for k in keys}}
b,a,c=read('before.json'),read('after.json'),read('balanced.json')
assert len(b['workers'])==len(a['workers'])==20 and len(c['workers'])==40
assert not b['failures'] and not a['failures'] and not c['failures']
assert b['worker_script_sha256']==a['worker_script_sha256']==c['worker_script_sha256']
assert b['seed_sha256']==a['seed_sha256']==c['seed_sha256']
for w in b['workers']+a['workers']+c['workers']:check_worker(w)
for wb,wa in zip(b['workers'],a['workers']):
    assert wb['initial_state']==wa['initial_state']
    for sb,sa in zip(wb['samples'],wa['samples']):assert query_calls(sb)==query_calls(sa)
result={'schema':1,'worker_script_sha256':b['worker_script_sha256'],'seed_sha256':b['seed_sha256'],
        'sequential':{kind:{'before':group(b,kind),'after':group(a,kind)} for kind in ('first_open','cached_return')},
        'balanced':{},'pairs':[],'query_and_initial_shape_equal':True,
        'raw_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name not in ('COMPARISON.json','VALIDATION.json')}}
for strategy in ('legacy_parent','final_parent'):
    data={'workers':[w for w in c['workers'] if w['strategy']==strategy]}
    result['balanced'][strategy]={kind:group(data,kind) for kind in ('first_open','cached_return')}
    result['balanced'][strategy]['add_widget']=stats([w['mechanism']['add_widget_ns'][0] for w in data['workers']])
for pair in range(20):
    ww=[w for w in c['workers'] if w['pair']==pair];assert len(ww)==2
    expected=['legacy_parent','final_parent'] if pair%2==0 else ['final_parent','legacy_parent']
    assert [w['strategy'] for w in ww]==expected and [w['order_index'] for w in ww]==[0,1]
    old=next(w for w in ww if w['strategy']=='legacy_parent');new=next(w for w in ww if w['strategy']=='final_parent')
    assert old['initial_state']==new['initial_state']
    for so,sn in zip(old['samples'],new['samples']):assert query_calls(so)==query_calls(sn)
    assert old['mechanism']['parent_changes']==old['mechanism']['style_changes']==1
    assert new['mechanism']['parent_changes']==new['mechanism']['style_changes']==0
    old_ns=old['samples'][0]['total_ns'];new_ns=new['samples'][0]['total_ns']
    result['pairs'].append({'pair':pair,'order':expected,'legacy_ns':old_ns,'final_ns':new_ns,'delta_ns':old_ns-new_ns,'reduction_percent':100*(old_ns-new_ns)/old_ns})
result['paired_delta']=stats([p['delta_ns'] for p in result['pairs']]);result['paired_median_reduction_percent']=statistics.median(p['reduction_percent'] for p in result['pairs']);result['pairs_with_lower_first_open']=sum(p['delta_ns']>0 for p in result['pairs'])
for key,data in (('sequential',result['sequential']),('balanced',result['balanced'])):
    if key=='sequential':
        for kind,row in data.items():print(key,kind,'before',row['before']['total'],'after',row['after']['total'])
    else:
        for strategy,row in data.items():print(key,strategy,row['first_open']['total'],'add_widget',row['add_widget'])
print('paired median reduction',result['paired_median_reduction_percent'],'wins',result['pairs_with_lower_first_open'],'/20')
(OUT/'COMPARISON.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
