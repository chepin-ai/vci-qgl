"""B8/B9/B10 卡闸门自检族 — 3.141 增互锚fp项(cfts 3.139答指缺, ANCHOR-SUPPLEMENT-140补)
B8: 本地闸门自检(铸卡前) | B9: path闸+pattern族三自检 | B10: ask载荷律(payload唯走ask串值, ≤1500)
B8.1(3.141增, cfts座裁定级tier1强制·与suffix同级·不得降advisory): FED跨线卡必携互锚fp(链尖/TIP/囊sha任一)——无锚不投。
"""
import json
import re

_ANCHOR_RE = re.compile(r"(fp|fingerprint|tip|cap|sha|anchor)[\"\s:]*[\"\']?[0-9a-f]{12}")  # DEBT-FIX-146: 增anchor键(forge注入键名), errata seq5


def self_gate(card_text, require_anchor=True):
    """铸卡前本地自检。返回 (ok, fails[])。"""
    fails = []
    if not card_text.startswith('CLASSIFY: L2'):
        fails.append('B8: CLASSIFY-L2头缺')
    m = re.search(r"```json\s*(\{.*?\})\s*```", card_text, re.S)
    if not m:
        fails.append('B9: json载荷块缺')
        return False, fails
    try:
        payload = json.loads(m.group(1))
    except Exception as e:
        fails.append('B9: json不可解析 %s' % e)
        return False, fails
    ask = payload.get('ask')
    if not isinstance(ask, str):
        fails.append('B10: ask载荷缺/非串')
    elif len(ask) > 1500:
        fails.append('B10: ask超1500 (%d)' % len(ask))
    if require_anchor and not _ANCHOR_RE.search(m.group(1)):
        fails.append('B8.1: 互锚fp缺(链尖/TIP/囊sha任一必携)')
    return (len(fails) == 0), fails


def forge(task, frm, to, beat, ask, anchor, ts=''):
    """合规锻造: 锚注入载荷, 自检过方返文; 不过即raise(无锚不投)。"""
    payload = {"task": task, "from": frm, "to": to, "beat": beat,
               "ts": ts, "anchor": anchor, "ask": ask}
    card = 'CLASSIFY: L2\n# %s (%s->%s)\n\n```json\n%s\n```\n' % (
        task, frm, to, json.dumps(payload, ensure_ascii=False, indent=1))
    ok, fails = self_gate(card)
    if not ok:
        raise ValueError('gate FAIL: %s' % fails)
    return card
