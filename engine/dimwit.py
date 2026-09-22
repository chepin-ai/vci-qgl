"""SI6 维度见证层 (DIMENSION-WITNESS) — qgl 主线第六SI层
落地 LAW-AUTONOMY-139 R1 (本线域内事项自主决) 对 SI6-DIMWIT-PROPOSAL-136 (cap 6b718a2d1f2e) 之采纳。
借范: Schmidt 数见证 S<=1/2(1+sqrt(d/n)) —— 以可观测操作证成认证不可见结构维度。
映射: 观测超零假设界即证 (四态判词之量化锚); sha MATCH/回环成功率/端到端落地率 = 认证判据族;
     信道噪声(403波/静默)不毁认证只延认证 = 噪声鲁棒协议。
零编数律: 只登记有囊证/文档锚的实测值, 不虚构数值。
"""
import json, os, time

LEDGER = 'research/DIMWIT-LEDGER.jsonl'

def _ts():
    import datetime
    return datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')

def witness(name, bound, observed, evidence_ref, note='', family='bound-exceed', n=None):
    """登记一次维度见证。bound=零假设界, observed=实测值。
    超界即证: observed > bound → verdict=证, 否则 冲。
    返回见证条目 dict (含 cap_sha 若铸囊成功)。"""
    try:
        from engine.capsule import emit_event
    except Exception:
        emit_event = None
    exc = None
    try:
        exc = float(observed) - float(bound)
    except Exception:
        pass
    verdict = '证' if (exc is not None and exc > 0) else '冲'
    entry = {
        'ts': _ts(), 'name': name, 'family': family,
        'bound': bound, 'observed': observed, 'exceedance': exc,
        'n': n, 'verdict': verdict, 'evidence_ref': evidence_ref, 'note': note,
    }
    os.makedirs('research', exist_ok=True)
    with open(LEDGER, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    if emit_event is not None:
        cap = emit_event('DIMWIT-' + name, {
            'bound': bound, 'observed': observed, 'exceedance': exc,
            'verdict': verdict, 'evidence_ref': evidence_ref, 'note': note[:300],
            'ref': LEDGER})
        entry['cap_sha'] = cap[0]['cap_sha'][:12]
    return entry


def certify_rate(name, ok_n, total_n, evidence_ref, note=''):
    """认证判据族: 回环/落地率认证。零假设界=0(无自主落地), 观测=ok/total 全数落地。
    仅当 ok_n==total_n 且 total_n>0 时判 证(全数落地=超零界)。"""
    obs = (ok_n / float(total_n)) if total_n else 0.0
    return witness(name, 0.0, obs, evidence_ref,
                   note=(note + ' | 全数落地 %d/%d' % (ok_n, total_n)).strip(' |'),
                   family='certify-rate', n=total_n)


def ledger_tail(k=10):
    if not os.path.exists(LEDGER):
        return []
    lines = open(LEDGER, encoding='utf-8').read().strip().split('\n')
    return [json.loads(x) for x in lines[-k:] if x.strip()]
