#!/usr/bin/env python3
# KAT for heartbeat fatal/success branches and wake_put persistence; zero network/credentials.
import contextlib, importlib.util, io, json, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('heartbeat_api', os.path.join(HERE, 'heartbeat_api.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fails = []
TOTAL = 6

def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

def only_heartbeat(receipts):
    names = [x for x in os.listdir(receipts) if x.startswith('heartbeat-') and x != 'heartbeat-last.json']
    assert len(names) == 1, names
    with open(os.path.join(receipts, names[0]), encoding='utf-8') as f:
        return json.load(f)

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

# A valid empty tree completes normally and persists an explicit null wake_put.
m.PAT = ''
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
        empty_rec = only_heartbeat('receipts')
finally:
    os.chdir(cwd)
summary = json.loads(out.getvalue())
check('valid empty tree exits normally', summary == {'addr': 0, 'new': 0, 'wake_put': None, 'pushed': False} and receipt_ok)
check('empty receipt persists wake_put null', empty_rec.get('wake_put', 'MISSING') is None)

# New addressed work exercises both successful and failed wake PUT outcomes.
def run_wake(status):
    tree = {'tree': [{'path': 'lanes/lgt/inbox/qgl-task.md', 'sha': 'a' * 40}]}
    def fake_api(method, url, tok, body=None):
        if method == 'GET' and '/git/trees/' in url:
            return 200, json.dumps(tree)
        if method == 'GET' and '/contents/wake/qgl.json' in url:
            return 404, ''
        if method == 'PUT' and '/contents/wake/qgl.json' in url:
            return status, ''
        raise AssertionError((method, url))
    m.PAT = 'dummy-not-a-credential'
    m.api = fake_api
    out = io.StringIO()
    try:
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            with contextlib.redirect_stdout(out):
                m.main()
            rec = only_heartbeat('receipts')
    finally:
        os.chdir(cwd)
    return json.loads(out.getvalue()), rec

summary_201, rec_201 = run_wake(201)
check('wake PUT 201 persists in receipt', summary_201['wake_put'] == 201 and rec_201.get('wake_put') == 201 and rec_201['new_since_last'] == 1)
summary_404, rec_404 = run_wake(404)
check('wake PUT 404 persists in receipt', summary_404['wake_put'] == 404 and rec_404.get('wake_put') == 404 and rec_404['new_since_last'] == 1)

print('KAT: %d pass, %d fail' % (TOTAL - len(fails), len(fails)))
raise SystemExit(1 if fails else 0)
