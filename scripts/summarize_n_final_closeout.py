"""Verify and summarize the single bounded candidate without business tolerances."""
from pathlib import Path
import ast,hashlib,json,math,statistics,textwrap
from scripts.profile_n_final_closeout import CHANGES,production_hash
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/performance/n-final-closeout';P.mkdir(exist_ok=True)
def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def stats(v):
 v=sorted(v);return dict(n=len(v),median_ns=statistics.median(v),p95_nearest_rank_ns=v[math.ceil(.95*len(v))-1],min_ns=min(v),max_ns=max(v))
d=json.loads((ROOT/'tmp/n-final-closeout/formal-abba-01/raw.json').read_bytes());assert not d['failures'];assert len(d['workers'])==40
assert d['production_sha256']==production_hash()
assert d['control_script_sha256']==hashlib.sha256((ROOT/'scripts/profile_n_final_closeout.py').read_bytes()).hexdigest()
assert d['worker_script_sha256']==hashlib.sha256((ROOT/'scripts/profile_n_first_open.py').read_bytes()).hexdigest()
assert d['worker_script_sha256']=='7ad87b464e8e27fa882cd3b8409222dafcb5fa36e1612c52468357579f684dd5'
for name,h in d['seed_sha256'].items():assert hashlib.sha256((ROOT/'tmp/n-first-open/seed'/name).read_bytes()).hexdigest()==h
source=(ROOT/'packages/ui/carbon_material_page.py').read_text(encoding='utf-8');cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='CarbonMaterialAccountingPage')
actual={n.name:hashlib.sha256(textwrap.dedent('\n'.join(source.splitlines()[n.lineno-1:n.end_lineno])).encode()).hexdigest() for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in CHANGES}
result={'base':d['base'],'sampling_head':d['head'],'production_sha256':d['production_sha256'],'series':'independent formal ABBA, not pooled with diagnostic or PR56','strategies':{},'pairs':[],'query_counts_equal':True,'all_tracked_call_counts_equal':True,'qt_callback_errors':0,'actual_final_methods_match':True}
def calls(s):return {k:v['calls'] for k,v in s['parts'].items()}
for w in d['workers']:
 assert not w['qt_callback_errors'];assert w['initial_state']==d['workers'][0]['initial_state']
 for s in w['samples']:assert s['correct_page'] and s['total_ns']==s['navigate_ns']+s['event_pump_ns']
 if w['strategy']=='final_parent':assert w['candidate_method_sha256']==actual
for strategy in ('legacy_parent','final_parent'):
 ws=[w for w in d['workers'] if w['strategy']==strategy]
 result['strategies'][strategy]={}
 for kind in ('first_open','cached_return'):
  samples=[s for w in ws for s in w['samples'] if s['kind']==kind]
  keys=sorted({k for s in samples for k in s['parts']})
  result['strategies'][strategy][kind]={'total':stats([s['total_ns'] for s in samples]),'parts':{k:{field:stats([s['parts'].get(k,{}).get(field,0) for s in samples]) for field in ('calls','inclusive_ns','self_ns')} for k in keys}}
for i in range(20):
 pair=[w for w in d['workers'] if w['pair']==i];assert [w['strategy'] for w in pair]==(['legacy_parent','final_parent'] if i%2==0 else ['final_parent','legacy_parent'])
 old=next(w for w in pair if w['strategy']=='legacy_parent');new=next(w for w in pair if w['strategy']=='final_parent')
 for os,ns in zip(old['samples'],new['samples']):assert calls(os)==calls(ns),(i,os['kind'],calls(os),calls(ns))
 a=old['samples'][0]['total_ns'];b=new['samples'][0]['total_ns'];result['pairs'].append({'pair':i,'legacy_ns':a,'final_ns':b,'reduction_ns':a-b,'reduction_percent':100*(a-b)/a})
result['paired_median_reduction_ns']=statistics.median(p['reduction_ns'] for p in result['pairs']);result['paired_median_reduction_percent']=statistics.median(p['reduction_percent'] for p in result['pairs']);result['pairs_faster']=sum(p['reduction_ns']>0 for p in result['pairs']);result['initial_state']=d['workers'][0]['initial_state']
proofs=[json.loads((ROOT/('tmp/n-first-open/'+r+'/proof.json')).read_bytes()) for r in ('final-before-01','final-after-01')];assert proofs[0]['states']==proofs[1]['states'];assert proofs[0]['images']==proofs[1]['images'];assert all(not p['qt_callback_errors'] for p in proofs)
proof={'images_equal':30,'complete_states_equal':2,'files':{},'states':{k:{field:v[field] for field in ('form_sha256','controls_sha256','dirty')} for k,v in proofs[0]['states'].items()},'images':proofs[0]['images']}
for r in ('final-before-01','final-after-01'):proof['files'][r]=hashlib.sha256((ROOT/('tmp/n-first-open/'+r+'/proof.json')).read_bytes()).hexdigest()
write(P/'COMPARISON.json',result);write(P/'SNAPSHOT_PROOF.json',proof)
for name,origin in [('formal-abba.json','formal-abba-01'),('diagnostic.json','diagnostic-01')]:write(P/name,json.loads((ROOT/('tmp/n-final-closeout/'+origin+'/raw.json')).read_bytes()))
print(json.dumps({k:v for k,v in result.items() if k not in ('strategies','pairs')},ensure_ascii=False));print(json.dumps({st:{k:v['total'] for k,v in group.items()} for st,group in result['strategies'].items()}))
