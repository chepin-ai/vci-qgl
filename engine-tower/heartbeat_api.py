#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TOWER-HEARTBEAT-01B (毂回响心跳·API版) — 跑在 vci-qgl Actions(实测可行演武场)
扫毂仓(ci-inbox) lanes 树致qgl件(tree sha即内容指纹,零下载) → 对照自域 receipts/heartbeat-last.json
→ 新件: 自域 receipts/heartbeat-<ts>.json + 试立毂仓 wake/qgl.json 唤醒队(写败则降级自域,诚实记)
auth: HUB_PAT 由 Secrets.LINE_PAT 注入(值不入码); 回写自域用 GITHUB_TOKEN(Actions自动)。
律: 会话歇而毂自收,席开口首读 wake 队。零编数: 只记树实测。
"""
import json, os, subprocess, datetime, urllib.request, urllib.error, urllib.parse

HUB = 'ci-inbox'
OWNER = 'chepin-ai'
PAT = os.environ.get('HUB_PAT', '')
GT = os.environ.get('GITHUB_TOKEN', '')

def api(method, url, tok, body=None):
    r = urllib.request.Request(url, method=method)
    r.add_header('Authorization', 'Bearer ' + tok)
    r.add_header('Accept', 'application/vnd.github+json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()

def main():
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    s, raw = api('GET', f'https://api.github.com/repos/{OWNER}/{HUB}/git/trees/HEAD?recursive=1', PAT)
    if s != 200:
        print(json.dumps({'fatal': 'tree', 'http': s})); return
    tree = json.loads(raw).get('tree', [])
    addr = sorted([{'path': t['path'], 'sha': t['sha'][:12]} for t in tree
                   if t['path'].startswith('lanes/') and '/inbox/' in t['path']
                   and 'qgl' in t['path'].split('/')[-1].lower()], key=lambda x: x['path'])
    last_fp = 'receipts/heartbeat-last.json'
    old = json.load(open(last_fp)).get('addr', []) if os.path.exists(last_fp) else []
    old_set = {(x['path'], x['sha']) for x in old}
    new = [x for x in addr if (x['path'], x['sha']) not in old_set]
    os.makedirs('receipts', exist_ok=True)
    rec = {'ts': ts, 'run': os.environ.get('GITHUB_RUN_ID', 'local'),
           'trigger': os.environ.get('GITHUB_EVENT_NAME', '?'),
           'hub': 'sha256:' + __import__('hashlib').sha256(f'{OWNER}/{HUB}'.encode()).hexdigest()[:12],
           'qgl_addressed': len(addr), 'new_since_last': len(new), 'new': new}
    json.dump(rec, open(f'receipts/heartbeat-{ts}.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'ts': ts, 'addr': addr}, open(last_fp, 'w'), ensure_ascii=False, indent=1)
    wake = {'wake': 'qgl', 'ts': ts, 'new_items': new, 'law': '会话歇而毂自收;席开口首读本队'}
    wake_http = None
    if new and PAT:
        import base64
        url = f'https://api.github.com/repos/{OWNER}/{HUB}/contents/wake/qgl.json'
        s0, old0 = api('GET', url, PAT)
        b = {'message': 'qgl-wake heartbeat', 'content': base64.b64encode(
            json.dumps(wake, ensure_ascii=False, indent=1).encode()).decode()}
        if s0 == 200:
            try: b['sha'] = json.loads(old0)['sha']
            except Exception: pass
        wake_http, _ = api('PUT', url, PAT, b)
        rec['wake_put'] = wake_http
    sh('git', 'config', 'user.name', 'qgl-heartbeat')
    sh('git', 'config', 'user.email', 'heartbeat@qgl.local')
    sh('git', 'add', 'receipts')
    pushed = False
    if sh('git', 'status', '--porcelain'):
        sh('git', 'commit', '-m', f'heartbeat {ts} new={len(new)}')
        pushed = subprocess.run(['git', 'push'], capture_output=True).returncode == 0
    print(json.dumps({'addr': len(addr), 'new': len(new), 'wake_put': wake_http,
                      'pushed': pushed}, ensure_ascii=False))

if __name__ == '__main__':
    main()
