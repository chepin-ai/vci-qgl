"""qfk.chain — 链-哈希脊柱（留证层）。

对应洞察 I2「承诺常态、重证按需」：append 时每条 entry 即 L1 轻承诺（哈希链），
每 TILE=8 条成 tile、每个 tile 落 checkpoint（L2 中证的挂点），争议时 verify()
全量重放即 L3。对应深研件 qf-know_dim04.md（可验索引：tile 化 + checkpoint 入链 +
Merkle inclusion/consistency 双证明）与 qf-know_substrate.md §4 HOLO-01
（H1 prev=全史哈希承诺、H2 checkpoint 对 CHAIN 全体承诺）。
硬约束：链内部承诺全 256-bit（sha256 32B）；alias() 的 12-hex 仅显示别名，
永不入验证路径（本模块一切 verify 函数对非 32B 输入直接拒绝）。
@gray 旧链兼容：genesis checkpoint 可绑定外部旧 12-hex 链头，证据等级字段
如实降级为 "degraded-12hex"——12-hex 承诺抗碰撞强度不足，仅作迁移过渡证据。
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional

TILE = 8  # 每 8 条 entry 成一个 tile（规格钉死）
HASH_LEN = 32  # 链内部全 256-bit


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def canon(obj) -> bytes:
    """确定性序列化：json sort_keys + ensure_ascii=False（规格钉死）。"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def alias(h: bytes) -> str:
    """12-hex 显示别名。仅用于人读界面/日志，**永不入验证路径**。

    本模块所有 verify 函数要求 32B 全长哈希；把 alias 的产出喂给任何
    verify/proof 函数会被长度检查直接拒绝。
    """
    if isinstance(h, str):
        h = bytes.fromhex(h)
    if len(h) != HASH_LEN:
        raise ValueError("alias() 只接受 32B 全长哈希")
    return h.hex()[:12]


def _require_32b(h: bytes, what: str) -> None:
    if not isinstance(h, (bytes, bytearray)) or len(h) != HASH_LEN:
        raise ValueError(f"{what} 必须是 32B（256-bit）全长哈希；12-hex 别名禁止入验证路径")


def merkle_root(leaves: list[bytes]) -> bytes:
    for lf in leaves:
        _require_32b(lf, "merkle leaf")
    if not leaves:
        return sha256(b"qfk:empty")
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [sha256(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def merkle_path(leaves: list[bytes], idx: int) -> list[tuple[bytes, str]]:
    """tile 内 inclusion 路径；side='L' 表示兄弟在左。"""
    if not (0 <= idx < len(leaves)):
        raise IndexError("leaf index out of range")
    path: list[tuple[bytes, str]] = []
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        sib = idx ^ 1
        path.append((level[sib], "R" if sib > idx else "L"))
        idx //= 2
        level = [sha256(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return path


def merkle_verify(leaf: bytes, path: list[tuple[bytes, str]], root: bytes) -> bool:
    _require_32b(leaf, "merkle leaf")
    _require_32b(root, "merkle root")
    cur = leaf
    for sib, side in path:
        _require_32b(sib, "merkle sibling")
        cur = sha256(sib + cur) if side == "L" else sha256(cur + sib)
    return cur == root


@dataclass
class Entry:
    seq: int
    ts: float
    domain: str
    payload: bytes
    prev: bytes  # 32B
    hash: bytes = b""  # 32B，compute_hash() 填充

    def body(self) -> dict:
        return {
            "seq": self.seq,
            "ts": self.ts,
            "domain": self.domain,
            "payload": self.payload.hex(),
            "prev": self.prev.hex(),
        }

    def compute_hash(self) -> bytes:
        _require_32b(self.prev, "entry.prev")
        return sha256(self.prev + canon(self.body()))

    def to_dict(self) -> dict:
        d = self.body()
        d["hash"] = self.hash.hex()
        return d


@dataclass
class Checkpoint:
    epoch: int
    tile_roots: list[bytes]
    root: bytes
    prev_checkpoint_root: bytes
    beacon_anchor: Optional[str] = None  # 可选 beacon tick hash（hex），L2 与熵锚交叉
    legacy: Optional[dict] = None  # genesis 旧链绑定（证据降级）

    def to_dict(self) -> dict:
        return {
            "epoch": self.epoch,
            "tile_roots": [r.hex() for r in self.tile_roots],
            "root": self.root.hex(),
            "prev_checkpoint_root": self.prev_checkpoint_root.hex(),
            "beacon_anchor": self.beacon_anchor,
            "legacy": self.legacy,
        }


def _checkpoint_root(prev_cp_root: bytes, tile_roots: list[bytes]) -> bytes:
    _require_32b(prev_cp_root, "prev_checkpoint_root")
    return sha256(prev_cp_root + merkle_root(tile_roots))


class Chain:
    """append-only 哈希链 + tile 化 checkpoint。

    legacy_head: 可选外部旧链 12-hex 链头，仅绑定进 genesis checkpoint，
    evidence_level 如实记为 degraded-12hex（@gray，见模块 docstring）。
    """

    def __init__(self, legacy_head: Optional[str] = None):
        self.entries: list[Entry] = []
        legacy = None
        if legacy_head is not None:
            legacy = {"head": legacy_head, "format": "12-hex", "evidence_level": "degraded-12hex"}
        genesis = Checkpoint(
            epoch=0,
            tile_roots=[],
            root=b"",
            prev_checkpoint_root=sha256(b"qfk:genesis"),
            legacy=legacy,
        )
        genesis.root = _checkpoint_root(genesis.prev_checkpoint_root, genesis.tile_roots)
        self.checkpoints: list[Checkpoint] = [genesis]
        self._pending_anchor: Optional[str] = None

    # ---- L1：每拍轻承诺 ----
    def append(self, domain: str, payload: bytes, ts: Optional[float] = None) -> Entry:
        prev = self.entries[-1].hash if self.entries else sha256(b"qfk:genesis")
        e = Entry(seq=len(self.entries), ts=time.time() if ts is None else ts,
                  domain=domain, payload=bytes(payload), prev=prev)
        e.hash = e.compute_hash()
        self.entries.append(e)
        if len(self.entries) % TILE == 0:
            self._finalize_tile()
        return e

    def anchor_beacon(self, tick_hash_hex: str) -> None:
        """把最近一个 beacon tick 哈希挂到下一个 checkpoint（I2 的分频交叉锚）。"""
        self._pending_anchor = tick_hash_hex

    def _finalize_tile(self) -> None:
        tiles = [self.entries[i:i + TILE] for i in range(0, len(self.entries), TILE)]
        tile_roots = [merkle_root([e.hash for e in t]) for t in tiles]
        prev_cp = self.checkpoints[-1]
        cp = Checkpoint(epoch=prev_cp.epoch + 1, tile_roots=tile_roots, root=b"",
                        prev_checkpoint_root=prev_cp.root, beacon_anchor=self._pending_anchor)
        cp.root = _checkpoint_root(cp.prev_checkpoint_root, cp.tile_roots)
        self.checkpoints.append(cp)

    @property
    def head(self) -> bytes:
        return self.entries[-1].hash if self.entries else self.checkpoints[0].root

    # ---- L3：争议时全量重放 ----
    def verify(self) -> bool:
        prev = sha256(b"qfk:genesis")
        for e in self.entries:
            _require_32b(e.hash, "entry.hash")
            if e.prev != prev or e.compute_hash() != e.hash:
                return False
            prev = e.hash
        # 重放 checkpoint 链（consistency：相邻 root 链）
        cp_root = _checkpoint_root(sha256(b"qfk:genesis"), [])
        if self.checkpoints[0].root != cp_root:
            return False
        expected_cps = 1 + len(self.entries) // TILE
        if len(self.checkpoints) != expected_cps:
            return False
        for i, cp in enumerate(self.checkpoints[1:], start=1):
            tiles = [self.entries[j:j + TILE] for j in range(0, i * TILE, TILE)]
            tile_roots = [merkle_root([e.hash for e in t]) for t in tiles]
            if cp.tile_roots != tile_roots:
                return False
            cp_root = _checkpoint_root(cp_root, tile_roots)
            if cp.root != cp_root or cp.prev_checkpoint_root != self.checkpoints[i - 1].root:
                return False
        return True

    # ---- 证明：tile 内 inclusion + checkpoint consistency ----
    def prove(self, seq: int) -> dict:
        if not (0 <= seq < len(self.entries)):
            raise IndexError("seq out of range")
        tile_idx = seq // TILE
        n_tiles = len(self.entries) // TILE
        if tile_idx >= n_tiles:
            raise ValueError("entry 尚未入 tile（未过 TILE 边界），T5 见证处于 pending")
        tile = self.entries[tile_idx * TILE:(tile_idx + 1) * TILE]
        leaves = [e.hash for e in tile]
        cp = self.checkpoints[tile_idx + 1]
        return {
            "entry": self.entries[seq].to_dict(),
            "tile_index": tile_idx,
            "leaf_index": seq % TILE,
            "path": [(s.hex(), side) for s, side in merkle_path(leaves, seq % TILE)],
            "tile_root": merkle_root(leaves).hex(),
            "checkpoint": cp.to_dict(),
        }

    def verify_proof(self, proof: dict) -> bool:
        """独立验证 inclusion（tile 内 Merkle 路径）+ consistency（checkpoint 相邻 root 链）。"""
        body = {k: proof["entry"][k] for k in ("seq", "ts", "domain", "payload", "prev")}
        leaf = sha256(bytes.fromhex(body["prev"]) + canon(body))
        _require_32b(leaf, "proof leaf")
        path = [(bytes.fromhex(s), side) for s, side in proof["path"]]
        tile_root = bytes.fromhex(proof["tile_root"])
        if not merkle_verify(leaf, path, tile_root):
            return False
        cpd = proof["checkpoint"]
        tile_roots = [bytes.fromhex(r) for r in cpd["tile_roots"]]
        if tile_root not in tile_roots:
            return False
        # consistency：从该 checkpoint 的 prev 重算 root，并与本链当前同 epoch 的 root 对比
        recomputed = _checkpoint_root(bytes.fromhex(cpd["prev_checkpoint_root"]), tile_roots)
        if recomputed.hex() != cpd["root"]:
            return False
        epoch = cpd["epoch"]
        if epoch >= len(self.checkpoints):
            return False
        return self.checkpoints[epoch].root.hex() == cpd["root"]

    def entries_of(self, domain: str) -> list[Entry]:
        return [e for e in self.entries if e.domain == domain]
