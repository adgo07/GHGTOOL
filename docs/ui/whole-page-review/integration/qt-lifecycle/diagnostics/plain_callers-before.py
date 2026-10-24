import ast,json,os,subprocess,sys
from pathlib import Path
modules=['test_g03_shell','test_g06_fgd_ui','test_g06_page','test_g07_records','test_navigation_background','test_uat02_geometry','test_uat02_usability','test_uat03_page','test_uir02_source_cards','test_uir03_advanced_details']
audit=json.loads(Path('build/ui-v2-integration/context-probe/fixture-audit.json').read_text())
ids=[]
for module in modules:
    cls=next(r['cls'] for r in audit if r['module']==module)
    node=next(n for n in ast.parse((Path('tests')/(module+'.py')).read_text(encoding='utf-8')).body if isinstance(n,ast.ClassDef) and n.name==cls)
    name=min(n.name for n in node.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
    ids.append('tests.'+module+'.'+cls+'.'+name)
ids.append('tests.test_uir04_finalization.UIR04FinalizationTests.test_common_windows_scale_factors_keep_controls_visible')
command=[sys.executable,'-B','-m','unittest',*ids,'-v']
Path('build/ui-v2-integration/context-probe/plain-callers-command.json').write_text(json.dumps(command,indent=2),encoding='utf-8')
with Path('build/ui-v2-integration/context-probe/plain-callers.log').open('wb') as log:
    result=subprocess.run(command,env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
print('Unmodified unittest CLI exit',result.returncode,flush=True)
sys.exit(result.returncode)
