"""qfk.beacon — 量子锚（熵与时间证人 + 软绑定抽签）。

对应洞察 I6「量子绑定须诚实分层」与 I2「beacon 相位即验证分频器」：
只实装硬绑定（DI 认证熵锚的挂点）与软绑定（leader 抽签），QUBO 留 hook。
对应深研件 qf-know_dim06.md：熵混合用 HKDF(ANU‖drand‖os‖prev, info=str(seq))
抗部分熵降 + 上下文绑定；qrand⊕local 的最强链组合器语义保留在混合输入里。
默认离线模式：ANU/drand 由 os.urandom 模拟并经 prev 演进——**classical-sim**，
不 claim 任何量子性；真客户端类存在但测试零网络（硬约束 1）。
@gray 收缩寻路 QUBO（qubo_hook）= 北星试件，禁性能承诺（dim06 §0-3：
无直接 QUBO 先例，演示价值>性能价值）；leader_draw 是软绑定，经典可替。
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


@dataclass
class BeaconTick:
    seq: int
    qrand: bytes  # 32B
    prev: bytes   # 32B
    hash: bytes   # 32B = sha256(seq‖prev‖qrand)
    source_names: tuple = ()  # v0.2（F-2）：tick() 时快照各源 name，默认 () 兼容旧构造

    def to_dict(self) -> dict:
        return {"seq": self.seq, "qrand": self.qrand.hex(),
                "prev": self.prev.hex(), "hash": self.hash.hex(),
                "source_names": list(self.source_names)}


class OfflineSource:
    """离线熵源（classical-sim）：os.urandom 模拟外部量子源，注释钉死非量子。"""

    name = "offline-classical-sim"

    def fetch(self) -> bytes:
        return os.urandom(32)


class ANUClient:
    """ANU QRNG 真客户端（存在但默认离线；测试不得触网）。"""

    name = "anu-qrng"
    URL = "https://qrng.anu.edu.au/API/jsonI.php?length=32&type=hex16"

    def fetch(self) -> bytes:  # pragma: no cover - 网络路径，测试禁用
        with urllib.request.urlopen(self.URL, timeout=10) as r:
            data = json.loads(r.read().decode())
        return bytes.fromhex("".join(data["data"]))


class DrandClient:
    """drand 真客户端（quicknet；存在但默认离线；测试不得触网）。"""

    name = "drand-quicknet"
    URL = "https://api.drand.sh/52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971/public/latest"

    def fetch(self) -> bytes:  # pragma: no cover - 网络路径，测试禁用
        with urllib.request.urlopen(self.URL, timeout=10) as r:
            data = json.loads(r.read().decode())
        return bytes.fromhex(data["randomness"])


class Beacon:
    """beacon={seq,qrand,prev} 链（substrate §6 母钟的最小面）。

    mode="offline"（默认）：两路外部源皆为 OfflineSource（classical-sim），
    混合式仍是 HKDF(ANU‖drand‖os‖prev, info=str(seq))，prev 每拍演进，
    换真源时无须改调用面。
    """

    def __init__(self, sources: tuple = (OfflineSource(), OfflineSource())):
        self.sources = sources
        self.seq = 0
        self.prev = sha256(b"qfk:beacon:genesis")
        self.ticks: list[BeaconTick] = []

    def tick(self) -> BeaconTick:
        anu, drand = (s.fetch() for s in self.sources)
        local = os.urandom(32)
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

    def phase(self, n: int, p: int) -> bool:
        """点火律 seq%N==p（I2：beacon 相位驱动验证深度档位）。"""
        return self.seq % n == p

    def entropy_grade(self) -> str:
        """熵源认证档（v0.2，F-2，A5）：任一源为 OfflineSource → "classical-sim"。

        只如实报告源组成，不作任何量子性声称："certified" 仅表示无离线模拟源
        在列（源自述非 sim），不等于 DI 级物理认证——硬件实证永不升格为数学保证。
        """
        if any(isinstance(s, OfflineSource) for s in self.sources):
            return "classical-sim"
        return "certified"


def leader_draw(members: list[str], tick: BeaconTick) -> str:
    """确定性公开抽签（软绑定，经典可替——Filecoin/drand 同构先例）。

    同一 (members, tick) 输入必得同一结果；不提供抗操纵证明，仅可复现。
    """
    if not members:
        raise ValueError("members 非空")
    scores = {m: sha256(tick.qrand + m.encode()) for m in members}
    return min(scores, key=lambda m: (scores[m], m))


def qubo_hook(problem: dict) -> dict:
    """收缩寻路 QUBO 北星试件接口（@gray：禁性能承诺）。

    原型不内嵌求解器；仅登记问题摘要入残差流（type="north_star_qubo"），
    是否接 QuantumRings/Quafu 真机由研究队列决定（dim06 §0-3：无直接先例）。
    """
    return {
        "status": "hook_only",
        "residual": {
            "type": "north_star_qubo",
            "focus": "tensor.contraction_path",
            "severity": "info",
            "constraint": "no_performance_promise",  # 北星禁承诺
            "detail": f"QUBO problem registered ({len(problem)} keys); solver not wired",
            "tick": None,
        },
    }
