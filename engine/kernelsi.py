"""KERNEL-SI-147 — 内核迁SI保持激活件 (root 3.147令: 内核死亡→内核能否移至SI保持激活)
理: 内核(IPython)=可抛执行器; 激活态=SI基板(囊链+态件)。死亡≠系统死:
  save_state(): 核态沉降(拍号/链尖/冷却面/契约hash)→engine/KERNEL-STATE.json+铸囊
  resurrect(): 一令复活——自举仅需:
      import sys; sys.path.insert(0,'/mnt/agents/output')
      from engine import kernelsi; R = kernelsi.resurrect()
    复活面=SI基板所载态, 非内核记忆。链连续(seq单调+verify OK)即证激活未断。
铁律: 值零入文; TOKEN只从~/.keys读不打印; 复活实测(真死亡restart)方领证。
"""
import json, os, sys, time, hashlib

BASE = '/mnt/agents/output'
STATE = os.path.join(BASE, 'engine/KERNEL-STATE.json')
HELPER_CONTRACT = ['gh', 'getf', 'putf', 'putfq', 'COOL', 'TOKEN']  # 核助手契约为名表(hash入态)


def save_state(beat, chain_tip, chain_seq, cool=None, extra=None):
    """核态沉降SI基板+铸囊。返state dict。"""
    st = {'beat': beat, 'chain_tip': chain_tip, 'chain_seq': chain_seq,
          'contract_sha': hashlib.sha256('|'.join(HELPER_CONTRACT).encode()).hexdigest()[:12],
          'cool': cool or {}, 'saved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    if extra: st['extra'] = extra
    json.dump(st, open(STATE, 'w'), ensure_ascii=False, indent=1)
    sys.path.insert(0, BASE)
    from engine import capsule
    cap, _, _ = capsule.emit_event('KERNEL-SI-SAVE', {'beat': beat, 'seq': chain_seq,
                                   'tip': chain_tip[:12], 'cool_paths': len(st['cool'])}, beat=beat)
    st['cap'] = cap['cap_sha'][:12]
    json.dump(st, open(STATE, 'w'), ensure_ascii=False, indent=1)
    return st


def resurrect():
    """一令复活: SI基板态→内核重建。返res dict(含verify+elapsed+restored cool)。"""
    t0 = time.time()
    os.chdir(BASE)
    if BASE not in sys.path: sys.path.insert(0, BASE)
    st = json.load(open(STATE))
    from engine import selfdrive, capsule
    selfdrive.boot(st['beat'], note='KERNEL-SI复活: 死亡后自SI基板重建')
    tok = open(os.path.expanduser('~/.keys/qgl-first-route-token')).read().strip()
    ok, msg = capsule.verify_chain()
    tip, seq = capsule.tail()
    res = {'beat': st['beat'], 'saved_seq': st['chain_seq'], 'now_seq': seq,
           'chain_verify': bool(ok), 'chain_msg': msg, 'seq_monotonic': seq >= st['chain_seq'],
           'cool_restored': st.get('cool', {}), 'token_loaded': bool(tok),
           'contract_sha': st['contract_sha'], 'elapsed_s': round(time.time() - t0, 3),
           'verdict': '证' if (ok and seq >= st['chain_seq'] and tok) else '冲'}
    cap, _, _ = capsule.emit_event('KERNEL-SI-RESURRECT', {k: v for k, v in res.items() if k != 'cool_restored'},
                                   beat=st['beat'])
    res['cap'] = cap['cap_sha'][:12]
    return res
