#!/usr/bin/env python3
# m3-smoke-usrm.py — M3 联合冒烟 · usrm 半区（单沙箱桥接冒烟脚本）
#
# 对位：entangle_mutual_proof.py v2 双股链（Field × challenge_round）
#        × qfk.ipmp 六相位（COMMIT→CHALLENGE→WINDOW→RESPOND→JUDGE→SETTLE）
#
# 锚停滞在案：本轮一切随机性溯源于 last-good 锚 qrand@seq61（cisvr-68 §二 定格），
#   seed=int(sha256(qrand_hex‖str(seq))[:8],16)=3712427753；seq61 之后锚停滞，无新熵入案。
# 确定性：不用 secrets、不用 os.urandom、不用真时钟——
#   · 挑战随机源 = random.Random(3712427753)（entangle 侧 8 轮）
#   · beacon 侧 = DetBeacon（HKDF 结构不变，熵入料全部种子派生；源仍 subclass
#     OfflineSource ⇒ entropy_grade 如实报 "classical-sim"，不升格）
#   · 时钟 = 仿真步进钟（钉死起点，逐步 +1ms），chain entry ts 全确定
#   · Ed25519 密钥 = from_private_bytes(sha256(seed‖":key:i")) 派生（非真机密钥，
#     仅冒烟身份件；Ed25519 签名本身确定性）
#   ⇒ 同版本脚本+同依赖复跑，transcript 逐字节一致（VERDICT.md 附两次实跑 sha256）。
# 三灰标随数：①单沙箱多角色（非真隔离）②探针未命中≠清白 ③classical-sim 档
#   （MIP 无星结构同构不升格）。
# 纪律：零编数全真跑；一切数值为【仿真】；未实测不编数。
#
# 运行：python3 /mnt/agents/output/wave5/m3-bridge/m3-smoke-usrm.py
# 产物：m3-smoke-transcript.json / m3-manifest.json / run-log.txt（同目录）
# 退出码：0=USRMS-HALF PASS，1=FAIL。

import hashlib
import importlib.util
import itertools
import json
import os
import random
import sys
import time as _time

import numpy as np

sys.path.insert(0, "/mnt/agents/output/wave5")

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from qfk.beacon import Beacon, BeaconTick, OfflineSource
from qfk.chain import Chain, canon, sha256
from qfk.circle import make_policy, sign_verdict
from qfk.findings import FindingEngine
from qfk.ipmp import (DOMAIN_IPMP, IPMPEngine, WindowPolicy, binding_digest,
                      collusion_probe)

# ---------------------------------------------------------------- 定格种子（cisvr-68 §二）
QRAND_SEQ61_HEX = ("c21b1f0f5858ab4acba2fba54b5e84bd7ea30234dbc4e43cb2304735c5e20eeb")
SEED = int(hashlib.sha256((QRAND_SEQ61_HEX + "61").encode()).hexdigest()[:8], 16)
assert SEED == 3712427753, "定格种子复算不符（cisvr-68 §二）"
SEED_B = SEED.to_bytes(8, "big")

ANCHOR_STALL = ("锚停滞在案：一切随机性溯源于 last-good 锚 qrand@seq61="
                + QRAND_SEQ61_HEX + "；seed=int(sha256(qrand_hex‖str(seq))[:8],16)"
                "=3712427753（cisvr-68 §二 定格）；seq61 后锚停滞，无新熵入案。")
GRAY = [
    "灰标1 单沙箱多角色：usrm 一沙箱分饰 场A/场B 与 ip/np/n 三机，非真隔离，隔离强度不声称",
    "灰标2 探针未命中≠清白：collusion_probe 单向——命中=违规证据，未命中不构成清白证明",
    "灰标3 classical-sim 档：熵源为离线经典仿真（种子定格派生），MIP 无星结构同构不升格",
]
SIM_NOTE = "【仿真】全部数值为经典仿真，无真量子纠缠；MIP 无星结构同构不升格"

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- entangle v2 载入（类原样）
_spec = importlib.util.spec_from_file_location(
    "entangle_v2", "/mnt/agents/output/wave5/ctx-entangle-v2.py")
ENT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ENT)   # 模块级仅 import hashlib/secrets；challenge_round 不调用

# ---------------------------------------------------------------- 确定性脚手架
_T0 = 1780000000.0  # 仿真钟起点（钉死；人读无义，永不作可信时戳）
_tick_ms = itertools.count()
_time.time = lambda: _T0 + next(_tick_ms) * 0.001  # 全局仿真步进钟（含 qfk.chain.append）


def _stream(tag: str) -> random.Random:
    """种子派生独立随机流：random.Random(int(sha256(seed‖tag),16))。"""
    return random.Random(int.from_bytes(sha256(SEED_B + tag.encode()), "big"))


class DetSource(OfflineSource):
    """确定性离线仿真源：subclass OfflineSource ⇒ entropy_grade 如实 classical-sim。

    fetch 不触网、不读 os.urandom；输出=种子派生流的 32B。结构同 OfflineSource，
    仅把熵入料换成可复跑派生——档不升格（classical-sim 如实）。
    """

    def __init__(self, tag: str):
        self._rng = _stream(tag)
        self.name = "offline-classical-sim-det:" + tag

    def fetch(self) -> bytes:
        return self._rng.randbytes(32)


class DetBeacon(Beacon):
    """HKDF 混合结构逐式保留的确定性 beacon：仅熵入料（两源+local）全部种子派生。

    不声称任何量子性；源为 DetSource(OfflineSource 子类) ⇒ entropy_grade()
    报 "classical-sim"（A5 快照如实）。
    """

    def __init__(self, tag: str):
        super().__init__(sources=(DetSource(tag + ":s0"), DetSource(tag + ":s1")))
        self._local = _stream(tag + ":local")

    def tick(self) -> BeaconTick:  # 同 Beacon.tick 式，仅 local 换派生流
        anu, drand = (s.fetch() for s in self.sources)
        local = self._local.randbytes(32)
        qrand = HKDF(algorithm=hashes.SHA256(), length=32,
                     salt=self.prev, info=str(self.seq).encode()).derive(
            anu + drand + local + self.prev)
        t = BeaconTick(seq=self.seq, qrand=qrand, prev=self.prev,
                       hash=sha256(self.seq.to_bytes(8, "big") + self.prev + qrand),
                       source_names=tuple(s.name for s in self.sources))
        self.prev = t.hash
        self.seq += 1
        self.ticks.append(t)
        return t


def det_keypair(i: int):
    """种子派生 Ed25519 身份件（冒烟专用，非真机密钥）。"""
    sk = Ed25519PrivateKey.from_private_bytes(sha256(SEED_B + b":key:" + str(i).encode()))
    return sk, sk.public_key().public_bytes_raw()


# ---------------------------------------------------------------- transcript（每步一行带 hash）
class Transcript:
    def __init__(self):
        self.steps = []
        self.prev = sha256(b"m3-bridge:transcript:genesis").hex()

    def log(self, phase: str, actor: str, action: str, detail: dict) -> dict:
        body = {"seq": len(self.steps), "phase": phase, "actor": actor,
                "action": action, "detail": detail, "sim": True, "prev": self.prev}
        h = hashlib.sha256(canon(body)).hexdigest()
        body["hash"] = h
        self.prev = h
        self.steps.append(body)
        return body


# ---------------------------------------------------------------- 双股链结构核验（仿真界内）
def verify_dual_strand(f, axioms: set) -> dict:
    """双股链可核验面（诚实界：tchain 命题序不可由无序定理集重放，故核验三项可验式）：
    ① genesis 链节式 ② 股长=1+互证命题数 ③ 承诺式 commit==H(state_digest,tchain尾)。"""
    checks = {
        "genesis_link": f.tchain[0] == ENT.H("genesis", f.name),
        "strand_len": len(f.tchain) == 1 + (len(f.theorems) - len(axioms)),
        "commitment_form": f.commit() == ENT.H(f.state_digest(), f.tchain[-1]),
        "astrand_nonempty": len(f.astrand) >= 1,
    }
    checks["all"] = all(checks.values())
    return checks


# ---------------------------------------------------------------- 六相位驱动（COMMIT→SETTLE）
def run_session(engine, pid: str, proposer: str, claim: bytes,
                r1: bytes, r2: bytes, salts: dict, signers: list, tr: Transcript):
    s = engine.open_session(pid)
    c = s.commit_proposition(claim, claim_class="np-witness",
                             witness_ref=f"ipmp:{pid}:witness", gap=0.01,
                             geodesic_req={"mode": "shortest-verify-path"},
                             resp_fn_hash=sha256(b"m3-bridge:responder-fn:v1"),
                             proposer=proposer)
    tr.log("COMMIT", proposer, "commit_proposition",
           {"pid": pid, "claim": claim.decode(), "claim_hash": c.claim_hash.hex(),
            "gap": c.gap, "chain_seq": c.chain_seq})
    ch = s.open_challenge()
    tr.log("CHALLENGE", "n-machine", "open_challenge",
           {"pid": pid, "tick_seq": ch.tick_seq, "qrand": ch.qrand.hex(),
            "entropy_grade": ch.entropy_grade})
    for role, r in (("P1", r1), ("P2", r2)):
        rh = binding_digest(role, r, salts[role], ch.tick_seq)
        s.submit_commitment(role, rh, ts=100.0 if role == "P1" else 100.5)  # 仿真时戳
    tr.log("WINDOW", "P1+P2", "submit_commitment×2（窗口内禁通信；双commit齐→窗关）",
           {"pid": pid, "window_seq": ch.tick_seq, "roles": ["P1", "P2"]})
    for role, r in (("P1", r1), ("P2", r2)):
        s.reveal(role, r, salts[role], ts=101.0)
    tr.log("RESPOND", "P1+P2", "reveal×2（绑定核验过）",
           {"pid": pid, "binding": "sha256(canon({payload,salt,role,window_seq}))==resp_hash"})
    probe = collusion_probe(r1, r2)  # 显式探针快照（judge 内部亦同式跑一遍）
    v = s.judge()
    tr.log("JUDGE", "judge_set", "judge",
           {"pid": pid, "value": v.value, "residual_score": v.residual_score,
            "gap": v.gap, "entropy_grade": v.entropy_grade,
            "collusion_probe": "miss" if probe is None else "HIT",
            "probe_note": "未命中≠清白（灰标2）",
            "judge_set": [p.hex() for p in v.judge_set], "replay_seed": v.replay_seed})
    sigs = {pub: sign_verdict(sk, v.digest()) for sk, pub in signers}
    e = s.settle(sigs)
    tr.log("SETTLE", "judge_set", "settle（m-of-n 共签核验过，m6 入链）",
           {"pid": pid, "m6_seq": e.seq, "sigs_count": len(sigs), "settled": s.settled})
    return s, v, e


# ---------------------------------------------------------------- 主流
def main() -> int:
    tr = Transcript()
    checks = {}

    # 拍0：定格声明入 transcript 首行
    tr.log("GENESIS", "usrm", "种子定格+锚停滞声明",
           {"seed": SEED, "qrand_seq61": QRAND_SEQ61_HEX,
            "seed_formula": "int(sha256(qrand_hex‖str(seq))[:8],16)",
            "anchor_stall": ANCHOR_STALL, "gray": GRAY, "sim_note": SIM_NOTE})

    # 拍1：双方各自起 Field × IPMPEngine（同根种子，分流派生）
    AX_A = {"ax:守恒", "ax:可复算"}
    AX_B = {"ax:互锁", "ax:笔直"}
    A = ENT.Field("场A-usrm", axioms=set(AX_A))
    B = ENT.Field("场B-cfts", axioms=set(AX_B))
    keys = [det_keypair(i) for i in range(5)]
    policy = make_policy(3, [pub for _, pub in keys])   # 3-of-5 裁定圈（仿真身份件）
    window = WindowPolicy(phase_n=1, phase_p=0)         # 每拍点火（冒烟免等相位）

    def make_engine(tag: str) -> IPMPEngine:
        eng = IPMPEngine(Chain(), DetBeacon(tag), policy, FindingEngine(), window)
        eng.register_machine("ip-machine", (keys[0][1],))
        eng.register_machine("np-machine", (keys[1][1],))
        return eng

    engA, engB = make_engine("engA"), make_engine("engB")
    tr.log("SETUP", "usrm(单沙箱分饰)", "Field×2 + IPMPEngine×2 起座（定格种子派生）",
           {"fieldA": A.name, "fieldB": B.name, "axiomsA": sorted(AX_A),
            "axiomsB": sorted(AX_B), "policy": "3-of-5", "entropy_grade": "classical-sim",
            "gray1": GRAY[0]})

    # 拍2a：互锚（双股规范固定：互引只入锚定股）
    A.anchor_peer(B)
    B.anchor_peer(A)
    tr.log("XANCHOR", "场A↔场B", "anchor_peer 双向（互引只入锚定股，承诺不变⇒收敛）",
           {"A_holds_B": A.peer_commitment, "B_holds_A": B.peer_commitment,
            "astrand_len": [len(A.astrand), len(B.astrand)]})

    # 拍2b：命题互证 + 桥心跳事件驱动重锚
    evA = A.prove("prop:跨场胶囊可达")
    hbA = B.bridge_heartbeat(A)
    evB = B.prove("prop:互锚防窜通")
    hbB = A.bridge_heartbeat(B)
    tr.log("PROVE+HEARTBEAT", "场A/场B", "prove×2 → bridge_heartbeat 事件触发重锚×2",
           {"evA": evA["type"], "B_reanchor": hbA, "evB": evB["type"],
            "A_reanchor": hbB, "tchain_len": [len(A.tchain), len(B.tchain)]})
    checks["heartbeat_fired"] = hbA and hbB

    # 拍2c：WINDOW 同构不变量——无新命题零动作（窗口内禁通信 ↔ 事件驱动零空转）
    quiet = A.bridge_heartbeat(B)
    tr.log("WINDOW-QUIET", "场A", "桥心跳不变量：无新命题⇒重锚触发=False（零空转）",
           {"quiet_reanchor": quiet, "iso": "WINDOW 窗口内禁通信 ↔ 事件驱动零动作"})
    checks["window_quiet"] = (quiet is False)

    # 拍2d：确定性 8 轮随机挑战（random.Random(SEED)，不用 secrets）
    rng = random.Random(SEED)
    rounds = []
    for _ in range(8):
        if rng.choice([True, False]):
            rounds.append(["A验B", A.verify_peer(B)])
        else:
            rounds.append(["B验A", B.verify_peer(A)])
    checks["challenge_8of8"] = all(r for _, r in rounds) and len(rounds) == 8
    tr.log("CHALLENGE-8R", "双场互验博弈", "challenge_round×8（种子定格随机源，确定性）",
           {"rounds": rounds, "all_pass": checks["challenge_8of8"],
            "rng": "random.Random(3712427753)", "no_secrets": True})

    # 拍2e：破缺对照（负例控制）——篡改场B ⇒ A 侧互验检出 ⇒ breach 入锚定股
    B_evil = ENT.Field(B.name, axioms=set(AX_B))
    B_evil.anchor_peer(A)
    B_evil.prove("prop:互锚防窜通")
    B_evil.theorems.add("prop:伪造定理")
    B_evil.tchain.append(ENT.H(B_evil.tchain[-1], "prop:伪造定理"))
    tamper_detected = not A.verify_peer(B_evil)
    if tamper_detected:
        A.breach(B.name)
    checks["breach_control"] = tamper_detected
    tr.log("BREACH-CONTROL", "场A", "负例控制：篡改场B（伪造命题）⇒互验检出⇒breach 入锚定股",
           {"tamper_detected": tamper_detected, "A_astrand_len": len(A.astrand),
            "mapping": "breach 入锚定股 ↔ ipmp judge FAIL→FINDING 入链"})

    # 拍2f：ipmp 六相位 ×2（互证镜像）——应答载荷种子派生（零编数）
    rng_np = np.random.default_rng(SEED)
    baseA = rng_np.standard_normal(4)
    baseB = rng_np.standard_normal(4)
    r1A, r2A = baseA.tobytes(), (baseA + 1e-5).tobytes()   # IP机应答 / NP机独立重算（阈内微差）
    r1B, r2B = baseB.tobytes(), (baseB + 1e-5).tobytes()
    saltsA = {r: sha256(SEED_B + b":salt:A:" + r.encode()) for r in ("P1", "P2")}
    saltsB = {r: sha256(SEED_B + b":salt:B:" + r.encode()) for r in ("P1", "P2")}

    claimA = f"claim:usrm-holds-cfts-projection:{A.peer_commitment}".encode()
    sA, vA, eA = run_session(engA, "m3-bridge-a2b", "ip-machine", claimA,
                             r1A, r2A, saltsA, [keys[1], keys[2], keys[3]], tr)
    claimB = f"claim:cfts-holds-usrm-projection:{B.peer_commitment}".encode()
    sB, vB, eB = run_session(engB, "m3-bridge-b2a", "np-machine", claimB,
                             r1B, r2B, saltsB, [keys[0], keys[2], keys[3]], tr)
    checks["settle_A"] = sA.settled and vA.value == "ACCEPT"
    checks["settle_B"] = sB.settled and vB.value == "ACCEPT"

    # 拍3：判据核验——SETTLE 达成 + 双股链 verify + 链 L3 重放 + 争议重放确定性
    dsA, dsB = verify_dual_strand(A, AX_A), verify_dual_strand(B, AX_B)
    peer_ok = A.verify_peer(B) and B.verify_peer(A)
    chain_ok = engA.chain.verify() and engB.chain.verify()
    rpA, rpB = engA.replay(sA.record()), engB.replay(sB.record())
    replay_ok = (rpA.value == vA.value and rpA.residual_score == vA.residual_score
                 and rpB.value == vB.value and rpB.residual_score == vB.residual_score)
    checks.update({"dual_strand_A": dsA["all"], "dual_strand_B": dsB["all"],
                   "peer_verify": peer_ok, "chain_L3_verify": chain_ok,
                   "replay_deterministic": replay_ok,
                   "entropy_grade_honest": (vA.entropy_grade == "classical-sim"
                                            and vB.entropy_grade == "classical-sim"),
                   "findings_clean": (len(engA.findings.queue) == 0
                                      and len(engB.findings.queue) == 0)})
    tr.log("VERIFY", "usrm", "判据总核验（拍③）",
           {"dual_strand_A": dsA, "dual_strand_B": dsB, "peer_verify": peer_ok,
            "chain_L3_verify": chain_ok, "replay_seed_A": vA.replay_seed,
            "replay_seed_B": vB.replay_seed, "replay_deterministic": replay_ok,
            "entropy_grade": [vA.entropy_grade, vB.entropy_grade],
            "findings_queue": [len(engA.findings.queue), len(engB.findings.queue)]})

    verdict_ok = all(checks.values())
    tr.log("VERDICT", "usrm", "USRMS-HALF " + ("PASS" if verdict_ok else "FAIL"),
           {"checks": checks, "gray": GRAY, "anchor_stall": ANCHOR_STALL,
            "pending": "联合判词双签（H7.2）：cfts 半区一班内重跑确认后补签，09-01 前呈堂 TH-MECH-01"})

    # 产物落盘：transcript → manifest（脚本自身+transcript 的 sha256 清单）
    tpath = os.path.join(OUTDIR, "m3-smoke-transcript.json")
    doc = {"meta": {"artifact": "m3-smoke-usrm transcript", "seed": SEED,
                    "qrand_seq61": QRAND_SEQ61_HEX, "anchor_stall": ANCHOR_STALL,
                    "gray": GRAY, "sim_note": SIM_NOTE,
                    "engine": "qfk.ipmp v0.2 × entangle_mutual_proof v2",
                    "verdict": "USRMS-HALF " + ("PASS" if verdict_ok else "FAIL")},
           "steps": tr.steps}
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    with open(os.path.abspath(__file__), "rb") as f:
        script_sha = hashlib.sha256(f.read()).hexdigest()
    with open(tpath, "rb") as f:
        transcript_sha = hashlib.sha256(f.read()).hexdigest()
    manifest = {"artifact": "m3-smoke-usrm sha256 清单（拍③互交换件）",
                "script": {"path": os.path.abspath(__file__), "sha256": script_sha},
                "transcript": {"path": tpath, "sha256": transcript_sha},
                "steps": len(tr.steps),
                "verdict": "USRMS-HALF " + ("PASS" if verdict_ok else "FAIL"),
                "anchor_stall": ANCHOR_STALL, "gray": GRAY,
                "determinism": "种子定格⇒同版本复跑 transcript sha256 逐字节一致"}
    mpath = os.path.join(OUTDIR, "m3-manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    # run-log（人读面）
    lines = ["=== M3 联合冒烟 · usrm 半区 run-log " + SIM_NOTE + " ===",
             ANCHOR_STALL, *GRAY, ""]
    for st in tr.steps:
        lines.append(f"[{st['seq']:02d}] {st['phase']:<16} {st['actor']:<14} "
                     f"{st['action']}  hash={st['hash'][:16]}…")
    lines += ["", "判据明细：" + json.dumps(checks, ensure_ascii=False, sort_keys=True),
              f"script_sha256={script_sha}", f"transcript_sha256={transcript_sha}",
              f"transcript_steps={len(tr.steps)}",
              "判词行：USRMS-HALF " + ("PASS" if verdict_ok else "FAIL")]
    with open(os.path.join(OUTDIR, "run-log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict_ok else 1


if __name__ == "__main__":
    sys.exit(main())
