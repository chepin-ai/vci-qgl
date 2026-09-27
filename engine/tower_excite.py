"""tower_excite.py — 层-网-塔自激回路 (拍3.63)
律: 塔面(注册表/元律/CE日志)不是静态档案——其失效条款/lag/候项构成常备工作队列,
    自激=塔面扫描自动向信标武装新探针, 无需外部触发。
回路: 层(kernel/链产出工件) → 网(投影广播) → 塔(判词入册,失效条款+lag累积) → 自激扫描 → 信标新武装 → 层(新拍工作)
用法: python3 tower_excite.py scan
"""
import json, os, sys, subprocess

BASE = '/mnt/agents/output'
BEACON_PY = os.path.join(BASE, 'engine/beacon.py')

def scan():
    proposed = []
    # ① 注册表失效条款/lag: lag≥2 的合同 → 武装复测探针
    reg = json.load(open(os.path.join(BASE, 'research/contract-registry.json')))
    for c in reg['contracts']:
        lag = c.get('lag')
        if isinstance(lag, int) and lag >= 2 and c.get('state') == '证':
            proposed.append({
                # TOWER-FIX-98(qfa修方三行·水位差分): 探针id嵌水位lag——lag递增即新针, 静态不重提
                "id": f"RETEST-{c['pat'][:8]}-lag{lag}", "kind": "internal-beat",
                "note": f"合同{c['pat'][:13]} lag={lag}→拍内复测(registry_retest.py)",
                "source": "registry.lag"})
    # ② 元律候项(RESEARCH-LAWS 桥层+候注记)
    # 桥层候 → 周期性自检不是时钟; 以链增长为事件: chain_seq_gt
    sys.path.insert(0, os.path.join(BASE, 'engine'))
    import capsule
    cur_seq = capsule.tail()[1]
    proposed.append({
        "id": "BRIDGE-TWELVE-RETEST", "kind": "chain_seq_gt", "arg": str(cur_seq + 20),
        "note": "桥层候项自检窗: 链+20后再评估十二律↔模式场桥接(承P4失效条款)",
        "source": "laws.bridge"})
    # ③ CE日志跟进件
    ce_lines = open(os.path.join(BASE, 'engine/ce-log.jsonl')).read().strip().splitlines()
    last_ce = json.loads(ce_lines[-1])
    proposed.append({
        "id": f"CE-FOLLOW-{last_ce['id']}", "kind": "chain_seq_gt", "arg": str(cur_seq + 10),
        "note": f"{last_ce['id']}({last_ce['type']})跟进: 修正后指标稳定性复察",
        "source": "ce-log"})
    # ④ 候状态S-I实例的运行证据探针(S-I/4新声)
    # TOWER-FIX-98(水位差分): id嵌当前匹配数——新声出现(计数+1)才成新针, 静态不重提
    # TOWER-CUTOVER-149: 增量游标轨(3拍双轨漂移0证, cap 9ed04f43c287/30998e0b87bd) — 54-92s→~6s; 兜底全扫
    try:
        from engine import tower_cursors as _tc
        _found, _st = _tc.scan_awake_incr()
        n_awake = len(_found)
    except Exception:
        import glob as _glob
        n_awake = len(_glob.glob(os.path.join(BASE, '**/awake*.log'), recursive=True))
    proposed.append({
        "id": f"SI4-new-voice-n{n_awake}", "kind": "glob_exists", "arg": "**/awake*.log",
        "note": "S-I/4 awake链新声出现→验证链活+FD-SI4-01/02升级轨",
        "source": "si4-pack"})
    return proposed, cur_seq

DONE_FILE = os.path.join(BASE, 'engine/tower_done.json')

def load_done():
    """CE-14: 自激环路记账——已结案探针不得重武装(拍3.70/3.71: scan重武装BRIDGE/CE-11双结案件被捕获)"""
    if os.path.exists(DONE_FILE):
        return set(json.load(open(DONE_FILE)))
    return set()

def mark_done(probe_id):
    d = sorted(load_done() | {probe_id})
    json.dump(d, open(DONE_FILE, 'w'), ensure_ascii=False, indent=1)

def arm_all(proposed):
    done_set = load_done()
    # TOWER-FIX-98(防重传感): 同kind+arg已武装者不重复武装(水位id换代时旧针仍是在役传感器)
    try:
        _b = json.load(open(os.path.join(BASE, 'app/public/qgl-beacon.json')))
        armed_args = set()
        for e in _b.get('armed_events', []):
            pr = e.get('probe', {})
            for k in ('pattern', 'path', 'needle', 'seq'):
                if k in pr: armed_args.add(str(pr[k]))
    except Exception:
        armed_args = set()
    done = []
    for p in proposed:
        if p['id'] in done_set:
            done.append(f"skip(done): {p['id']}")
            continue
        if p.get('arg') and str(p.get('arg')) in armed_args:
            done.append(f"skip(already-armed): {p['id']}")
            continue
        if p['kind'] == 'chain_seq_gt':
            r = subprocess.run(['python3', BEACON_PY, 'arm', p['id'], 'chain_seq_gt', p['arg'], p['note']],
                               capture_output=True, text=True)
        elif p['kind'] == 'glob_exists':
            r = subprocess.run(['python3', BEACON_PY, 'arm', p['id'], 'glob_exists', p['arg'], p['note']],
                               capture_output=True, text=True)
        else:
            # internal-beat: 不入信标探针, 入候件队列字段
            b = json.load(open(os.path.join(BASE, 'app/public/qgl-beacon.json')))
            b.setdefault('beat_queue', []).append({"id": p['id'], "note": p['note'], "source": p['source']})
            b['beacon_seq'] += 1
            json.dump(b, open(os.path.join(BASE, 'app/public/qgl-beacon.json'), 'w'), ensure_ascii=False, indent=1)
            r = type('x', (), {'stdout': f"queued: {p['id']}"})()
        done.append(r.stdout.strip())
    return done

if __name__ == '__main__':
    proposed, seq = scan()
    print(f"塔面扫描 @链{seq}: 提名 {len(proposed)} 件")
    for p in proposed: print(f"  [{p['source']}] {p['id']} ({p['kind']})")
    done = arm_all(proposed)
    for d in done: print(" ", d)
