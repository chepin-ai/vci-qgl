"""qfk.test_all — 交验测试（≥12，硬约束 7：本模块全绿=完成定义）。

覆盖规格测试清单：链追加/篡改检测/alias 不入验证/tile 证明/圈签 m-of-n 通过
与不足拒绝/RECONFIG 自指/场指纹对拍/漂移→FINDING/切片订阅/tensor 不动点收敛/
tn_residual 阈值/trans T4+T5/beacon 离线抽签确定性/findings 闭环入链。
零网络：beacon 全走离线 classical-sim 源，ANU/drand 客户端不被实例化调用。
运行：在 /mnt/agents/output 下 `python -m qfk.test_all`。
"""

import json
import unittest

import numpy as np

from .beacon import Beacon, BeaconTick, leader_draw, qubo_hook, sha256 as bsha
from .chain import Chain, TILE, alias, merkle_verify, sha256
from .circle import (commit_reconfig, effective_policy, gen_keypair, llm_advice,
                     make_policy, sign_checkpoint, verify as circle_verify)
from .field import Field
from .findings import FindingEngine, make_residual
from .tensor import (Relation, Rule, contraction_path, run_fixpoint, tn_embed,
                     tn_residual)
from .trans import trans


class TestChain(unittest.TestCase):
    def test_01_append_and_verify(self):
        c = Chain()
        for i in range(2 * TILE + 3):
            c.append("test", f"payload-{i}".encode())
        self.assertTrue(c.verify())
        self.assertEqual(len(c.checkpoints), 1 + 2)  # genesis + 2 tiles
        self.assertEqual(len(c.head), 32)            # 全 256-bit

    def test_02_tamper_detection(self):
        c = Chain()
        for i in range(TILE):
            c.append("test", f"p{i}".encode())
        self.assertTrue(c.verify())
        c.entries[3].payload = b"forged"             # 篡改
        self.assertFalse(c.verify())

    def test_03_alias_never_in_verification(self):
        c = Chain()
        e = c.append("test", b"x")
        a = alias(e.hash)
        self.assertEqual(a, e.hash.hex()[:12])
        self.assertEqual(len(a), 12)
        # alias 产出喂进验证路径 → 直接拒绝（长度检查）
        with self.assertRaises(ValueError):
            merkle_verify(bytes.fromhex(a), [], c.checkpoints[0].root)
        with self.assertRaises(ValueError):
            alias(bytes.fromhex(a))  # 12-hex 不可再 alias（非 32B）

    def test_04_tile_inclusion_proof(self):
        c = Chain()
        for i in range(TILE):
            c.append("doc", f"fact-{i}".encode())
        proof = c.prove(5)
        self.assertTrue(c.verify_proof(proof))
        # 换叶即败
        bad = dict(proof)
        bad["entry"] = dict(proof["entry"], payload=b"evil".hex())
        self.assertFalse(c.verify_proof(bad))

    def test_05_legacy_12hex_binding_degraded(self):
        c = Chain(legacy_head="a1b2c3d4e5f6")  # @gray 旧链 12-hex 头
        g = c.checkpoints[0].legacy
        self.assertEqual(g["evidence_level"], "degraded-12hex")  # 如实降级
        c.append("test", b"x")
        self.assertTrue(c.verify())


class TestCircle(unittest.TestCase):
    def setUp(self):
        self.keys = [gen_keypair() for _ in range(5)]
        self.members = [pub for _, pub in self.keys]
        self.policy = make_policy(3, self.members)
        self.cp_root = sha256(b"checkpoint-root")

    def test_06_m_of_n_pass(self):
        sigs = {pub: sign_checkpoint(sk, self.cp_root)
                for sk, pub in self.keys[:3]}
        self.assertTrue(circle_verify(self.cp_root, sigs, self.policy))

    def test_07_insufficient_reject(self):
        sigs = {pub: sign_checkpoint(sk, self.cp_root)
                for sk, pub in self.keys[:2]}
        self.assertFalse(circle_verify(self.cp_root, sigs, self.policy))
        # 伪造签名者（非成员）不计数
        sk_x, pub_x = gen_keypair()
        sigs[pub_x] = sign_checkpoint(sk_x, self.cp_root)
        self.assertFalse(circle_verify(self.cp_root, sigs, self.policy))

    def test_08_reconfig_self_referential(self):
        c = Chain()
        new_keys = [gen_keypair() for _ in range(3)]
        new_policy = make_policy(2, [pub for _, pub in new_keys])
        commit_reconfig(c, new_policy)  # 新政策=domain="circle" 链 entry，自指生效
        cur = effective_policy(c, self.policy)
        self.assertEqual(cur.policy_hash, new_policy.policy_hash)
        sigs = {pub: sign_checkpoint(sk, self.cp_root) for sk, pub in new_keys[:2]}
        self.assertTrue(circle_verify(self.cp_root, sigs, cur))
        self.assertFalse(circle_verify(self.cp_root, sigs, self.policy))  # 旧政策失配

    def test_09_llm_advice_weight_zero(self):
        adv = llm_advice("should we reconfig?", {"cp": "x"})
        self.assertEqual(adv["weight"], 0)         # LLM 权重恒 0
        self.assertIsNone(adv["advice"])           # 占位：无 LLM 调用面
        self.assertTrue(circle_verify(             # verify 路径永不读 advice
            self.cp_root,
            {pub: sign_checkpoint(sk, self.cp_root) for sk, pub in self.keys[:3]},
            self.policy))


class TestField(unittest.TestCase):
    def _field_with_locks(self):
        f = Field()
        for w, ps in {"alice": ["x", "y"], "bob": ["z"]}.items():
            for p in ps:
                self.assertTrue(f.claim(p, w))
        return f

    def test_10_fingerprint_commit_and_tick_check_clean(self):
        c, eng = Chain(), FindingEngine()
        f = self._field_with_locks()
        f.put("a:x", b"v1", "alice", tick=1)
        f.put("b:z", b"v2", "bob", tick=1)
        f.commit(c, tick=1)
        self.assertIsNone(f.tick_check(c, eng, tick=2))  # 对拍一致 → 无残差
        self.assertEqual(len(eng.queue), 0)

    def test_11_drift_becomes_finding(self):
        c, eng = Chain(), FindingEngine()
        f = self._field_with_locks()
        f.put("a:x", b"v1", "alice", tick=1)
        f.commit(c, tick=1)
        f.put("a:x", b"v2-mutated", "alice", tick=2)     # 写后即感应，链未追平
        finding = f.tick_check(c, eng, tick=2)
        self.assertIsNotNone(finding)
        self.assertEqual(finding.type, "drift")
        self.assertEqual(finding.domain, "field")
        # 手动重放重建：投影可弃，真源唯一（链）
        f.commit(c, tick=2)
        f2 = Field.rebuild_from(c)
        self.assertEqual(f2.root(), f.root())

    def test_12_reconcile_and_slice(self):
        f1, f2 = self._field_with_locks(), self._field_with_locks()
        f1.put("a:x", b"same", "alice", tick=1)
        f2.put("a:x", b"same", "alice", tick=1)
        self.assertEqual(Field.reconcile(f1, f2)["status"], "PASS")
        f2.put("a:y", b"only-in-f2", "alice", tick=2)
        r = Field.reconcile(f1, f2)
        self.assertEqual(r["status"], "DIFF")
        self.assertIn("a:y", r["diff"])
        # AOI 切片订阅：prefix + max_count
        f1.put("a:y", b"v", "alice", tick=2)
        got = list(f1.iter_slice("a:", max_count=1))
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0][0].startswith("a:"))

    def test_13_write_gate_max5(self):
        eng = FindingEngine()
        f = Field()
        for i in range(5):  # 写者前沿 ≤5（I7，角色 CZ-4：与签者圈 5–30 分开）
            self.assertTrue(f.claim(f"p{i}", f"w{i}"))
        self.assertFalse(f.claim("p5", "w5-overflow", engine=eng, tick=1))  # 第 6 写者被拒
        denied = [x for x in eng.queue if x.type == "write_gate_denied"]
        self.assertEqual(len(denied), 1)                 # 超区诉求→残差流


class TestTensor(unittest.TestCase):
    def test_14_fixpoint_transitive_closure(self):
        edges = Relation("edge", {(0, 1), (1, 2), (2, 3)}, (4, 4))
        rules = [Rule("xy,yz->xz", ("edge", "edge"), "reach"),
                 Rule("xy,yz->xz", ("reach", "edge"), "reach")]
        out = run_fixpoint(rules, {"edge": edges}, max_iter=50)
        self.assertTrue(out["converged"])
        reach = out["relations"]["reach"].tuples
        self.assertIn((0, 3), reach)   # 多跳闭包
        self.assertIn((0, 2), reach)
        self.assertNotIn((3, 0), reach)

    def test_15_tn_embed_and_residual_threshold(self):
        rng = np.random.default_rng(7)
        core = rng.standard_normal((3, 4, 5))
        fa = tn_embed(core, rank=3, n_iter=10, seed=1)[0]
        self.assertIsNone(tn_residual(fa, fa.copy(), eps=1e-3))  # 零残差→无 FINDING
        fb = fa + 0.5 * rng.standard_normal(fa.shape)            # 大扰动超阈
        res = tn_residual(fa, fb, eps=1e-3, tol=1.0, tick=9)
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "tensor_residual")
        self.assertEqual(set(res), {"type", "focus", "severity",  # 五域同 schema
                                    "constraint", "detail", "tick"})

    def test_16_contraction_path_cache_with_digest(self):
        dims = {"a": 4, "b": 8, "c": 2, "d": 16}
        p1 = contraction_path("ab,bc,cd->ad", dims, state_digest="s1")
        p2 = contraction_path("ab,bc,cd->ad", dims, state_digest="s1")
        p3 = contraction_path("ab,bc,cd->ad", dims, state_digest="s2")
        self.assertEqual(p1, p2)                 # 同 digest 命中缓存
        self.assertIs(p1, p2)                    # 命中返回同一缓存对象
        self.assertEqual(len(p1), 2)             # 3 张量 → 2 步逐对收缩
        self.assertEqual(len(p3), 2)


class TestTrans(unittest.TestCase):
    def test_17_t4_gate(self):
        ok = trans("L0", "L2", "def f():\n    return 1\n", {"tier": "T4", "tick": 1})
        self.assertIsNone(ok["residual"])
        self.assertTrue(ok["proof"]["passed"])
        bad = trans("L0", "L2", "def f(:\n  ???", {"tier": "T4", "tick": 2})
        self.assertIsNone(bad["artifact"])                    # 当闸：不过即拒
        self.assertEqual(bad["residual"]["type"], "t4_gate_fail")
        self.assertEqual(bad["residual"]["severity"], "breaking")

    def test_18_t5_chain_witness(self):
        c = Chain()
        for i in range(TILE - 1):                 # 先填 7 条，T5 见证成第 8 条入 tile
            c.append("doc", f"filler-{i}".encode())
        r = trans("L2", "L3", b"artifact-bytes", {"tier": "T5", "chain": c, "tick": 3})
        self.assertEqual(r["proof"]["tier"], "T5")
        proof = r["proof"]["evidence"]
        self.assertTrue(c.verify_proof(proof))    # inclusion+consistency 可验
        self.assertIsNone(r["residual"])
        # pending 分支：未过 TILE 边界时如实返回
        c2 = Chain()
        r2 = trans("L2", "L3", b"x", {"tier": "T5", "chain": c2, "tick": 0})
        self.assertEqual(r2["proof"]["evidence"]["status"], "pending_tile")

    def test_19_hook_tiers_residual(self):
        for tier in ("T1", "T2", "T3"):
            r = trans("L0", "L1", "some statement", {"tier": tier, "tick": 1})
            self.assertEqual(r["residual"]["type"], "proof_tier_unavailable")
            self.assertEqual(r["residual"]["severity"], "info")


class TestBeacon(unittest.TestCase):
    def test_20_offline_tick_chain_and_draw_deterministic(self):
        b = Beacon()                      # 默认离线 classical-sim，零网络
        t1, t2 = b.tick(), b.tick()
        self.assertEqual(t2.prev, t1.hash)          # prev 演进
        self.assertEqual(len(t1.qrand), 32)
        members = ["alice", "bob", "carol", "dave", "erin"]
        d1 = leader_draw(members, t2)
        d2 = leader_draw(list(reversed(members)), t2)
        self.assertEqual(d1, d2)                    # 确定性、与输入顺序无关
        self.assertIn(d1, members)

    def test_21_qubo_hook_no_promise(self):
        r = qubo_hook({"edges": [("a", "b")]})
        self.assertEqual(r["status"], "hook_only")  # 北星试件：禁性能承诺
        self.assertEqual(r["residual"]["constraint"], "no_performance_promise")


class TestFindings(unittest.TestCase):
    def test_22_closed_loop_commit_on_chain(self):
        c, eng = Chain(), FindingEngine()
        f = eng.produce(make_residual("drift", "field.root", "warn",
                                      "holo", "mismatch demo", 5), "field")
        self.assertEqual(f.status, "routed")
        self.assertEqual(f.routed_to, "auto")
        eng.resolve(f.id, "note-1")
        eng.resolve(f.id, "note-2 [resolved]")
        self.assertEqual(f.status, "resolved")
        e = eng.commit(c, f.id)
        self.assertEqual(c.entries[e.seq].domain, "finding")
        body = json.loads(c.entries[e.seq].payload.decode())
        self.assertEqual(body["type"], "drift")     # 五域同 schema 入链留证
        self.assertEqual(body["severity"], "warn")
        with self.assertRaises(RuntimeError):
            eng.resolve(f.id, "too late")           # 已入链不可再注记
        self.assertTrue(c.verify())

    def test_23_breaking_human_gate_and_round_cap(self):
        eng = FindingEngine()
        f = eng.produce(make_residual("t4_gate_fail", "trans:L0->L2", "breaking",
                                      "ast", "syntax", 1), "trans")
        self.assertTrue(f.human_gate)               # breaking→人工闸
        self.assertEqual(f.routed_to, "human")
        for i in range(3):
            eng.resolve(f.id, f"round-{i}")
        with self.assertRaises(RuntimeError):       # ≤3 轮注记
            eng.resolve(f.id, "round-4")


if __name__ == "__main__":
    unittest.main(verbosity=2)
