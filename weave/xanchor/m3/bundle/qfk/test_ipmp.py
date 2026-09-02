"""qfk.test_ipmp — ipmp 模块交验测试（续 test_all.py 编号 24–34，设计 T-01~T-11）。

覆盖：三机规格卡/类闸门/gap 钉死/窗口 commit-reveal 正例/提前 reveal 负例组/
串谋负例（M-probe）/熵档快照/裁定重放确定性/verdict m-of-n/绑定失配留证/
灰区#10 自证禁止与角色轮换。
零网络：beacon 全走离线 classical-sim 源或定值桩源（fetch 不触网）；恶意负例
（T-06/T-10）与正例（T-04）共享同一公开接口路径，无测试专用后门。
运行：在 /mnt/agents/output 下 `python -m qfk.test_ipmp`。
"""

import copy
import json
import unittest

import numpy as np

from .beacon import Beacon
from .chain import Chain, sha256
from .circle import gen_keypair, make_policy, sign_verdict, verify_verdict
from .field import Field
from .findings import FindingEngine
from .ipmp import (BindingError, ClassGateError, DOMAIN_IPMP, ENTROPY_DISCLAIMER,
                   IPMPEngine, PhaseError, SelfJudgeError, WindowLockedError,
                   WindowPolicy, binding_digest, judge_verdict, machine_spec)


class StubCertifiedSource:
    """定值桩源（name 非 offline → entropy_grade="certified"）；fetch 不触网。"""

    name = "stub-certified"

    def fetch(self) -> bytes:
        return b"\x42" * 32


class TestIpmp(unittest.TestCase):
    def setUp(self):
        self.chain = Chain()
        self.beacon = Beacon()               # 默认离线 classical-sim，零网络
        self.findings = FindingEngine()
        self.keys = [gen_keypair() for _ in range(5)]
        self.members = [pub for _, pub in self.keys]
        self.policy = make_policy(3, self.members)          # 3-of-5
        self.window = WindowPolicy(phase_n=1, phase_p=0)    # 每拍点火，免等相位
        self.engine = IPMPEngine(self.chain, self.beacon, self.policy,
                                 self.findings, self.window)
        self.salts = {"P1": b"\xaa" * 32, "P2": b"\xbb" * 32}
        fa = np.array([0.5, -1.25, 3.0, 0.125], dtype=np.float64)
        self.r1 = fa.tobytes()                      # IP 机应答
        self.r2 = (fa + 1e-5).tobytes()             # NP 机独立重算（阈内微差）
        self.resp_fn_hash = sha256(b"responder-fn-v1")

    # 公共驱动：COMMIT→…→JUDGE（各测试按需截取相位）
    def _drive(self, engine, pid, *, r1=None, r2=None, gap=0.01,
               proposer="ip-machine", stop="judge", wrong_window=False):
        r1 = self.r1 if r1 is None else r1
        r2 = self.r2 if r2 is None else r2
        s = engine.open_session(pid)
        commit = s.commit_proposition(
            b"claim: witness w satisfies phi", claim_class="np-witness",
            witness_ref=f"ipmp:{pid}:witness", gap=gap,
            geodesic_req={"mode": "shortest-verify-path"},
            resp_fn_hash=self.resp_fn_hash, proposer=proposer)
        if stop == "commit":
            return s, commit, None
        ch = s.open_challenge()
        if stop == "challenge":
            return s, ch, None
        wseq = ch.tick_seq + 1 if wrong_window else ch.tick_seq
        for role, r in (("P1", r1), ("P2", r2)):
            rh = binding_digest(role, r, self.salts[role], wseq)
            s.submit_commitment(role, rh, ts=100.0 if role == "P1" else 100.5)
        if stop == "window":
            return s, ch, None
        for role, r in (("P1", r1), ("P2", r2)):
            s.reveal(role, r, self.salts[role], ts=101.0)
        if stop == "reveal":
            return s, ch, None
        v = s.judge()
        return s, ch, v

    def _sign3(self, verdict, k=3):
        return {pub: sign_verdict(sk, verdict.digest())
                for sk, pub in self.keys[:k]}

    # T-01（A1）：三机规格卡声明 + honesty_assumption 只在 m1 不入验证路径
    def test_24_machine_specs_declared(self):
        specs = [machine_spec(n) for n in ("ip-machine", "np-machine", "n-machine")]
        self.assertEqual(len({s.role for s in specs}), 3)      # role 字段互异
        with self.assertRaises(KeyError):
            machine_spec("hal-machine")                        # 未知名 KeyError
        s, ch, v = self._drive(self.engine, "t24")
        m1 = json.loads(self.chain.entries_of(DOMAIN_IPMP)[0].payload.decode())
        self.assertIn("honesty_assumption", json.dumps(m1["machine"],
                                                       ensure_ascii=False))
        # 验证路径不含之：verdict 共签对象的 canon 体无 honesty_assumption
        from .chain import canon as _canon
        self.assertNotIn("honesty_assumption",
                         _canon(v._canon_body()).decode("utf-8"))
        self.assertTrue(verify_verdict(v.digest(), self._sign3(v), self.policy))

    # T-02（A2）：类闸门拒纠缠编译档，会话停在 COMMIT，恰一条 warn finding
    def test_25_class_gate_rejects_entangled(self):
        s = self.engine.open_session("t25")
        with self.assertRaises(ClassGateError):
            s.commit_proposition(
                b"claim: entangled", claim_class="entangled-compiled",
                witness_ref="ipmp:t25:witness", gap=0.01, geodesic_req={},
                resp_fn_hash=self.resp_fn_hash)
        self.assertEqual(s.phase, "COMMIT")                    # 会话停在 COMMIT
        rej = [f for f in self.findings.queue
               if f.type == "proposition_class_rejected"]
        self.assertEqual(len(rej), 1)                          # 恰一条
        self.assertEqual(rej[0].severity, "warn")
        self.assertEqual(rej[0].domain, "mutual-proof")
        self.assertFalse(rej[0].human_gate)
        # 合法两类放行（同会话 COMMIT 相位可重提 + 新会话）
        s.commit_proposition(b"c", claim_class="np-witness",
                             witness_ref="w", gap=0.01, geodesic_req={},
                             resp_fn_hash=self.resp_fn_hash)
        s2 = self.engine.open_session("t25b")
        s2.commit_proposition(b"c", claim_class="pcp-compiled",
                              witness_ref="w", gap=0.01, geodesic_req={},
                              resp_fn_hash=self.resp_fn_hash)
        self.assertEqual(len([f for f in self.findings.queue
                              if f.type == "proposition_class_rejected"]), 1)

    # T-03（A3）：gap=None 一律 GAP_UNKNOWN；同输入带 gap → ACCEPT（对照组）
    def test_26_gap_unknown_pinned(self):
        claim_hash = sha256(b"claim")
        qrand = sha256(b"qrand")
        v_none = judge_verdict(claim_hash, qrand, self.r1, self.r1, None)
        self.assertEqual(v_none, ("GAP_UNKNOWN", None))        # residual 为 None
        v_gap = judge_verdict(claim_hash, qrand, self.r1, self.r1, 0.01)
        self.assertEqual(v_gap, ("ACCEPT", 0.0))               # gap 是唯一差异
        # 两分支共享同一纯函数：超阈分支同函数产出 REJECT
        far = (np.frombuffer(self.r1, dtype=np.float64) + 1.0).tobytes()
        v_rej = judge_verdict(claim_hash, qrand, self.r1, far, 0.01)
        self.assertEqual(v_rej[0], "REJECT")
        self.assertGreater(v_rej[1], 1.0)

    # T-04（A4 正例 + m6 schema）：双 commit→双 reveal→judge→3 签 settle 全通
    def test_27_window_commit_reveal_happy(self):
        self.engine.field = Field()                            # κ 互锚可选臂
        s, ch, v = self._drive(self.engine, "t27")
        self.assertEqual(v.value, "ACCEPT")
        self.assertLessEqual(v.residual_score, 1.0)
        self.assertEqual(v.entropy_grade, "classical-sim")
        e = s.settle(self._sign3(v))
        self.assertEqual(e.domain, DOMAIN_IPMP)
        self.assertTrue(self.chain.verify())                   # m6 入链后链可验
        m6 = json.loads(e.payload.decode())
        for k in ("verdict", "qrand", "kappa_chain", "kappa_field",
                  "entropy_grade", "replay_seed", "sigs", "entropy_disclaimer"):
            self.assertIn(k, m6)
        self.assertEqual(m6["qrand"], ch.qrand.hex())
        self.assertEqual(m6["replay_seed"], ch.tick_hash.hex())
        self.assertEqual(m6["entropy_grade"], "classical-sim")
        self.assertIsNotNone(m6["kappa_field"])
        self.assertEqual(m6["verdict"]["value"], "ACCEPT")
        self.assertTrue(s.settled)                             # 终态只读
        with self.assertRaises(PhaseError):
            s.settle(self._sign3(v))

    # T-05（A4 负例组）：提前 reveal / 错窗承诺 / 相位外补交
    def test_28_window_early_reveal_rejected(self):
        # 仅单方 commit 即 reveal → WindowLockedError
        s = self.engine.open_session("t28a")
        s.commit_proposition(b"c", claim_class="np-witness", witness_ref="w",
                             gap=0.01, geodesic_req={},
                             resp_fn_hash=self.resp_fn_hash)
        ch = s.open_challenge()
        rh = binding_digest("P1", self.r1, self.salts["P1"], ch.tick_seq)
        s.submit_commitment("P1", rh, ts=100.0)
        self.assertEqual(s.phase, "WINDOW")
        with self.assertRaises(WindowLockedError):
            s.reveal("P1", self.r1, self.salts["P1"], ts=100.1)
        # 窗口编号错（window_seq≠tick_seq）→ reveal 绑定核验 BindingError
        s2, _, _ = self._drive(self.engine, "t28b", stop="window",
                               wrong_window=True)
        self.assertEqual(s2.phase, "RESPOND")
        with self.assertRaises(BindingError):
            s2.reveal("P1", self.r1, self.salts["P1"], ts=101.0)
        # 相位外再 submit_commitment → PhaseError
        with self.assertRaises(PhaseError):
            s2.submit_commitment("P1", b"\x22" * 32, ts=102.0)

    # T-06（A4+M-probe 负例）：恶意串谋——绑定全过、流程合法，探针命中压哨
    def test_29_collusion_negative(self):
        r1 = np.array([0.5, -1.25, 3.0, 0.125], dtype=np.float64).tobytes()
        r2 = sha256(r1)            # NP 机把 r1 的指纹拼进应答（32B，可反序列化）
        s, ch, v = self._drive(self.engine, "t29", r1=r1, r2=r2)
        sus = [f for f in self.findings.queue if f.type == "collusion_suspect"]
        self.assertEqual(len(self.findings.queue), 1)          # 恰一条 finding
        self.assertEqual(len(sus), 1)
        self.assertEqual(sus[0].severity, "breaking")
        self.assertTrue(sus[0].human_gate)                     # 人工闸
        self.assertNotEqual(v.value, "ACCEPT")                 # verdict 不得 ACCEPT
        self.assertEqual(v.value, "REJECT")

    # T-07（A5）：熵档快照入 verdict + m6 disclaimer；桩源切 certified（零网络）
    def test_30_entropy_grade_in_verdict(self):
        s, ch, v = self._drive(self.engine, "t30a")
        self.assertEqual(v.entropy_grade, "classical-sim")     # 默认离线源
        e = s.settle(self._sign3(v))
        m6 = json.loads(e.payload.decode())
        self.assertEqual(m6["entropy_disclaimer"], ENTROPY_DISCLAIMER)
        # 双桩源（name 非 offline，fetch 定值，不触网）→ certified
        b2 = Beacon(sources=(StubCertifiedSource(), StubCertifiedSource()))
        eng2 = IPMPEngine(Chain(), b2, self.policy, FindingEngine(), self.window)
        s2, _, v2 = self._drive(eng2, "t30b")
        self.assertEqual(v2.entropy_grade, "certified")

    # T-08（A6）：同 record 连跑两次 replay 全等；篡改一字节 → mismatch+BindingError
    def test_31_replay_deterministic(self):
        s, ch, v = self._drive(self.engine, "t31")
        s.settle(self._sign3(v))
        rec = s.record()
        va = self.engine.replay(rec)
        vb = self.engine.replay(rec)
        self.assertEqual(va.to_dict(), vb.to_dict())           # 两次全等
        self.assertEqual(va.value, "ACCEPT")
        self.assertEqual(va.replay_seed, ch.tick_hash.hex())   # 可复现锚
        bad = copy.deepcopy(rec)
        raw = bytearray.fromhex(bad["m3_reveal"]["P2"]["payload"])
        raw[7] ^= 0x80                                         # 篡改 r2 一字节（翻符号位）
        bad["m3_reveal"]["P2"]["payload"] = raw.hex()
        with self.assertRaises(BindingError):
            self.engine.replay(bad)
        mis = [f for f in self.findings.queue if f.type == "replay_mismatch"]
        self.assertEqual(len(mis), 1)
        self.assertEqual(mis[0].severity, "breaking")
        self.assertTrue(mis[0].human_gate)

    # T-09（m5/circle F-3）：不足 m 拒、伪造非成员签仍拒、补齐 3 签过
    def test_32_verdict_m_of_n_enforced(self):
        s, ch, v = self._drive(self.engine, "t32")
        n_before = len(self.chain.entries_of(DOMAIN_IPMP))
        with self.assertRaises(PhaseError):                    # 2 签不足 m=3
            s.settle(self._sign3(v, k=2))
        sk_x, pub_x = gen_keypair()
        forged = self._sign3(v, k=2)
        forged[pub_x] = sign_verdict(sk_x, v.digest())         # 伪造第 3 签（非成员）
        with self.assertRaises(PhaseError):
            s.settle(forged)
        self.assertEqual(len(self.chain.entries_of(DOMAIN_IPMP)), n_before)  # m6 未入链
        e = s.settle(self._sign3(v))                           # 补齐 3 签 → 过
        self.assertGreater(len(self.chain.entries_of(DOMAIN_IPMP)), n_before)
        self.assertTrue(self.chain.verify())

    # T-10（M1 负例）：reveal 与 commit 绑定失配 → BindingError + breaking 留证
    def test_33_binding_mismatch_finding(self):
        s, ch, _ = self._drive(self.engine, "t33", stop="window")
        with self.assertRaises(BindingError):
            s.reveal("P1", b"\x00" * 32, self.salts["P1"], ts=101.0)  # 错 payload
        bm = [f for f in self.findings.queue if f.type == "binding_mismatch"]
        self.assertEqual(len(bm), 1)
        self.assertEqual(bm[0].severity, "breaking")
        self.assertTrue(bm[0].human_gate)
        self.assertEqual(s.phase, "RESPOND")                   # 会话不得进 JUDGE
        with self.assertRaises(PhaseError):
            s.judge()

    # T-11（灰区#10）：剔除后无人可裁 → SelfJudgeError；轮换表正例
    def test_34_no_self_judge(self):
        sk_np, pub_np = gen_keypair()
        solo_policy = make_policy(1, [pub_np])                 # members 恰为 NP 单机密钥
        eng = IPMPEngine(Chain(), Beacon(), solo_policy, FindingEngine(),
                         self.window)
        eng.register_machine("np-machine", (pub_np,))
        tick = eng.beacon.tick()
        with self.assertRaises(SelfJudgeError):                # 宁停不让自证
            eng.judge_set_for("np-machine", tick)
        # 角色轮换接口正例：显式映射排除 proposer 密钥
        rot_keys = [gen_keypair() for _ in range(3)]
        rot = {"np-machine": tuple(pub for _, pub in rot_keys)}
        eng2 = IPMPEngine(Chain(), Beacon(), solo_policy, FindingEngine(),
                          self.window, judge_rotation=rot)
        eng2.register_machine("np-machine", (pub_np,))
        js = eng2.judge_set_for("np-machine", tick)
        self.assertNotIn(pub_np, js)                           # 裁定集不含 proposer 密钥
        self.assertEqual(set(js), {pub for _, pub in rot_keys})
        with self.assertRaises(KeyError):
            eng2.register_machine("ghost-machine", (pub_np,))


if __name__ == "__main__":
    unittest.main(verbosity=2)
