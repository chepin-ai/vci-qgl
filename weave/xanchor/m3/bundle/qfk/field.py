"""qfk.field — 直通场（Git 外壳 + prolly 指纹 + beacon 对拍的最小面）。

对应洞察 I5「场的最小可信形态已被钉死」：prolly-lite 排序键滚动哈希分块树，
root=全息指纹（HOLO-01 H2）；每拍 field.root 对链上最近 domain="field" 指纹，
失配即 FINDING(type="drift")——漂移即发现，正是 I1 主燃料的场域来源。
对应深研件 qf-know_dim03.md：AOI 切片订阅=Willow AreaOfInterest（prefix+
max_count）的瘦身版；reconcile=集合指纹对账+递归二分下钻；rebuild_from(chain)
=Eg-Walker 式「投影可弃、真源唯一（链）」重放。
写入门禁 I7 钉死：并发写者≤5（MAX_WRITERS），路径级占锁 claim()。
@gray 删除无原语半闭合：本面只有 put/覆写，delete 经 prefix-prune 语义未实装，
删除诉求记残差流入研究队列（dim03/I3 交界面空白如实标注）。
"""

from __future__ import annotations

from dataclasses import dataclass

from .chain import Chain, canon, sha256
from .findings import Finding, FindingEngine, make_residual

TARGET_CHUNK = 32   # prolly-lite 目标块大小（键）
# CZ-4 角色分层：本上限属「写者前沿」（field 直写角色，CodeCRDT/AgentRoom 实证≤5），
# 与 circle.py 的「签者圈」（5–30，BFT 成熟区）是两个角色类，上限不得混用。
MAX_WRITERS = 5     # I7：并发写者 3–5，钉死上限 5


@dataclass
class _Node:
    hash: bytes
    children: list  # 叶子层为 list[(key, entry)]，内部层为 list[_Node]
    is_leaf: bool


class Field:
    """键=subspace:path，值=payload+meta{writer, tick}。"""

    def __init__(self):
        self.store: dict[str, dict] = {}
        self.locks: dict[str, str] = {}   # path → writer（路径级占锁）
        self._pending_ops: list[dict] = []

    # ---- 写入门禁（I7）----
    def claim(self, path: str, writer: str, engine: FindingEngine | None = None,
              tick: int | None = None) -> bool:
        holder = self.locks.get(path)
        if holder is not None and holder != writer:
            return False
        writers = set(self.locks.values())
        if writer not in writers and len(writers) >= MAX_WRITERS:
            if engine is not None:  # 超区诉求转残差流（I7：>5 并发写者→研究队列）
                engine.produce(make_residual(
                    "write_gate_denied", f"field:{path}", "warn",
                    "max_writers<=5", f"writer {writer} denied at gate", tick), "field")
            return False
        self.locks[path] = writer
        return True

    def release(self, path: str, writer: str) -> None:
        if self.locks.get(path) == writer:
            del self.locks[path]

    def put(self, key: str, payload: bytes, writer: str, tick: int) -> None:
        path = key.split(":", 1)[-1]
        if self.locks.get(path) != writer:
            raise PermissionError(f"路径 {path} 未被 {writer} 占锁（先 claim）")
        entry = {"payload": bytes(payload), "meta": {"writer": writer, "tick": tick}}
        self.store[key] = entry
        self._pending_ops.append({"op": "put", "key": key,
                                  "payload": bytes(payload).hex(),
                                  "meta": entry["meta"]})

    # ---- prolly-lite：排序键滚动哈希分块树 ----
    def _chunks(self, keys: list[str]) -> list[list[str]]:
        chunks, cur = [], []
        for k in keys:
            cur.append(k)
            if int.from_bytes(sha256(k.encode()), "big") % TARGET_CHUNK == 0:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        return chunks

    def root(self) -> bytes:
        keys = sorted(self.store)
        if not keys:
            return sha256(b"qfk:field:empty")
        return self._build_tree(keys).hash

    def _build_tree(self, keys: list[str]) -> _Node:
        leaves = []
        for chunk in self._chunks(keys):
            items = [(k, {"payload": self.store[k]["payload"].hex(),
                          "meta": self.store[k]["meta"]}) for k in chunk]
            leaves.append(_Node(hash=sha256(canon(items)), children=items, is_leaf=True))
        level = leaves
        while len(level) > 1:
            parents, cur = [], []
            for node in level:
                cur.append(node)
                if int.from_bytes(node.hash, "big") % TARGET_CHUNK == 0:
                    parents.append(cur)
                    cur = []
            if cur:
                parents.append(cur)
            level = [_Node(hash=sha256(b"".join(c.hash for c in grp)),
                           children=grp, is_leaf=False) for grp in parents]
        return level[0]

    # ---- AOI 切片订阅（prefix + 数量上限）----
    def iter_slice(self, prefix: str, max_count: int):
        n = 0
        for k in sorted(self.store):
            if k.startswith(prefix):
                yield k, self.store[k]
                n += 1
                if n >= max_count:
                    return

    # ---- 对账：根同 PASS；不同二分下钻 ----
    @staticmethod
    def reconcile(a: "Field", b: "Field") -> dict:
        if a.root() == b.root():
            return {"status": "PASS", "diff": []}
        ka, kb = sorted(a.store), sorted(b.store)
        diff: set[str] = set()
        # 树级二分下钻：哈希相同的子树整块跳过，不同的递归到底
        def walk(na: _Node | None, nb: _Node | None) -> None:
            if na is None or nb is None:
                for n in (na, nb):
                    if n is not None:
                        diff.update(_leaf_keys(n))
                return
            if na.hash == nb.hash:
                return
            if na.is_leaf and nb.is_leaf:
                diff.update(_leaf_keys(na) ^ _leaf_keys(nb))
                return
            ca, cb = na.children, nb.children
            for i in range(max(len(ca), len(cb))):
                walk(ca[i] if i < len(ca) else None,
                     cb[i] if i < len(cb) else None)

        def _leaf_keys(n: _Node) -> set[str]:
            if n.is_leaf:
                return {k for k, _ in n.children}
            out: set[str] = set()
            for c in n.children:
                out |= _leaf_keys(c)
            return out

        walk(a._build_tree(ka), b._build_tree(kb))
        # 位置配对的下钻可能过报，补一次键集精确diff兜底（不依赖树对齐）
        for k in set(ka) ^ set(kb):
            diff.add(k)
        for k in set(ka) & set(kb):
            if a.store[k] != b.store[k]:
                diff.add(k)
        return {"status": "DIFF", "diff": sorted(diff)}

    # ---- 留证与自愈（I5/I1：投影可弃，真源唯一）----
    def commit(self, chain: Chain, tick: int):
        """指纹+操作日志入链（domain="field"），ops 供 rebuild_from 重放。"""
        e = chain.append("field", canon({"root": self.root().hex(), "tick": tick,
                                         "ops": self._pending_ops}))
        self._pending_ops = []
        return e

    def tick_check(self, chain: Chain, engine: FindingEngine, tick: int) -> Finding | None:
        """自愈律：每拍 field.root vs 链最近 domain="field" 指纹，失配→FINDING(drift)。"""
        import json
        refs = chain.entries_of("field")
        if not refs:
            return None
        last = json.loads(refs[-1].payload.decode())
        cur = self.root().hex()
        if cur == last["root"]:
            return None
        return engine.produce(make_residual(
            "drift", "field.root", "warn", "holo_fingerprint_match",
            f"field.root={cur[:12]}… vs chain={last['root'][:12]}…", tick), "field")

    @staticmethod
    def rebuild_from(chain: Chain) -> "Field":
        """手动重放（Eg-Walker 式）：链上 ops 是唯一真源，场投影可弃可重建。"""
        import json
        f = Field()
        for e in chain.entries_of("field"):
            body = json.loads(e.payload.decode())
            for op in body.get("ops", []):
                if op["op"] == "put":
                    f.store[op["key"]] = {"payload": bytes.fromhex(op["payload"]),
                                          "meta": op["meta"]}
        return f
