import hashlib, json, os, subprocess, sys, time
from pathlib import Path

root = Path.cwd()
out = root / 'build/ui-v2-integration/exact-children'
out.mkdir(exist_ok=True)
cases = [('modal-message', [sys.executable, '-B', '-m', 'tests.ui_dialog_process', 'DialogProcessTests.test_message', '-v'], 45, None)]
cases += [('scale-' + scale, [sys.executable, str(root / 'scripts/uir04_scale_acceptance.py'), '--scale', scale], 60, scale) for scale in ('1.0', '1.25', '1.5')]
results = []
for name, command, timeout, scale in cases:
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    if scale:
        env.update(QT_AUTO_SCREEN_SCALE_FACTOR='0', QT_SCALE_FACTOR=scale)
    start = time.monotonic()
    try:
        run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 'TIMEOUT', error.stdout or b'', error.stderr or b''
        stdout = stdout.decode('utf-8', 'replace') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode('utf-8', 'replace') if isinstance(stderr, bytes) else stderr
    (out / (name + '.stdout.log')).write_text(stdout, encoding='utf-8')
    (out / (name + '.stderr.log')).write_text(stderr, encoding='utf-8')
    results.append(dict(name=name, command=command, timeout_seconds=timeout, elapsed_seconds=time.monotonic()-start, returncode=code))
    print(json.dumps(results[-1]), flush=True)
summary = dict(source_sha256=hashlib.sha256((root/'packages/ui/carbon_material_page.py').read_bytes()).hexdigest(), results=results)
(out/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
sys.exit(0 if all(result['returncode'] == 0 for result in results) else 1)
