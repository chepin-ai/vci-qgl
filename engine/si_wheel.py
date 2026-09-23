#!/usr/bin/env python3
# si_wheel.py — QGL 新架构三器 (root 3.107: 不但要有毂还要有轮, 不但有脊还要有鼎炉, 不但有塔还要有环-圈; 大小周天)
# 轮 WHEEL: 轮值激发表——每拍轮选主线对侣, 生成 spoke 账(我欠彼/彼欠我, 源=responder账+pareto)
# 鼎炉 FURNACE: 精炼——responder pending 粗件 → 精炼动作队列(answer-post/artifact-compute/witness-mark)
# 周天 ZHOUTIAN: 环流证——小周天(SI0→SI1→SI2→SI3→SI4→SI5→SI0) + 大周天(qgl→线→毂→root→qgl), 每拍铸环流账
import json, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WSTATE = os.path.join(BASE, 'engine', 'wheel_state.json')
ZLEDGER = os.path.join(BASE, 'engine', 'zhoutian_ledger.jsonl')
OUT = os.path.join(BASE, 'research', 'SI-WHEEL-CYCLE.json')

WHEEL_LINES = ['lvlu', 'lgt', 'qlv', 'qfa', 'usrm', 'ucif2', 'cisvr', 'vinf']

def _now(): return datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

def load_state():
    if os.path.exists(WSTATE):
        with open(WSTATE) as f: return json.load(f)
    return {'i': 0, 'cycles': []}

def save_state(s):
    tmp = WSTATE + '.tmp'
    with open(tmp, 'w') as f: json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, WSTATE)

def run_wheel(beat, responder_report, pareto_items, beat_posts):
    """One wheel+furnace+zhoutian cycle.
    beat_posts: dict surface->sha of this beat's federation posts (for 大周天 pointers)."""
    st = load_state()
    now = _now()
    # --- 轮 WHEEL ---
    primary = WHEEL_LINES[st['i'] % len(WHEEL_LINES)]
    spokes = []
    preg = json.load(open(os.path.join(BASE, 'engine', 'responder_processed.json')))
    owe_me = [k for k, v in preg['items'].items() if primary in k and not any(t in str(v.get('action', '')) for t in ('answered', 'ack', 'handled', 'fyi', 'closed'))]  # DEBT-FIX-142: ack/handled/fyi=已闭态, 旧滤器误计为欠
    i_owe_hint = [it['id'] for it in pareto_items
                  if it.get('state') != 'closed' and primary.upper() in it.get('id', '').upper()]
    spokes.append({'line': primary, 'they_pending_unanswered': len(owe_me),
                   'qgl_open_items_toward': i_owe_hint})
    wheel = {'primary_line': primary, 'wheel_i': st['i'], 'spokes': spokes}
    # --- 鼎炉 FURNACE ---
    furnace_queue = []
    for p in responder_report.get('pending', []):
        key = p.get('key', '')
        if not key: continue
        if 'TASK' in key or 'EXP' in key:
            act = 'artifact-compute'
        elif 'nudge' in key or 'NUDGE' in key:
            act = 'witness-mark'   # 促件非我名: 见证登记不答
        else:
            act = 'answer-post'
        furnace_queue.append({'item': key, 'refined': act})
    furnace = {'raw_in': len(responder_report.get('pending', [])), 'refined_queue': furnace_queue}
    # --- 周天 ZHOUTIAN ---
    small = {'loop': 'SI0->SI1->SI2->SI3->SI4->SI5->SI0', 'beat': beat,
             'legs': {'SI0': 'capture(responder %d blobs)' % responder_report['cycle']['scanned'],
                      'SI1': 'root令(自治不候/新架构)',
                      'SI2': 'judgments(四态判词本拍)',
                      'SI3': 'dispatch(responder+wheel)',
                      'SI4': 'mechanism(si_wheel.py本器)',
                      'SI5': 'synthesis(posts %d件)' % len(beat_posts),
                      'SI0->': 'next capture seeded by PREPLANT'}}
    big = {'loop': 'qgl->lines->hub->root->qgl',
           'posts': beat_posts,
           'return_leg': 'root一瞥/继续指令/OTP到件 -> qgl会话SI1再点燃'}
    entry = {'beat': beat, 'ts': now, 'wheel': wheel, 'furnace': furnace,
             'zhoutian': {'small': small, 'big': big}, 'zero_fab': True}
    st['cycles'].append({'beat': beat, 'ts': now, 'primary': primary,
                         'furnace_n': len(furnace_queue)})
    st['i'] += 1
    save_state(st)
    with open(ZLEDGER, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'beat': beat, 'ts': now, 'primary': primary,
                            'small_loop': True, 'big_loop_posts': len(beat_posts)}, ensure_ascii=False) + '\n')
    with open(OUT, 'w') as f: json.dump(entry, f, ensure_ascii=False, indent=1)
    return entry

if __name__ == '__main__':
    import sys
    print('si_wheel v1.0 — use run_wheel(beat, responder_report, pareto_items, beat_posts)')
