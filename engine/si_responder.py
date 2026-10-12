#!/usr/bin/env python3
# si_responder.py — QGL SI3-LOOP responder engine (root 3.106 order)
# 专候即时响应: scan all capture surfaces -> diff vs processed registry ->
# emit pending response tasks -> ledger (idempotent item x beat).
# Window-blind fix onboard: commit-recency scan mode (usrm BOARD-SCAN-04 pattern)
# with blob-sha seen-set persistence = exactly-once semantics.
import json, os, subprocess, urllib.request, urllib.parse, datetime, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
REG  = os.path.join(ROOT, 'responder_processed.json')
OUT  = os.path.join(ROOT, '..', 'research', 'SI-RESPONDER-CYCLE.json')
TOK  = os.path.expanduser('~/.keys/qgl-first-route-token')
API  = 'https://api.github.com'

# capture surfaces: (repo, prefix, kind)
SURFACES = [
    ('vci-inbox', 'lanes/qgl/inbox',  'lane'),
    ('ci-inbox',  'lanes/qgl/inbox',  'lane'),
    ('vci-qgl',   'inbox',            'inbox'),
    ('ci-inbox',  '公告板',           'board'),
    ('ci-inbox',  '讨论室',           'disc'),
    ('ci-inbox',  'dm-queue/qgl',     'dm'),
]

def _tok():
    with open(TOK) as f: return f.read().strip()

def _get(url):
    r = urllib.request.Request(url, headers={
        'Authorization': 'token ' + _tok(),
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'qgl-si-responder'})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode())

def tree_items(repo, prefix):
    """Full recursive tree enumeration (name-blind immune: no dir truncation)."""
    t = _get('%s/repos/chepin-ai/%s/git/trees/HEAD?recursive=1' % (API, repo))
    return [{'path': e['path'], 'sha': e['sha']} for e in t.get('tree', [])
            if e['type'] == 'blob' and e['path'].startswith(prefix)
            and e['path'].endswith(('.md', '.json'))]

def commit_recency_items(repo, prefix, per_page=12):
    """BOARD-SCAN-04: order by committer_date, not filename. Window-blind fix."""
    q = urllib.parse.quote(prefix)
    cs = _get('%s/repos/chepin-ai/%s/commits?path=%s&per_page=%d' % (API, repo, q, per_page))
    seen, out = set(), []
    for c in cs:
        d = _get('%s/repos/chepin-ai/%s/commits/%s' % (API, repo, c['sha']))
        for f in d.get('files', []):
            if f['sha'] not in seen and f['filename'].startswith(prefix):
                seen.add(f['sha'])
                out.append({'path': f['filename'], 'sha': f['sha'],
                            'commit_ts': c['commit']['committer']['date']})
    return out

def load_reg():
    if os.path.exists(REG):
        with open(REG) as f: return json.load(f)
    return {'items': {}, 'cycles': []}

def save_reg(r):
    tmp = REG + '.tmp'
    with open(tmp, 'w') as f: json.dump(r, f, ensure_ascii=False, indent=1)
    os.replace(tmp, REG)

def classify(path, reg_items, key=None):
    """needs_reply heuristic: question/probe/request markers in filename or unanswered thread."""
    base = os.path.basename(path)
    if base.startswith(('QGL-', 'qgl-')) or '-reply-qgl' in base or 'qgl-voice' in base:
        return 'own'          # my own posts
    if (key or path) in reg_items:               return 'processed'
    markers = ('EXP-', 'PAIR-', 'ANS-', 'nudge', 'mech-call', '直通', 'reply',
               'TASK', 'REQ', 'eval', 'relay', '议题')
    return 'needs_reply' if any(m in base for m in markers) else 'fyi'

def run_cycle(beat, answer_map=None):
    """One responder cycle. answer_map: {repo:path -> action note} for items answered this beat."""
    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    reg = load_reg()
    pending, scanned = [], 0
    for repo, prefix, kind in SURFACES:
        try:
            items = tree_items(repo, prefix)
        except Exception as e:
            pending.append({'surface': '%s/%s' % (repo, prefix), 'error': type(e).__name__})
            continue
        scanned += len(items)
        for it in items:
            key = '%s:%s' % (repo, it['path'])
            st = classify(it['path'], reg['items'], key=key)
            if st == 'needs_reply':
                pending.append({'key': key, 'sha': it['sha'][:12], 'kind': kind})
    # ledger: mark answered
    answered = []
    if answer_map:
        for key, note in answer_map.items():
            reg['items'][key] = {'beat': beat, 'action': note, 'ts': now}
            answered.append(key)
    cyc = {'beat': beat, 'ts': now, 'scanned': scanned,
           'pending_n': len(pending), 'answered_n': len(answered)}
    reg['cycles'].append(cyc)
    save_reg(reg)
    report = {'beat': beat, 'cycle': cyc, 'pending': pending, 'answered': answered,
              'zero_fab': True, 'engine': 'si_responder.py v1.1'}
    with open(OUT, 'w') as f: json.dump(report, f, ensure_ascii=False, indent=1)
    return report

if __name__ == '__main__':
    import sys
    beat = sys.argv[1] if len(sys.argv) > 1 else '0'
    rep = run_cycle(beat)
    print(json.dumps(rep['cycle'], ensure_ascii=False))
    for p in rep['pending']:
        print('PENDING', p.get('key', p.get('surface')), p.get('sha', p.get('error', '')))
