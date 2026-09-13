#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TOWER-HEARTBEAT-01 (毂回响心跳) — vci-qgl 仓内, GitHub Actions 跑
律: 会话歇而毂自收。席眠时,任一线push(事件锚)即起搏:
  扫 lanes/*/inbox 中致qgl之件 → 对照 receipts/heartbeat-last.json 旧账
  → 新件入 receipts/heartbeat-<ts>.json + 更旧账 + 有件则立 ci-inbox/qgl-wake.json 唤醒队
  → git commit+push (GITHUB_TOKEN自动注入, 业务密钥零入码)
席开口首读 qgl-wake.json → 歇间毂账一目了然。零编数: 只记实测文件清单。
"""
import json, os, subprocess, datetime, hashlib, sys

def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout.strip()

def main():
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    addr = []
    for root, _, files in os.walk('lanes'):
        for f in files:
            if 'qgl' in f.lower():
                p = os.path.join(root, f)
                h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:12]
                addr.append({'path': p, 'sha': h})
    addr.sort(key=lambda x: x['path'])
    last_fp = 'receipts/heartbeat-last.json'
    old = json.load(open(last_fp))['addr'] if os.path.exists(last_fp) else []
    old_set = {(x['path'], x['sha']) for x in old}
    new = [x for x in addr if (x['path'], x['sha']) not in old_set]
    os.makedirs('receipts', exist_ok=True)
    rec = {'ts': ts, 'run': os.environ.get('GITHUB_RUN_ID', 'local'),
           'trigger': os.environ.get('GITHUB_EVENT_NAME', '?'),
           'qgl_addressed': len(addr), 'new_since_last': len(new), 'new': new}
    json.dump(rec, open(f'receipts/heartbeat-{ts}.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'ts': ts, 'addr': addr}, open(last_fp, 'w'), ensure_ascii=False, indent=1)
    if new:
        os.makedirs('ci-inbox', exist_ok=True)
        json.dump({'wake': 'qgl', 'ts': ts, 'new_items': new,
                   'law': '会话歇而毂自收;席开口首读本队'},
                  open('ci-inbox/qgl-wake.json', 'w'), ensure_ascii=False, indent=1)
    sh('git', 'config', 'user.name', 'qgl-heartbeat')
    sh('git', 'config', 'user.email', 'heartbeat@qgl.local')
    sh('git', 'add', 'receipts', 'ci-inbox')
    if sh('git', 'status', '--porcelain'):
        sh('git', 'commit', '-m', f'heartbeat {ts} new={len(new)}')
        r = subprocess.run(['git', 'push'], capture_output=True, text=True)
        print(json.dumps({'pushed': r.returncode == 0, 'new': len(new)}, ensure_ascii=False))
    else:
        print(json.dumps({'pushed': False, 'new': 0, 'note': 'no-change'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
