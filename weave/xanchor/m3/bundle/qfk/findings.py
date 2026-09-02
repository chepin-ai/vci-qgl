"""qfk.findings — 残差引擎（I1 主循环）。

对应洞察 I1「残差不是异常，是主燃料」：五域（chain/circle/field/tensor/trans）
的残差是同一类对象——期望失配流；本模块是其生产→分类→路由→消解→入链留证
的闭环。残差 schema 采 SHACL ValidationReport 化（对应深研件
qf-know_dim05.md §3：W3C 标准词表可机判）：{type, focus, severity, constraint,
detail, tick}，severity ∈ info/warn/breaking，breaking 打人工闸标记。
入链 domain="finding"，非零残差即入队并入链（硬约束 3）——链是残差留证机。
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from .chain import Chain, Entry, canon

SEVERITIES = ("info", "warn", "breaking")
# 六域同 schema（v0.2 追加 "mutual-proof"：ipmp 三机互证域，见 ipmp.py）
DOMAINS = ("chain", "circle", "field", "tensor", "trans", "mutual-proof")
MAX_RESOLVE_ROUNDS = 3  # ≤3 轮注记（规格钉死）

# 类型×严重度分类表：未登记类型按给定 severity 原样放行（开放世界）
CLASSIFY_MAP = {
    "drift": "warn",
    "tensor_residual": "warn",
    "t4_gate_fail": "breaking",
    "proof_tier_unavailable": "info",
    "north_star_qubo": "info",
    "write_gate_denied": "warn",
    "chain_tamper": "breaking",
    # v0.2 ipmp 域（F-1）：串谋探针/绑定失配/重放失配=breaking；类闸门=warn；无 gap=info
    "collusion_suspect": "breaking",
    "proposition_class_rejected": "warn",
    "binding_mismatch": "breaking",
    "replay_mismatch": "breaking",
    "gap_unknown": "info",
}

_ids = itertools.count()


def make_residual(type: str, focus: str, severity: str, constraint: str,
                  detail: str, tick: int | None) -> dict:
    """五域共用残差 schema（SHACL 化）。"""
    if severity not in SEVERITIES:
        raise ValueError(f"severity 须 ∈ {SEVERITIES}")
    return {"type": type, "focus": focus, "severity": severity,
            "constraint": constraint, "detail": detail, "tick": tick}


@dataclass
class Finding:
    id: int
    type: str
    focus: str
    severity: str
    constraint: str
    detail: str
    tick: int | None
    domain: str
    status: str = "open"          # open → routed → resolved → committed
    routed_to: str = ""           # auto | human
    human_gate: bool = False      # severity≥breaking → 人工闸标记
    annotations: list[str] = field(default_factory=list)
    committed_seq: int | None = None

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in
                ("id", "type", "focus", "severity", "constraint", "detail",
                 "tick", "domain", "status", "routed_to", "human_gate",
                 "annotations", "committed_seq")}


class FindingEngine:
    """produce→classify→route→resolve→commit 主循环（I1）。"""

    def __init__(self):
        self.queue: list[Finding] = []

    # 生产+分类
    def produce(self, residual: dict, domain: str) -> Finding:
        if domain not in DOMAINS:
            raise ValueError(f"domain 须 ∈ {DOMAINS}")
        sev = CLASSIFY_MAP.get(residual["type"], residual["severity"])
        # classify：登记类型以分类表为准（type×severity），未登记者信任产出方
        f = Finding(id=next(_ids), type=residual["type"], focus=residual["focus"],
                    severity=sev, constraint=residual["constraint"],
                    detail=residual["detail"], tick=residual["tick"], domain=domain)
        self.route(f)
        self.queue.append(f)
        return f

    # 路由：severity≥breaking → 人工闸
    def route(self, f: Finding) -> None:
        f.human_gate = f.severity == "breaking"
        f.routed_to = "human" if f.human_gate else "auto"
        f.status = "routed"

    # 消解：≤3 轮注记
    def resolve(self, fid: int, note: str) -> Finding:
        f = self._get(fid)
        if f.status == "committed":
            raise RuntimeError("已入链的 finding 不可再注记")
        if len(f.annotations) >= MAX_RESOLVE_ROUNDS:
            raise RuntimeError(f"注记轮次超上限 {MAX_RESOLVE_ROUNDS}")
        f.annotations.append(note)
        if len(f.annotations) == MAX_RESOLVE_ROUNDS or note.rstrip().endswith("[resolved]"):
            f.status = "resolved"
        return f

    # 反哺留证：入链 domain="finding"
    def commit(self, chain: Chain, fid: int) -> Entry:
        f = self._get(fid)
        if f.committed_seq is not None:
            raise RuntimeError("finding 已入链")
        e = chain.append("finding", canon(f.to_dict()))
        f.committed_seq = e.seq
        f.status = "committed"
        return e

    def commit_all(self, chain: Chain) -> list[Entry]:
        return [self.commit(chain, f.id) for f in self.queue if f.committed_seq is None]

    def open_findings(self) -> list[Finding]:
        return [f for f in self.queue if f.status in ("open", "routed")]

    def _get(self, fid: int) -> Finding:
        for f in self.queue:
            if f.id == fid:
                return f
        raise KeyError(f"finding {fid} 不存在")
