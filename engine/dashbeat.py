#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashbeat.py — 拍面json生成器 · 组件契约唯一真源（PP160-DASHGEN-UNIFY / DASH-SCHEMA-159-ERRATA铸械）
律：键名契约以组件类型为唯一真源；禁临时内联脚本重写发布面数据。
契约（app/src/qgo/Beat.tsx）：
  dash-beat.json  : {beat, chain_seq, chain_tip, pc, ts, highlights[], pending[]}
  dash-beats.json : {generated_at, current_beat, beats[{beat, caps, seq_first, seq_last}]}
highlights/pending 为拍级 authored 内容：缺省沿用旧件（增不覆写），仅链数字段每拍刷新。
"""
import json, os, datetime, hashlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = os.path.join(BASE, 'engine', 'capsule-chain.jsonl')
PUB = os.path.join(BASE, 'app', 'public')

BEAT_KEYS = ('beat', 'chain_seq', 'chain_tip', 'pc', 'ts', 'highlights', 'pending')   # Beat.tsx DashBeat
BEATS_KEYS = ('generated_at', 'current_beat', 'beats')                                # Beat.tsx DashBeats


def _bkey(b):
    try:
        return tuple(int(x) for x in str(b).split('.'))
    except Exception:
        return (0,)


def aggregate_beats():
    """链body.beat聚合 → (rows, tip_sha, tip_seq)。零编数：全出自链真值。"""
    rows_d, tip_sha, tip_seq = {}, None, -1
    with open(CHAIN, encoding='utf-8') as f:
        for line in f:
            c = json.loads(line)
            tip_sha, tip_seq = c.get('cap_sha', tip_sha), c.get('seq', tip_seq)
            b = c.get('body', {}).get('beat')
            if not b:
                continue
            d = rows_d.setdefault(b, {'beat': b, 'caps': 0, 'seq_first': c['seq'], 'seq_last': c['seq']})
            d['caps'] += 1
            d['seq_first'] = min(d['seq_first'], c['seq'])
            d['seq_last'] = max(d['seq_last'], c['seq'])
    rows = [rows_d[k] for k in sorted(rows_d, key=_bkey)]
    return rows, (tip_sha or ''), tip_seq


def gen_beat_faces(beat, highlights=None, pending=None, pc=None):
    """写 app/public/dash-beat.json + dash-beats.json。authored字段缺省沿用旧件。"""
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rows, tip_sha, tip_seq = aggregate_beats()
    beat_path = os.path.join(PUB, 'dash-beat.json')
    old = {}
    if os.path.exists(beat_path):
        try:
            old = json.load(open(beat_path, encoding='utf-8'))
        except Exception:
            old = {}
    doc = {
        'beat': beat,
        'chain_seq': tip_seq,
        'chain_tip': tip_sha[:12],
        'pc': (pc if pc is not None else int(float(beat)) % 12),
        'ts': now,
        'highlights': highlights if highlights is not None else old.get('highlights', []),
        'pending': pending if pending is not None else old.get('pending', []),
    }
    assert tuple(doc.keys()) == BEAT_KEYS, 'dash-beat 键序契约为 %s' % (BEAT_KEYS,)
    assert isinstance(doc['highlights'], list) and isinstance(doc['pending'], list)
    json.dump(doc, open(beat_path, 'w'), ensure_ascii=False, indent=2)
    beats_doc = {'generated_at': now, 'current_beat': beat, 'beats': rows}
    json.dump(beats_doc, open(os.path.join(PUB, 'dash-beats.json'), 'w'), ensure_ascii=False, indent=2)
    return {'beat': beat, 'chain_seq': tip_seq, 'chain_tip': tip_sha[:12],
            'beats_total': len(rows), 'highlights_carried': highlights is None and bool(old.get('highlights'))}


if __name__ == '__main__':
    import sys
    bt = sys.argv[1] if len(sys.argv) > 1 else '3.160'
    print(json.dumps(gen_beat_faces(bt), ensure_ascii=False))
