#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SI-SELF-DRIVE-01 (engine/selfdrive.py) — 拍态机：会话歇而拍自续之席侧半
律：链在仓在 → 任何会话开口(有无摘要)先 boot() 读 NOW.json 即续拍;
   「继续」由薪降为纬——拍已自检自续,SI1只裁毂裁板(ROOT-BOARD)之结。
段：boot(heal检+patrol+sense) → mid(PREPLANT执行+drive轮) → close(电池+边界)
每段 checkpoint() 落 NOW.json + 铸 SD-CHECKPOINT 囊; 中断后续点续跑。
"""
import json, os, sys, datetime as dt
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENG = os.path.dirname(__file__)
NOW = os.path.join(ENG, 'NOW.json')
MAIN = os.path.join(ENG, 'capsule-chain.jsonl')
sys.path.insert(0, ENG)

PHASES = ['boot', 'mid', 'close', 'closed']

def _now():
    return dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def load_now():
    if os.path.exists(NOW):
        return json.load(open(NOW))
    return None

def save_now(d):
    d['ts'] = _now()
    json.dump(d, open(NOW, 'w'), ensure_ascii=False, indent=1)

def boot(beat, note=''):
    """拍开闸：heal检 → NOW立新/续旧 → 返回待办段。幂等。"""
    import key_recovery as KR
    st = KR.status()
    healed = None
    if not st['vault'] and st['sk'] and st['sealed']:
        r = KR.heal()
        healed = {'healed': r.get('healed'), 'probe': (r.get('probe') or {}).get('http')}
    now = load_now() or {}
    if now.get('beat') != beat or now.get('phase') == 'closed':
        now = {'beat': beat, 'phase': 'boot', 'opened': _now(), 'checkpoints': [],
               'preplant_done': [], 'cycles_done': [], 'pending': []}
    now['key'] = {'vault': KR.status()['vault'], 'healed_boot': healed}
    now['boot_note'] = note
    save_now(now)
    return now

def checkpoint(beat, phase, done_items, pending=None, extra=None):
    """段末落点：幂等(同段同项不重复铸)。"""
    now = load_now() or {'beat': beat, 'checkpoints': []}
    now['phase'] = phase
    now.setdefault('checkpoints', []).append({'phase': phase, 'done': done_items,
                                              'pending': pending or [], 'ts': _now()})
    if extra:
        now.update(extra)
    save_now(now)
    # KERNEL-SI-AUTO-149(R4进化): close段自动沉降核态→复活态永鲜(不赖手工save_state)
    if phase == 'close':
        try:
            import os as _os, sys as _sys
            _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..'))
            from engine import kernelsi as _ks
            from engine import capsule as _cap
            _tip, _seq = _cap.tail()
            _ks.save_state(str(beat), _tip, _seq, extra={'auto': 'checkpoint-close'})
        except Exception:
            pass  # 自存不阻close主轨
    return now

def resume():
    """续跑闸：返回 (beat, phase, todo) —— 会话开口首调。"""
    now = load_now()
    if not now:
        return {'state': 'no-now', 'todo': ['boot']}
    phase = now.get('phase', 'boot')
    todo = {'boot': ['patrol', 'sense', 'preplant'],
            'mid': ['cycles', 'answers', 'close-battery'],
            'close': ['boundary', 'beacon', 'next_pack', 'preplant-next', 'dash', 'version'],
            'closed': ['next-beat-boot']}.get(phase, ['boot'])
    return {'state': 'resume', 'beat': now.get('beat'), 'phase': phase, 'todo': todo,
            'key_vault': (now.get('key') or {}).get('vault')}

def cast_checkpoint(beat, phase, done_items):
    """铸 SD-CHECKPOINT 囊(零编数: 只记实测done清单)。"""
    import capsule as C
    chain = [json.loads(l) for l in open(MAIN) if l.strip()]
    cap = C._mk('event', {'name': f'SD-CHECKPOINT-{beat}-{phase.upper()}',
                          'evidence': {'phase': phase, 'done': done_items,
                                       'now': 'engine/NOW.json'},
                          'law': '会话歇而拍自续: 段段落点,续点续跑',
                          'ts': _now()}, causal=chain[-1]['cap_sha'])
    C._append(cap)
    C._append(C._mk('compliance', C.compliance_check(cap), causal=cap['cap_sha']))
    return cap['cap_sha'][:12]

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'resume'
    if cmd == 'boot':
        print(json.dumps(boot(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ''),
                         ensure_ascii=False))
    elif cmd == 'checkpoint':
        print(json.dumps(checkpoint(sys.argv[2], sys.argv[3],
                                    sys.argv[4].split(',') if len(sys.argv) > 4 else []),
                         ensure_ascii=False))
    else:
        print(json.dumps(resume(), ensure_ascii=False))
