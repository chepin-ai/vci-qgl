# CAPSULE-OS-01 kernel — 纯QF-OS capsule引擎 v0.1
# 铁律: 无时钟(因果排序=哈希链序) / 纯事件驱动(emit/observe即全部入口) / 非存储转发(响应在调用内闭环或失败)
# 合规职能: 每个事件capsule自动级联一个compliance capsule(OS端streamline, 同调用内)
import json, hashlib, os

CHAIN = "/mnt/agents/output/engine/capsule-chain.jsonl"
V = "capsule/1"

def H(x): return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def tail():
    if not os.path.exists(CHAIN): return None, -1
    lines = open(CHAIN, encoding="utf-8").read().strip().splitlines()
    if not lines: return None, -1
    last = json.loads(lines[-1])
    return last["cap_sha"], last["seq"]

def _mk(kind, body, causal):
    prev, seq = tail()
    cap = {"v": V, "seq": seq + 1, "kind": kind, "prev": prev, "causal": causal, "body": body}
    cap["cap_sha"] = H({k: cap[k] for k in ("v","seq","kind","prev","causal","body")})
    return cap

def _append(cap):
    with open(CHAIN, "a", encoding="utf-8") as f:
        f.write(json.dumps(cap, ensure_ascii=False) + "\n")

# ---- 合规机: 事件触发的streamline自检(无时间量纲, 全部因果/结构判据) ----
def compliance_check(cap):
    findings = []
    b = cap["body"]
    if cap["kind"] == "event":
        if not b.get("evidence"): findings.append("C-NOEVIDENCE: 事件无实证载荷")          # RULE-AUTODRIVE-01
        if "http_status" in b and b["http_status"] in (401, 403): findings.append("C-STOPAUTH: 401/403停手铁律触发")
        if b.get("clock_ref"): findings.append("C-CLOCK: 引用已作废时钟量纲")
        if b.get("queue_ref"): findings.append("C-STOREFWD: 引用存储转发语义")
        # C-GAP: 因果缺口(无时钟合规主判据)——对端链长增长超K而本端零互锚
        gap = b.get("causal_gap")
        if isinstance(gap, int) and gap > 5: findings.append(f"C-GAP: 因果缺口{gap}件超阈5→STALL疑")
        # C-FORK: 同线同prev双子件=equivocation(G-8结构判据)
        if b.get("fork_detected"): findings.append("C-FORK: 检出equivocation分叉件")
        # C-ANCHOR-STD(峰B): 锚四件齐检查——name/evidence/sha-or-ref/因果引用,缺件注记(不阻断)
        miss = []
        if not b.get("name"): miss.append("name")
        ev = b.get("evidence")
        if not ev: miss.append("evidence")
        s = json.dumps(b, ensure_ascii=False)
        if not any(k in s for k in ("sha", "ref", "anchor")): miss.append("sha/ref")
        if not any(k in s for k in ("parent_seq", "trigger", "causal", "prev")): miss.append("causal")
        if miss: findings.append(f"C-ANCHOR-STD: 锚缺件{miss}(劝诫非阻断, 峰B标准化)")
    if cap["kind"] == "incoming":
        if not b.get("verified"): findings.append("C-UNVERIFIED: 来件未过自含验证即处理")
    return {"verdict": "GREEN" if not findings else "RED", "findings": findings,
            "subject": cap["cap_sha"][:12], "subject_seq": cap["seq"]}

def verify_incoming(cap):
    """来件自含验证: 链序自洽 + 摘要自重算。不过即拒(非存储转发: 不挂起, 不排队)。"""
    ok_sha = cap.get("cap_sha") == H({k: cap[k] for k in ("v","seq","kind","prev","causal","body") if k in cap})
    return {"verified": bool(ok_sha and cap.get("v") == V), "reason": None if ok_sha else "sha-mismatch-or-schema"}

# ---- 候触发器(C-FOLD): 事件体含"候"判词 → 自动级联 fold-probe(系统级fold-n发现) ----
# 立法: "候"不再是被动态,而是折叠嫌疑信号;每个候事件必须同调用内触发一次fold-probe
HOU_MARKERS = ("候", "PENDING", "pending", "await", "候排")

HOU_FIELDS = ("state", "verdict", "status", "next")   # v1.1: 只查判词字段,描述性提及不触发(CE-07)

HOU_NEGATIONS = ("不设候", "不候", "非候", "零候", "无候", "禁候", "销候", "候-等废除", "禁裸候", "候项=0")

def _has_hou(body):
    def hit(v):  # v1.2: 否定语境过滤(CE-07族: '不设候'类误判)
        s = HOU_MARKERS and any(m in v for m in HOU_MARKERS)
        return s and not any(n in v for n in HOU_NEGATIONS)
    def walk(x):
        if isinstance(x, dict):
            return any((k in HOU_FIELDS and isinstance(v, str) and hit(v)) or walk(v)
                       for k, v in x.items())
        return False
    return walk(body)

def _fold_probe(parent_cap):
    """fold-probe响应件: 登记该候,要求其下拍前复核(折叠期≤1拍目标)"""
    name = parent_cap["body"].get("name", "?")
    probe = _mk("event", {"name": f"fold-probe:{name}", "target": name,
                          "evidence": {"trigger": "C-FOLD", "parent_seq": parent_cap["seq"],
                                       "law": "候=折叠嫌疑; 复核窗=1拍; 逾期自动升级FINDING"},
                          "auto": True},
                causal=parent_cap["cap_sha"])
    _append(probe)
    return probe

def emit_event(name, evidence, **kw):
    """事件capsule + 自动级联合规capsule + 候触发fold-probe (同调用内streamline闭环)"""
    # ALIGN-138( kernel change, root通告): C-ANCHOR-STD劝诫732RED治理——body级causal+ref锚自动注入(峰B锚四件齐)
    prev_sha = tail()[0]
    if "causal" not in kw and not (isinstance(evidence, dict) and "causal" in evidence):
        kw["causal"] = (prev_sha or "")[:12]
    _ev_s = json.dumps(evidence, ensure_ascii=False) + json.dumps(kw, ensure_ascii=False)
    if not any(k in _ev_s for k in ("sha", "ref", "anchor")):
        kw["prev_ref"] = (prev_sha or "")[:12]
    cap = _mk("event", {"name": name, "evidence": evidence, **kw}, causal=prev_sha)
    _append(cap)
    comp = _mk("compliance", compliance_check(cap), causal=cap["cap_sha"])
    _append(comp)
    probe = _fold_probe(cap) if _has_hou(cap["body"]) else None
    return cap, comp, probe

def observe(incoming):
    """来件 → 验证 → 即时响应capsule。验证失败=拒件响应(不存储、不等待)。"""
    ver = verify_incoming(incoming)
    if not ver["verified"]:
        rej = _mk("reject", {"reason": ver["reason"], "got_sha": str(incoming.get("cap_sha"))[:12]}, causal=tail()[0])
        _append(rej); return rej
    resp = _mk("response", {"to": incoming["cap_sha"][:12], "to_seq": incoming["seq"],
                            "ack": True, "handler": "auto-streamline"}, causal=incoming["cap_sha"])
    _append(resp)
    comp = _mk("compliance", compliance_check(resp), causal=resp["cap_sha"])
    _append(comp)
    return resp, comp

def verify_chain():
    lines = open(CHAIN, encoding="utf-8").read().strip().splitlines()
    prev = None
    for i, l in enumerate(lines):
        c = json.loads(l)
        if c["seq"] != i: return False, f"seq break at {i}"
        if c["prev"] != prev: return False, f"prev break at {i}"
        if c["cap_sha"] != H({k: c[k] for k in ("v","seq","kind","prev","causal","body")}): return False, f"sha break at {i}"
        prev = c["cap_sha"]
    return True, f"OK {len(lines)} capsules"
