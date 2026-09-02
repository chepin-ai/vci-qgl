"""qfk.ipmp — 三机 MIP（无星）互证协议（v0.2 第八模块）。

判词（全文贯彻，不升格）：本模块实现的协议是 **MIP（无星）+ 绑定承诺互锚 +
信标挑战** 的结构同构工程构造，不是字面 MIP*——**MIP 无星结构同构不升格**。
一切 soundness 陈述只覆盖 A 档 1–6 的诚实上界；纠缠编译档命题由 A2 类闸门
整体移出本协议；硬件 Bell 数字永不入本模块的验证路径。
【合理推断（映射）/已证（封顶纪律）】

六相位状态机（迁移表见设计件 ipc-ipmp-design-01.md §1.2）：
  COMMIT → CHALLENGE → WINDOW → RESPOND → JUDGE → SETTLE → 终态（只读，可 replay）

四档标注纪律：sha256 绑定/Ed25519/m-of-n/Merkle=【已证（原语）】；三机角色映射、
探针有效方向=【合理推断】；TEE 升级路径=【猜想】；可信时戳、探针完备性、
软件隔离强度、灰区#10（NP 双帽）=【未闭合】。
@gray (a) 无通信窗口的时序强制是纪律级（M1 时间锁半边，本地时钟可伪造，
仅靠 m6 入链 seq 序做事后佐证）；(b) 串谋探针是审计启发式非完备检测
（M-probe：命中=违规证据，未命中≠清白）；(c) NP 双帽风险无形式化消解
（灰区#10，本模块只提供角色轮换接口 judge_rotation/judge_set_for，不声称闭合）。
硬约束继承：纯 Python≥3.11；依赖仅 numpy+cryptography；承诺/哈希全 256-bit；
12-hex 别名永不入验证路径；测试零网络（挑战走 beacon 离线 classical-sim 源，
熵档如实快照进 verdict）。B 档 7–9（物理纠缠模块/DI 认证闭合/硬件实证封顶）
本模块不触及、不预留假接口。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from . import circle as _circle
from .beacon import Beacon, BeaconTick, leader_draw  # noqa: F401  (§1.5 调用面)
from .chain import Chain, Entry, canon, sha256, _require_32b
from .circle import Policy
from .findings import FindingEngine, make_residual
from .tensor import tn_residual  # noqa: F401  (score 语义见 judge_verdict)

DOMAIN_IPMP = "mutual-proof"  # 链 domain 恒为此（钉死）

PROPOSITION_CLASSES = ("np-witness", "pcp-compiled")  # A2：仅此两类可入协议
VERDICT_VALUES = ("ACCEPT", "REJECT", "GAP_UNKNOWN")
ROLES = ("P1", "P2")  # P1=IP机（命题方），P2=NP机（独立重算方）
PHASES = ("COMMIT", "CHALLENGE", "WINDOW", "RESPOND", "JUDGE", "SETTLE")

# A1：人读数值声明字符串，随 m1 入链，永不升格为定理、永不入验证路径
COMPLETENESS_STMT = "honest-both-accept-in-intersection"
SOUNDNESS_STMT = "reject-unless-residual<=tol AND gap explicit"
# 判词照录：结构同构不升格（随 m6 入链）
STRUCTURAL_NOTE = ("MIP（无星）+绑定承诺互锚+信标挑战 的结构同构工程构造，"
                   "非字面 MIP*；MIP 无星结构同构不升格。")
# A5：熵档声明固定串（随 m6 入链）
ENTROPY_DISCLAIMER = ("classical-sim 档活在复杂度假设内：熵源未经物理认证，"
                      "仅作公开可复现挑战；certified 档亦仅声称源组成如实，"
                      "不升格为 DI 级认证。")


class PhaseError(RuntimeError):
    """非法相位迁移（无静默降级）。"""


class WindowLockedError(RuntimeError):
    """窗口内 reveal / 窗口外补交。"""


class BindingError(RuntimeError):
    """reveal 与 commitment 绑定失配。"""


class ClassGateError(ValueError):
    """命题类闸门拒绝（A2）。"""


class SelfJudgeError(PermissionError):
    """裁定者自证禁止（灰区#10：宁停不让自证）。"""


# ---------------------------------------------------------------- dataclass

@dataclass
class MachineSpec:
    """A1：三机形式化为交互机器。spec 仅作声明与裁定集校验，永不作 soundness 证据。"""
    name: str               # "ip-machine" | "np-machine" | "n-machine"
    role: str               # "prover_unbounded" | "verifier_polytime_prover" | "randomness_source"
    power_bound: str        # 人读声明
    honesty_assumption: str  # 人读声明；永不入验证路径

    def to_dict(self) -> dict:
        return {"name": self.name, "role": self.role,
                "power_bound": self.power_bound,
                "honesty_assumption": self.honesty_assumption}


_MACHINE_SPECS = {
    "ip-machine": MachineSpec(
        "ip-machine", "prover_unbounded",
        "unbounded-search, untrusted-honesty",
        "honest prover follows the protocol (assumption, never verified)"),
    "np-machine": MachineSpec(
        "np-machine", "verifier_polytime_prover",
        "polytime-recompute, independent",
        "independent recomputation not colluding (assumption, never verified)"),
    "n-machine": MachineSpec(
        "n-machine", "randomness_source",
        "public-beacon, no-compute",
        "beacon entropy is public and unpredictable (assumption, never verified)"),
}


def machine_spec(name: str) -> MachineSpec:
    """A1：返回三机之一的规格卡；name 未知抛 KeyError。

    spec 仅作声明与裁定集校验，永不作 soundness 证据。
    """
    if name not in _MACHINE_SPECS:
        raise KeyError(f"未知机器 {name!r}；合法名：{sorted(_MACHINE_SPECS)}")
    return _MACHINE_SPECS[name]


@dataclass
class PropositionCommit:
    """m1：命题承诺（承诺先于挑战）。"""
    pid: str
    proposer: str
    claim_hash: bytes          # 32B = sha256(canon(claim))
    claim_class: str           # ∈ PROPOSITION_CLASSES
    witness_ref: str           # field 键 "ipmp:<pid>:witness" 或外部引用
    gap: Optional[float]       # 显式 soundness gap；None ⟹ 永不可 ACCEPT
    geodesic_req: dict         # 测地定位请求（候选 B：承诺图最短验证路径）
    resp_fn_hash: bytes        # 32B，机制 M3：应答函数预承诺
    chain_seq: int             # m1 entry seq
    ts: float

    def to_dict(self) -> dict:
        return {"pid": self.pid, "proposer": self.proposer,
                "claim_hash": self.claim_hash.hex(),
                "claim_class": self.claim_class,
                "witness_ref": self.witness_ref, "gap": self.gap,
                "geodesic_req": self.geodesic_req,
                "resp_fn_hash": self.resp_fn_hash.hex(),
                "chain_seq": self.chain_seq, "ts": self.ts}


@dataclass
class Challenge:
    """m2：信标挑战。"""
    tick_seq: int
    qrand: bytes               # 32B，beacon.BeaconTick.qrand
    tick_hash: bytes           # 32B，beacon.BeaconTick.hash
    entropy_grade: str         # "certified" | "classical-sim"（A5 快照）

    def to_dict(self) -> dict:
        return {"tick_seq": self.tick_seq, "qrand": self.qrand.hex(),
                "tick_hash": self.tick_hash.hex(),
                "entropy_grade": self.entropy_grade}


def binding_digest(role: str, payload: bytes, salt: bytes, window_seq: int) -> bytes:
    """m3 绑定承诺的规范式（M1）：sha256(canon({payload,salt,role,window_seq}))。

    window_seq==challenge.tick_seq 使承诺绑定到本拍挑战——任何「看到对方应答后
    再凑」的行为须破 sha256 原像/碰撞【已证（原语）】。测试与实现共用本函数，
    无测试专用后门。
    """
    return sha256(canon({"payload": bytes(payload).hex(), "salt": bytes(salt).hex(),
                         "role": role, "window_seq": window_seq}))


@dataclass
class ResponseCommitment:
    """m3a/m3b 的 commit 半段（机制 M1）。"""
    role: str                  # ∈ ROLES
    resp_hash: bytes           # 32B = binding_digest(role, payload, salt, window_seq)
    window_seq: int            # == challenge.tick_seq
    ts: float

    def to_dict(self) -> dict:
        return {"role": self.role, "resp_hash": self.resp_hash.hex(),
                "window_seq": self.window_seq, "ts": self.ts}


@dataclass
class ResponseReveal:
    """m3a/m3b 的 reveal 半段。"""
    role: str
    payload: bytes             # r₁=Resp(p,q,见证) / r₂=独立重算结果
    salt: bytes                # 32B
    ts: float

    def binding_digest(self, window_seq: int) -> bytes:
        """重算 resp_hash 供核验（window_seq 由会话注入，见模块级 binding_digest）。"""
        return binding_digest(self.role, self.payload, self.salt, window_seq)

    def to_dict(self) -> dict:
        return {"role": self.role, "payload": self.payload.hex(),
                "salt": self.salt.hex(), "ts": self.ts}


@dataclass
class Verdict:
    """m5：裁定（共签对象）。"""
    value: str                       # ∈ VERDICT_VALUES
    residual_score: Optional[float]  # tn_residual 的 score；GAP_UNKNOWN 时可为 None
    gap: Optional[float]
    entropy_grade: str               # 从 Challenge 继承（A5）
    replay_seed: str                 # challenge.tick_hash.hex()（A6 争议重放种子）
    judge_set: tuple                 # 本场裁定集公钥（角色轮换后的有效集）

    def _canon_body(self) -> dict:
        return {"value": self.value, "residual_score": self.residual_score,
                "gap": self.gap, "entropy_grade": self.entropy_grade,
                "replay_seed": self.replay_seed,
                "judge_set": [p.hex() for p in self.judge_set]}

    def digest(self) -> bytes:
        """32B = sha256(VERDICT_TAG‖canon(...))，共签对象。"""
        return sha256(_circle.VERDICT_TAG + canon(self._canon_body()))

    def to_dict(self) -> dict:
        d = self._canon_body()
        d["digest"] = self.digest().hex()
        return d


@dataclass
class WindowPolicy:
    """无通信窗口配置（§3 三机制的参数面）。

    强度如实标注：M1 绑定=密码学级、时序=纪律级；M2 审计=纪律级；
    M3 代码绑定=密码学级、重放忠实=纪律级。三者叠加后的联合强度仍标
    【纪律级主体 + 密码学级绑定件】，不写成「密码学级窗口」。
    """
    phase_n: int                                  # 点火律 seq%phase_n==phase_p
    phase_p: int
    require_both_commitments: bool = True         # M1 钉死默认真
    max_commit_skew_s: float = 5.0                # 双 commit 最大时序偏斜（纪律级）
    audit_hook: Optional[callable] = None         # M2 信道审计钩 callable(event, pid, payload)
    collusion_detector: Optional[callable] = None  # M-probe 串谋探针 injectable


# ---------------------------------------------------------------- 纯函数

def judge_verdict(claim_hash: bytes, qrand: bytes, r1: bytes, r2: bytes,
                  gap: Optional[float], eps: float = 1e-3, tol: float = 1.0
                  ) -> tuple:
    """A6 核心：裁定规则确定化的纯函数（无副作用、无时钟读取）。

    同一 (claim_hash,qrand,r1,r2,gap) 必得同一结果。规则钉死（顺序即优先级）：
      1) gap is None      → ("GAP_UNKNOWN", None)   # A3：无 gap 永不 ACCEPT
      2) tn_residual 超阈 → ("REJECT", score)       # m4：score>tol
      3) 阈内且 gap 显式  → ("ACCEPT", score)
    score 复用 tensor.tn_residual 的 ‖Fa−Fb‖/(√d·ε)；r1/r2 → Fa/Fb 的反序列化
    约定为 np.frombuffer(payload, dtype=float64)，长度不等或不可反序列化即
    ("REJECT", None)（findings 由调用方 IPMPSession.judge 产出，本函数保持纯）。
    """
    if gap is None:
        return ("GAP_UNKNOWN", None)  # A3：无 gap 永不 ACCEPT（钉死短路）
    try:
        fa = np.frombuffer(r1, dtype=np.float64)
        fb = np.frombuffer(r2, dtype=np.float64)
    except (ValueError, TypeError):
        return ("REJECT", None)
    if fa.size == 0 or fa.shape != fb.shape:
        return ("REJECT", None)
    d = fa.size
    score = float(np.linalg.norm(fa - fb) / (np.sqrt(d) * eps))  # tn_residual 语义
    if score > tol:
        return ("REJECT", score)
    return ("ACCEPT", score)


def collusion_probe(r1: bytes, r2: bytes,
                    detector: Optional[callable] = None) -> Optional[dict]:
    """M-probe：Bell 不等式的三机合法对应物——只作审计探针，不证非局域关联。

    默认检测器：r2 内含 sha256(r1) 前缀/后缀、或 r1==r2 逐字节相同（独立重算
    概率≈0）→ 命中产 make_residual("collusion_suspect", ..., "breaking", ...)。
    detector 可注入更强统计检测（签名同默认：callable(r1, r2) -> Optional[dict]）。
    探针只有单向含义：命中=违规证据；未命中≠清白。
    【合理推断（探针有效方向）/未闭合（完备性）：漏报不构成协议缺陷，如实标注】
    """
    if detector is not None:
        return detector(r1, r2)
    h = sha256(r1)
    hit = (r1 == r2) or r2.startswith(h) or r2.endswith(h)
    if not hit:
        return None
    if r1 == r2:
        detail = "r1==r2 逐字节相同（独立重算概率≈0）"
    else:
        detail = "r2 内嵌 sha256(r1) 前缀/后缀（应答含对方承诺指纹）"
    return make_residual("collusion_suspect", "mutual-proof.window", "breaking",
                         "independent-response", detail, None)


# ---------------------------------------------------------------- 会话

class IPMPSession:
    """一轮互证（六消息流）的状态机载体。所有跨相位调用经 _require_phase 守卫。"""

    def __init__(self, engine: "IPMPEngine", pid: str):
        self.engine = engine
        self.pid = pid
        self._phase = "COMMIT"
        self.settled = False
        self.commit: Optional[PropositionCommit] = None
        self.challenge: Optional[Challenge] = None
        self._tick: Optional[BeaconTick] = None
        self.commitments: dict = {}   # role -> ResponseCommitment
        self.reveals: dict = {}       # role -> ResponseReveal
        self.verdict: Optional[Verdict] = None
        self.m6_entry: Optional[Entry] = None

    @property
    def phase(self) -> str:
        return self._phase

    def _require_phase(self, *phases: str) -> None:
        if self._phase not in phases:
            raise PhaseError(
                f"session {self.pid} 当前相位 {self._phase}，本操作要求 ∈ {phases}")

    def _audit(self, event: str, payload: dict) -> None:
        hook = self.engine.window.audit_hook
        if hook is not None:
            hook(event, self.pid, payload)

    # ---- m1（COMMIT→CHALLENGE）----
    def commit_proposition(self, claim: bytes, *, claim_class: str, witness_ref: str,
                           gap: Optional[float], geodesic_req: dict,
                           resp_fn_hash: bytes,
                           proposer: str = "ip-machine") -> PropositionCommit:
        self._require_phase("COMMIT")
        # A2 类闸门：纠缠编译档整体移出本协议（会话停在 COMMIT）
        if claim_class not in PROPOSITION_CLASSES:
            self.engine.findings.produce(make_residual(
                "proposition_class_rejected", f"mutual-proof:{self.pid}", "warn",
                "claim_class∈PROPOSITION_CLASSES",
                f"claim_class={claim_class!r} 被拒（A2：纠缠编译档移出本协议）",
                None), DOMAIN_IPMP)
            raise ClassGateError(
                f"claim_class 须 ∈ {PROPOSITION_CLASSES}，得 {claim_class!r}")
        _require_32b(resp_fn_hash, "resp_fn_hash")
        spec = machine_spec(proposer)  # 未知机器名 → KeyError（A1）
        # 前置条件：proposer ∉ 本场裁定集（剔除后无人可裁 → 宁停不让自证）
        if not self.engine._eligible_judges(proposer):
            raise SelfJudgeError(
                f"proposer={proposer!r} 剔除后裁定集为空（灰区#10：宁停不让自证）")
        claim_hash = sha256(canon(claim.decode("utf-8")))
        payload = canon({
            "type": "m1-proposition",
            "pid": self.pid, "proposer": proposer,
            "claim_hash": claim_hash.hex(), "claim_class": claim_class,
            "witness_ref": witness_ref, "gap": gap,
            "geodesic_req": geodesic_req, "resp_fn_hash": resp_fn_hash.hex(),
            "machine": spec.to_dict(),  # honesty_assumption 人读声明随 m1 入链，永不入验证路径
            "completeness_stmt": COMPLETENESS_STMT,
            "soundness_stmt": SOUNDNESS_STMT,
            "structural_note": STRUCTURAL_NOTE,
        })
        e = self.engine.chain.append(DOMAIN_IPMP, payload)
        self.commit = PropositionCommit(
            pid=self.pid, proposer=proposer, claim_hash=claim_hash,
            claim_class=claim_class, witness_ref=witness_ref, gap=gap,
            geodesic_req=geodesic_req, resp_fn_hash=bytes(resp_fn_hash),
            chain_seq=e.seq, ts=e.ts)
        self._phase = "CHALLENGE"
        return self.commit

    # ---- m2（CHALLENGE→WINDOW）----
    def open_challenge(self) -> Challenge:
        self._require_phase("CHALLENGE")
        w = self.engine.window
        if not self.engine.beacon.phase(w.phase_n, w.phase_p):
            raise PhaseError(  # 点火律未燃：调用方等下一拍，无静默降级
                f"beacon 相位未点火（seq%{w.phase_n}!={w.phase_p}）")
        tick = self.engine.beacon.tick()
        grade = self.engine.beacon.entropy_grade()  # A5：熵档快照
        self._tick = tick
        self.challenge = Challenge(tick_seq=tick.seq, qrand=tick.qrand,
                                   tick_hash=tick.hash, entropy_grade=grade)
        self.engine.chain.append(DOMAIN_IPMP, canon({  # m2 摘要入链
            "type": "m2-challenge", "pid": self.pid,
            **self.challenge.to_dict()}))
        self.engine.chain.anchor_beacon(tick.hash.hex())  # 熵锚待挂下一 checkpoint
        self._audit("challenge", {"tick_seq": tick.seq, "entropy_grade": grade})
        self._phase = "WINDOW"
        return self.challenge

    # ---- m3 commit 半段（WINDOW；双角色齐→RESPOND）----
    def submit_commitment(self, role: str, resp_hash: bytes, ts: float
                          ) -> ResponseCommitment:
        self._require_phase("WINDOW")
        if role not in ROLES:
            raise ValueError(f"role 须 ∈ {ROLES}，得 {role!r}")
        _require_32b(resp_hash, "resp_hash")
        if role in self.commitments:
            raise PhaseError(f"角色 {role} 已提交承诺（每角色恰一条）")
        c = ResponseCommitment(role=role, resp_hash=bytes(resp_hash),
                               window_seq=self.challenge.tick_seq, ts=ts)
        self.commitments[role] = c
        self._audit("commit", {"role": role, "window_seq": c.window_seq, "ts": ts})
        # 纪律级时序：双 commit 偏斜超阈 → 残差流（本地时钟可伪造，仅事后佐证）
        if len(self.commitments) == 2:
            ts_pair = [c.ts for c in self.commitments.values()]
            skew = abs(ts_pair[0] - ts_pair[1])
            if skew > self.engine.window.max_commit_skew_s:
                self.engine.findings.produce(make_residual(
                    "commit_skew_exceeded", f"mutual-proof:{self.pid}", "warn",
                    f"max_commit_skew_s<={self.engine.window.max_commit_skew_s}",
                    f"双 commit 偏斜 {skew:.3f}s 超阈（纪律级，@gray 可信时戳未闭合）",
                    self.challenge.tick_seq), DOMAIN_IPMP)
        if len(self.commitments) == 2 or not self.engine.window.require_both_commitments:
            self._phase = "RESPOND"
        return c

    # ---- m3 reveal 半段（RESPOND；绑定核验，双齐→JUDGE）----
    def reveal(self, role: str, payload: bytes, salt: bytes, ts: float
               ) -> ResponseReveal:
        if self._phase == "WINDOW":
            raise WindowLockedError(  # M1：窗口未关闭禁止 reveal
                f"session {self.pid} 窗口未关闭（双 commit 未齐），禁止 reveal")
        self._require_phase("RESPOND")
        if role not in self.commitments:
            raise PhaseError(f"角色 {role} 无窗口承诺，不得 reveal")
        if role in self.reveals:
            raise PhaseError(f"角色 {role} 已 reveal（每角色恰一条）")
        rv = ResponseReveal(role=role, payload=bytes(payload),
                            salt=bytes(salt), ts=ts)
        want = self.commitments[role].resp_hash
        got = rv.binding_digest(self.challenge.tick_seq)
        if got != want:  # 绑定失配（含 window_seq≠tick_seq 的错窗承诺）
            self.engine.findings.produce(make_residual(
                "binding_mismatch", f"mutual-proof:{self.pid}:{role}", "breaking",
                "sha256(canon({payload,salt,role,window_seq}))==resp_hash",
                f"reveal 重算 {got.hex()[:16]}… ≠ commit {want.hex()[:16]}…",
                self.challenge.tick_seq), DOMAIN_IPMP)
            raise BindingError(
                f"角色 {role} reveal 与 commitment 绑定失配（会话不得进 JUDGE）")
        self.reveals[role] = rv
        self._audit("reveal", {"role": role, "ts": ts})
        if len(self.reveals) == 2:
            self._phase = "JUDGE"
        return rv

    # ---- m4+m5（JUDGE→SETTLE）：内部调 judge_verdict + collusion_probe ----
    def judge(self) -> Verdict:
        self._require_phase("JUDGE")
        r1 = self.reveals["P1"].payload
        r2 = self.reveals["P2"].payload
        # M-probe 先行：命中即 breaking 留证，且 verdict 永不得 ACCEPT
        hit = collusion_probe(r1, r2, self.engine.window.collusion_detector)
        if hit is not None:
            hit["tick"] = self.challenge.tick_seq
            self.engine.findings.produce(hit, DOMAIN_IPMP)
        value, score = judge_verdict(self.commit.claim_hash, self.challenge.qrand,
                                     r1, r2, self.commit.gap)
        if hit is not None and value == "ACCEPT":
            value = "REJECT"  # 探针命中压哨：裁定不得 ACCEPT（score 保留供审计）
        if hit is None:  # 探针未命中时，REJECT/GAP_UNKNOWN 预产 findings（迁移表钉死）
            if value == "REJECT":
                self.engine.findings.produce(make_residual(
                    "tensor_residual", f"mutual-proof:{self.pid}", "warn",
                    "score<=sqrt(d)*eps",
                    f"residual_score={score} 超阈或应答不可比对（m4）",
                    self.challenge.tick_seq), DOMAIN_IPMP)
            elif value == "GAP_UNKNOWN":
                self.engine.findings.produce(make_residual(
                    "gap_unknown", f"mutual-proof:{self.pid}", "info",
                    "gap explicit required",
                    "gap=None：A3 钉死无 gap 永不 ACCEPT", self.challenge.tick_seq),
                    DOMAIN_IPMP)
        judge_set = self.engine.judge_set_for(self.commit.proposer, self._tick)
        self.verdict = Verdict(value=value, residual_score=score,
                               gap=self.commit.gap,
                               entropy_grade=self.challenge.entropy_grade,
                               replay_seed=self.challenge.tick_hash.hex(),
                               judge_set=judge_set)
        self._phase = "SETTLE"
        return self.verdict

    # ---- m6（SETTLE→终态）：共签核验 + 入链 + findings 分流 ----
    def settle(self, sigs: dict) -> Entry:
        self._require_phase("SETTLE")
        if self.settled:
            raise PhaseError(f"session {self.pid} 已终态（只读，可 replay）")
        policy = _circle.effective_policy(self.engine.chain, self.engine.policy)
        # 仅本场裁定集成员的签名计票（角色轮换后的有效集）
        pool = {p: s for p, s in sigs.items() if p in self.verdict.judge_set}
        if not _circle.verify_verdict(self.verdict.digest(), pool, policy):
            raise PhaseError(  # 共签不足/非成员：m6 不入链，相位停留可补签重试
                f"verdict 共签未达 m-of-n（计票签名 {len(pool)} 份）")
        kappa_chain = self.engine.chain.head.hex()  # 互锚承诺快照（m6 入链前）
        kappa_field = (self.engine.field.root().hex()
                       if getattr(self.engine, "field", None) is not None else None)
        payload = canon({
            "type": "m6-settle", "pid": self.pid,
            "verdict": self.verdict.to_dict(),
            "qrand": self.challenge.qrand.hex(),
            "kappa_chain": kappa_chain, "kappa_field": kappa_field,  # 双 κ
            "entropy_grade": self.verdict.entropy_grade,
            "entropy_disclaimer": ENTROPY_DISCLAIMER,  # A5 固定串
            "replay_seed": self.verdict.replay_seed,
            "sigs": {p.hex(): s.hex() for p, s in pool.items()},
            "record": self.record(),
            "structural_note": STRUCTURAL_NOTE,  # 判词照录入链
        })
        self.m6_entry = self.engine.chain.append(DOMAIN_IPMP, payload)
        self.engine.findings.commit_all(self.engine.chain)  # 残差分流留证
        self.settled = True  # 终态：session 只读，可 replay
        return self.m6_entry

    def record(self) -> dict:
        """导出全量会话记录（m1..m6 的 to_dict 拼接），供 replay 与链上 m6 payload。"""
        return {
            "pid": self.pid, "domain": DOMAIN_IPMP,
            "m1": self.commit.to_dict() if self.commit else None,
            "m2": self.challenge.to_dict() if self.challenge else None,
            "m3_commit": {r: c.to_dict() for r, c in self.commitments.items()},
            "m3_reveal": {r: v.to_dict() for r, v in self.reveals.items()},
            "m5": self.verdict.to_dict() if self.verdict else None,
            "m6": self.m6_entry.to_dict() if self.m6_entry else None,
            "structural_note": STRUCTURAL_NOTE,
        }


# ---------------------------------------------------------------- 引擎

class IPMPEngine:
    """会话注册表 + 七模块调用面的唯一汇聚点。"""

    def __init__(self, chain: Chain, beacon: Beacon, policy: Policy,
                 findings: FindingEngine, window: WindowPolicy,
                 judge_rotation: Optional[dict] = None):
        self.chain = chain
        self.beacon = beacon
        self.policy = policy
        self.findings = findings
        self.window = window
        self.judge_rotation = judge_rotation or {}
        self.sessions: dict = {}
        self.machine_keys: dict = {}  # 机器名 → 其持有的公钥集（裁定剔除用）
        self.field = None             # 可选臂：Field 实例，κ=Field.root() 互锚快照

    def register_machine(self, name: str, pubs: tuple) -> None:
        """A1 密钥面：登记机器持有的公钥（judge_set_for 剔除 proposer 密钥用）。"""
        machine_spec(name)  # 未知名 → KeyError
        self.machine_keys[name] = tuple(pubs)

    def open_session(self, pid: str) -> IPMPSession:
        if pid in self.sessions:
            raise ValueError(f"pid {pid!r} 已存在（会话唯一键）")
        s = IPMPSession(self, pid)
        self.sessions[pid] = s
        return s

    def _eligible_judges(self, proposer: str) -> list:
        """policy.members 剔除 proposer 所属密钥后的可裁集合。"""
        own = set(self.machine_keys.get(proposer, ()))
        return [m for m in self.policy.members if m not in own]

    def judge_set_for(self, proposer: str, tick: BeaconTick) -> tuple:
        """灰区#10 的角色轮换接口：judge_rotation 显式映射优先；缺省从
        policy.members 剔除 proposer 所属密钥后按 leader_draw 同式打分确定性排序。
        若剔除后无人可裁 → SelfJudgeError（宁停不让自证）。
        本接口只实装轮换，不声称消解 NP 双帽风险（@gray #10 未闭合）。
        """
        if proposer in self.judge_rotation:
            return tuple(self.judge_rotation[proposer])
        candidates = self._eligible_judges(proposer)
        if not candidates:
            raise SelfJudgeError(
                f"proposer={proposer!r} 剔除后裁定集为空（灰区#10：宁停不让自证）")
        # leader_draw 同式打分（sha256(tick.qrand‖member)）的确定性全排序
        ranked = sorted(candidates,
                        key=lambda p: (sha256(tick.qrand + p.hex().encode()), p.hex()))
        return tuple(ranked)

    def replay(self, record: dict) -> Verdict:
        """A6：L3 争议重放。从 record 重取 (claim_hash,qrand,r1,r2,gap)，重跑
        judge_verdict（含 M-probe 压哨语义）与原 verdict 比对；不一致 →
        findings("replay_mismatch", breaking) 且抛 BindingError。
        种子=record["m2"]["tick_hash"]（可复现锚）。
        """
        m1, m2, m5 = record["m1"], record["m2"], record["m5"]
        r1 = bytes.fromhex(record["m3_reveal"]["P1"]["payload"])
        r2 = bytes.fromhex(record["m3_reveal"]["P2"]["payload"])
        value, score = judge_verdict(bytes.fromhex(m1["claim_hash"]),
                                     bytes.fromhex(m2["qrand"]),
                                     r1, r2, m1["gap"])
        if collusion_probe(r1, r2) is not None and value == "ACCEPT":
            value = "REJECT"  # 与原 judge() 同律的探针压哨
        if value != m5["value"] or score != m5["residual_score"]:
            self.findings.produce(make_residual(
                "replay_mismatch", f"mutual-proof:{record.get('pid')}", "breaking",
                "replay==verdict",
                f"replay 得 ({value},{score}) ≠ 原 verdict "
                f"({m5['value']},{m5['residual_score']})（种子={m2['tick_hash']}）",
                m2["tick_seq"]), DOMAIN_IPMP)
            raise BindingError(
                "replay 与原 verdict 不一致（replay_mismatch 已入残差流）")
        return Verdict(value=value, residual_score=score, gap=m1["gap"],
                       entropy_grade=m5["entropy_grade"],
                       replay_seed=m2["tick_hash"],
                       judge_set=tuple(bytes.fromhex(h) for h in m5["judge_set"]))
