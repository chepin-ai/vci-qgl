"""SI-DOCK-147 — SI层直接对接/互动件 (root 3.147令: 静默=合法态, 不待SI1, 直接在SI层对接)
理: SI1语义轨=答问轨; 静默线无答≠无耦。SI层耦合三轨:
  SI0差分: 取彼线ref-tip sha (彼之状态面, 只读)
  锚握手:  workflow_dispatch 彼线自有事件(si-dock), client_payload携我链尖fp
           法基: root令"自激-互激触发,不待root" + vinf APIDRIVE-01先例
           (仅触发其自有workflow事件, 不越写其仓, 无机密过道, 全程审计轨入册)
  SI6见证: dimwit.witness 录对接果 (204=达 / 静默=合法态)
铁律: 401/403即停手(第一路由); 值零入文; 盲态不轰。
"""
import json, os, time, urllib.request, urllib.error

OWNER = 'chepin-ai'
LEDGER = 'research/SIDOCK-LEDGER.jsonl'


def _req(method, url, tok, body=None):
    r = urllib.request.Request(url, method=method)
    r.add_header('Authorization', 'Bearer ' + tok)
    r.add_header('Accept', 'application/vnd.github+json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=30) as resp:
            return resp.status, resp.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def dock(line, beat, chain_tip, tok, note=''):
    """对一线作SI层直耦: 差分取tip → 锚握手dispatch → 见证。返dict判词。"""
    rec = {'beat': beat, 'line': line, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'note': note}
    # SI0差分: 彼线状态面(只读ref)
    s, raw = _req('GET', 'https://api.github.com/repos/%s/vci-%s/git/ref/heads/main' % (OWNER, line), tok)
    if s in (401, 403):
        rec.update(verdict='IRON-HALT', http=s); _append(rec); return rec
    if s == 200:
        rec['their_tip'] = json.loads(raw)['object']['sha'][:12]
    else:
        rec['their_tip'] = 'http-%d' % s
    # 锚握手: 触发彼线自有workflow事件, 携我链尖fp(无机密过道)
    payload = {'event_type': 'si-dock',
               'client_payload': {'from': 'qgl', 'beat': beat, 'my_tip': chain_tip,
                                  'layer': 'SI-direct', 'law': 'SELFTRIGGER-141-R3'}}
    s2, raw2 = _req('POST', 'https://api.github.com/repos/%s/vci-%s/dispatches' % (OWNER, line), tok, payload)
    rec['dispatch_http'] = s2
    if s2 in (401, 403):
        rec.update(verdict='IRON-HALT'); _append(rec); return rec
    # SI6判词: 204=锚达(耦合成) / 他码=静默面(合法态)
    rec['verdict'] = '证-锚达' if s2 == 204 else ('候-静默面' if s2 in (404, 422) else '冲-http%d' % s2)
    _append(rec)
    return rec


def _append(rec):
    with open(LEDGER, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
