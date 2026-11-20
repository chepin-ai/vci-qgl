#!/usr/bin/env python3
# KAT for heartbeat fatal/success branches; zero network and zero real credentials.
import contextlib, importlib.util, io, json, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('heartbeat_api', os.path.join(HERE, 'heartbeat_api.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fails = []

def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

# Fatal tree read must print only status metadata and terminate nonzero.
m.api = lambda *a, **k: (404, '')
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        m.main()
except SystemExit as e:
    fatal_code = e.code
else:
    fatal_code = None
check('fatal tree exits 1', fatal_code == 1)
check('fatal output remains structured', json.loads(out.getvalue()) == {'fatal': 'tree', 'http': 404})

# A valid empty tree still completes normally and writes a local receipt without git/network.
m.api = lambda *a, **k: (200, json.dumps({'tree': []}))
m.sh = lambda *a: ''
cwd = os.getcwd()
out = io.StringIO()
try:
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        with contextlib.redirect_stdout(out):
            m.main()
        receipt_ok = len(os.listdir('receipts')) == 2
finally:
    os.chdir(cwd)
summary = json.loads(out.getvalue())
check('valid empty tree exits normally', summary == {'addr': 0, 'new': 0, 'wake_put': None, 'pushed': False} and receipt_ok)
print('KAT: %d pass, %d fail' % (3 - len(fails), len(fails)))
raise SystemExit(1 if fails else 0)
