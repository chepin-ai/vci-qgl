#!/usr/bin/env python3
# key_sentinel.py — SCAN 四步机件化(qfa 铸全联版): /user 钥体检 + 401钥亡警 + secrets元数据差分 + 降级面
# 值永不入文/日志: 唯 名/http码/updated_at 落 receipt
import json, os, time, urllib.request, urllib.error

GH = 'https://api.github.com'
REPO = os.environ.get('GITHUB_REPOSITORY', '')

def probe(token):
    if not token:
        return None
    req = urllib.request.Request(GH + '/user', headers={
        'Authorization': 'token ' + token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'key-sentinel'})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return {'http': r.status, 'login': json.load(r).get('login')}
    except urllib.error.HTTPError as e:
        return {'http': e.code}
    except Exception as e:
        return {'err': str(e)[:80]}

def secrets_meta(token):
    req = urllib.request.Request(GH + '/repos/' + REPO + '/actions/secrets?per_page=100', headers={
        'Authorization': 'token ' + token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'key-sentinel'})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.load(r)
        return {'http': 200, 'names': sorted({s['name']: s.get('updated_at', '') for s in d.get('secrets', [])}.items())}
    except urllib.error.HTTPError as e:
        return {'http': e.code}
    except Exception as e:
        return {'err': str(e)[:80]}

def main():
    ts = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    keys = {}
    for name in ('AI_FULL_PAT', 'CI_OPS_LINE_KEY', 'GH_TOKEN'):
        p = probe(os.environ.get(name))
        if p:
            keys[name] = p
    alive = [k for k, v in keys.items() if v.get('http') == 200]
    dead = [k for k, v in keys.items() if v.get('http') == 401]
    meta = secrets_meta(os.environ.get('AI_FULL_PAT') or os.environ.get('CI_OPS_LINE_KEY') or os.environ.get('GH_TOKEN'))
    state_p = 'receipts/key-sentinel/state.json'
    prev = {}
    if os.path.exists(state_p):
        prev = json.load(open(state_p))
    rec = {'id': 'KEY-SENTINEL-LINE-01', 'repo': REPO, 'ts': ts, 'clock': 'VOID',
           'keys': keys, 'alive': alive, 'dead401': dead,
           'secrets_meta_http': meta.get('http'), 'secrets_meta': meta.get('names'),
           'degraded': len(alive) == 0, 'diff_vs_prev': None}
    if prev.get('secrets_meta') is not None and prev.get('secrets_meta') != rec['secrets_meta']:
        rec['diff_vs_prev'] = {'prev': prev['secrets_meta'], 'cur': rec['secrets_meta']}
    os.makedirs('receipts/key-sentinel', exist_ok=True)
    json.dump(rec, open(state_p, 'w'), ensure_ascii=False, indent=1)
    json.dump(rec, open('receipts/key-sentinel/KS-' + ts + '.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'alive': alive, 'dead401': dead, 'meta_http': meta.get('http'), 'degraded': rec['degraded']}))

if __name__ == '__main__':
    main()
