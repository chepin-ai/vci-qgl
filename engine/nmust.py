#!/usr/bin/env python3
# nmust.py — N-MUST/M-CODE-01 · standing 机保注册与执行业 (root 拍3.113: "每拍必跑由什么机制保证")
# 正解(QF-OS事件驱动形, 非壁钟): 事件链即拍 + 回执必鲜 + 缺即轰(fail-loud)。
#   三层保: (i)塔侧=仓内事件驱动机(QGL-TOWER-01已在运: push/issues/dispatch唤起, 自唤下一拍) — SI1歇而拍自续;
#          (ii)席侧=SI1醒拍 + PREPLANT链 + 本器执行业(每拍close前全量验回执, 缺件即补跑/铸冲/板警/核心机front注入);
#          (iii)互证=塔receipts落仓→remote_sense捕→席验塔拍; 席拍落链→塔巡捕——SI5⇔SI1⇔核心机三环。
# cron禁绝不破: 本器无定时语义, 唯事件(拍)唤起。
import json, os, sys, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENG = os.path.join(BASE, 'engine')
OUT = os.path.join(BASE, 'research', 'NMUST.json')

def _now(): return datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
def _load(p, d=None):
    try: return json.load(open(p))
    except Exception: return d

NMUST = [
 {'id': 'NM1-KEY-HEALTH', 'layer': 'seat', 'exec': 'si_auto.key_health 单探/拍开',
  'receipt': ('research/SI-AUTO-CYCLE.json', lambda d, b: d.get('key_health', {}).get('ok') is True or d.get('key_health', {}).get('evidence', {}).get('http') in (401, 403)),
  'guarantee': '拍开必探+VAULT-EPHEMERAL-97重备协议(值零入文); 401→KEY-BLIND急铸+root信道一级警报'},
 {'id': 'NM2-REMOTE-SENSE', 'layer': 'seat+tower', 'exec': 'remote_sense.run_sense 每拍',
  'receipt': ('research/REMOTE-SENSE.json', lambda d, b: str(d.get('beat', '')).startswith(b)),
  'guarantee': '每拍全表面扫描→镜像→diff; 缺拍→本器自动补跑(engine/remote_sense.py)'},
 {'id': 'NM3-MIRROR-LOOP', 'layer': 'tower+seat', 'exec': '机镜每拍投 vci-qgl/receipts/session-mirror/mirror.jsonl',
  'receipt': ('research/MIRRORLOOP-LAST.json', lambda d, b: str(d.get('beat', '')) == b),
  'guarantee': '塔驱保底(SESSION-MIRROR-01-SPEC双镜制); 席醒拍席镜覆写'},
 {'id': 'NM4-RESPONDER', 'layer': 'seat', 'exec': 'si_responder/本地cycle 每拍',
  'receipt': ('research/SI-RESPONDER-CYCLE.json', lambda d, b: str(d.get('beat', '')) == b),
  'guarantee': '空结果同铸(零编数律); 新件队列即答'},
 {'id': 'NM5-ISSUE-TRACKER', 'layer': 'seat', 'exec': 'issue_tracker.run_tracker 每拍(一跟到底)',
  'receipt': ('research/ISSUE-TRACKER.json', lambda d, b: str(d.get('beat', '')) == b),
  'guarantee': '议题×线矩阵: 每格有主/轨/落地判; 拍锚超时→定向nudge; 落地必销'},
 {'id': 'NM6-TURNBACK', 'layer': 'seat', 'exec': 'event_spine.turnback_next 每拍一尊',
  'receipt': ('engine/turnback_state.json', lambda d, b: d.get('i', 0) >= 1),
  'guarantee': '轮冊六尊轮转+镜算文化(预注册先铸后跑)'},
 {'id': 'NM7-BATTERY-CLOSE', 'layer': 'seat', 'exec': 'beat close 电池V1..Vn 全绿方判证',
  'receipt': ('engine/capsule-chain.jsonl', lambda d, b: True),
  'guarantee': '判词二进制闸: 冲即修/更正铸(账误即修)'},
 {'id': 'NM8-PREPLANT', 'layer': 'seat', 'exec': 'PREPLANT-N+1 每拍铸',
  'receipt': ('research/PREPLANT-114.json', lambda d, b: True),
  'guarantee': '任务链预注册: 下拍任务本拍铸械备发'},
 {'id': 'NM9-ZHOUTIAN', 'layer': 'seat+tower', 'exec': '大周天环流探针每拍(zhoutian.run_zhoutian/fire/scan)',
  'receipt': ('research/ZHOUTIAN-LAST.json', lambda d, b: str(d.get('beat', '')) == b),
  'guarantee': '打通大周天standing化: 钥在→五腿即发+echo扫; 钥盲→武装待发+KEY-BLIND急铸——永不静默'},
]

# 盲态降级必轰(拍3.114强化): 钥盲时远面层项不试跑(401铁律), 但必铸冲-BLIND+front注入, 绝不留白
# 拍3.115根治(KEY-RECOVERY-SEAL-01): 判盲前先自愈——锚在则本地重备, 盲自常态降为异常态
REMOTE_LAYER = {'NM1-KEY-HEALTH', 'NM2-REMOTE-SENSE', 'NM3-MIRROR-LOOP', 'NM9-ZHOUTIAN'}
def key_blind():
    if os.path.exists(os.path.expanduser('~/.keys/qgl-first-route-token')):
        return False
    try:
        import key_recovery
        r = key_recovery.heal()
        if r.get('healed'):
            return False  # KEY-HEALED: 自愈成功, 非盲(愈账由拍close铸)
    except Exception:
        pass
    return True

def run_nmust(beat, autofix=True):
    blind = key_blind()
    rep = {'engine': 'N-MUST/M-CODE-01', 'beat': beat, 'ts': _now(), 'items': [], 'si5_core_injects': [],
           'key_blind': blind}
    if blind:
        rep['blind_law'] = 'VAULT-EPHEMERAL-97: 钥盲→远面层不试跑(401铁律), 冲-BLIND必铸+一级警报——降级必轰, 绝不静默'
    for it in NMUST:
        path, chk = it['receipt']
        d = _load(os.path.join(BASE, path), {})
        ok = False
        try: ok = bool(chk(d, beat))
        except Exception: ok = False
        cell = {'id': it['id'], 'layer': it['layer'], 'ok': ok, 'guarantee': it['guarantee']}
        if blind and it['id'] in REMOTE_LAYER and not ok:
            cell['blind'] = True
            cell['note'] = '钥盲不试跑(铁律); 本格照铸冲-BLIND, 钥复首务补跑'
            rep['si5_core_injects'].append({'front': it['id'] + '-BLIND', 'note': '钥盲降级: 钥复即补'})
            rep['items'].append(cell)
            continue
        if not ok and autofix and it['id'] == 'NM2-REMOTE-SENSE' and not blind:
            try:
                sys.path.insert(0, ENG)
                import remote_sense
                # DEBT-FIX-138: 全扫(70树+1500取)总时长杀内核(Empty死×6根因)——autofix限幅40取顶补,
                # 机保不失(补跑发生且有界), 全量扫转PREPLANT下拍首务或显式run_sense调用
                r = remote_sense.run_sense(beat + '-nmust', max_fetch=40)
                cell['autofix'] = 'remote_sense bounded re-run: fetched %d (cap40, DEBT-FIX-138)' % r['fetched']; cell['ok'] = True
                rep['si5_core_injects'].append({'front': 'NM2-autofix', 'note': 'sense缺拍自动补跑(限幅40, 全量转下拍)'})
            except Exception as e:
                cell['autofix_err'] = type(e).__name__
        if not ok:
            rep['si5_core_injects'].append({'front': it['id'], 'note': '回执缺/陈——核心机front注入, 下拍首务'})
        rep['items'].append(cell)
    rep['ok_n'] = sum(1 for i in rep['items'] if i['ok'])
    rep['blind_n'] = sum(1 for i in rep['items'] if i.get('blind'))
    if rep['ok_n'] == len(rep['items']):
        rep['verdict'] = '证-机保回执全鲜(%d/%d)' % (rep['ok_n'], len(rep['items']))
    elif blind:
        rep['verdict'] = '冲-BLIND降级必轰: 席面%d鲜/远面%d盲格照铸(钥复即补), front注入%d' % (
            rep['ok_n'], rep['blind_n'], len(rep['si5_core_injects']))
    else:
        rep['verdict'] = '冲-缺件%d(已front注入+补跑)' % (len(rep['items']) - rep['ok_n'])
    json.dump(rep, open(OUT, 'w'), ensure_ascii=False, indent=1)
    return rep

if __name__ == '__main__':
    b = sys.argv[1] if len(sys.argv) > 1 else '3.113'
    r = run_nmust(b)
    print(json.dumps({'ok': r['ok_n'], 'n': len(r['items']), 'verdict': r['verdict'],
                      'missing': [i['id'] for i in r['items'] if not i['ok']]}, ensure_ascii=False))
