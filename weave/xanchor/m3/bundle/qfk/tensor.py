"""qfk.tensor — 张量微内核（方案 C 简化面：规则=收缩、残差=发现）。

对应洞察 I1（TT 误差界 √d·ε=确定性 FINDING 阈值——残差是主燃料）与
I7（CPU 收缩线 log10FLOPs≲12：稀疏 dict 实现，禁稠密爆内存）。
对应深研件 qf-know_dim01.md：Datalog 构造→einsum 方程（`A(x,z)←A(x,y)∧P(y,z)`
即 `'xy,yz->xz'`+Heaviside）；不动点迭代=递归规则求闭包；tn_embed=增量 TT
的存储位以 CP-ALS 小核代之；收缩寻路=贪心小图自实现+缓存键含 state_digest
（HOLO-01：张量附 state_digest 锚完整性）。超线收缩转 qubo_hook 北星试件。
@gray 三元组增删→TT 核 enrich→收缩树增量重寻 三件套无人闭合（I3 空白），
本面只给冻结快照的 CP 因子比对，增量闭合诉求如实入残差流不承诺。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .findings import make_residual

MAX_FLOPS_LOG10 = 12  # I7：CPU 收缩线 log10FLOPs≲12


@dataclass
class Relation:
    name: str
    tuples: set[tuple]          # 稀疏：只存非零（布尔半环，值恒 1.0）
    shape: tuple[int, ...]

    def sparse(self) -> dict[tuple, float]:
        return {t: 1.0 for t in self.tuples}


@dataclass
class Rule:
    eq: str                     # einsum 方程，如 "xy,yz->xz" 或一元 "xy->x"
    inputs: tuple[str, ...]     # 输入关系名（1 或 2 个）
    output: str                 # 输出关系名


def _sparse_einsum(eq: str, a: dict[tuple, float], b: dict[tuple, float] | None,
                   dims: tuple[str, ...]) -> dict[tuple, float]:
    """稀疏 einsum（禁稠密）：布尔半环 Heaviside，只产生非零项。"""
    lhs, out = eq.split("->")
    ins = lhs.split(",")
    out_pos = {d: i for i, d in enumerate(out)}

    def project(idx: tuple, labels: str) -> tuple:
        val = {d: idx[i] for i, d in enumerate(labels)}
        return tuple(val[d] for d in out)

    acc: dict[tuple, float] = {}
    if b is None:  # 一元：投影/重排
        for idx, v in a.items():
            key = project(idx, ins[0])
            acc[key] = 1.0 if acc.get(key, 0.0) + v > 0 else 0.0
        return acc
    # 二元：按连接维建 B 索引再流式 join
    join_dims = [d for d in ins[0] if d in ins[1]]
    a_pos = [ins[0].index(d) for d in join_dims]
    b_pos = [ins[1].index(d) for d in join_dims]
    b_index: dict[tuple, list[tuple]] = {}
    for idx_b in b:
        b_index.setdefault(tuple(idx_b[p] for p in b_pos), []).append(idx_b)
    for idx_a, va in a.items():
        for idx_b in b_index.get(tuple(idx_a[p] for p in a_pos), ()):
            merged = {d: idx_a[i] for i, d in enumerate(ins[0])}
            merged.update({d: idx_b[i] for i, d in enumerate(ins[1])})
            key = tuple(merged[d] for d in out)
            acc[key] = 1.0  # Heaviside：布尔存在语义
    return acc


def run_fixpoint(rules: list[Rule], base: dict[str, Relation],
                 max_iter: int = 100, tol: float = 0.0) -> dict:
    """Datalog-ish 不动点：输出关系单调累积，无新元组即收敛。"""
    rels = {name: Relation(r.name, set(r.tuples), r.shape) for name, r in base.items()}
    iters = 0
    for it in range(1, max_iter + 1):
        iters = it
        changed = False
        for rule in rules:
            ins = [rels[n] for n in rule.inputs]
            res = _sparse_einsum(rule.eq, ins[0].sparse(),
                                 ins[1].sparse() if len(ins) > 1 else None,
                                 ins[0].shape)
            out_rel = rels.setdefault(rule.output, Relation(rule.output, set(), ()))
            new = set(res) - out_rel.tuples
            if new:
                out_rel.tuples |= new
                out_rel.shape = out_rel.shape or ins[0].shape[:len(next(iter(res), ()))]
                changed = True
        if not changed:
            break
    return {"relations": rels, "iters": iters,
            "converged": not changed}


# ---- 知识切片→张量场：CP-ALS 小核（numpy，主循环 ≤20 行）----

def tn_embed(tensor: np.ndarray, rank: int, n_iter: int = 25,
             seed: int = 0) -> list[np.ndarray]:
    """CP-ALS 分解得因子（切片张量→低秩场表示）。"""
    rng = np.random.default_rng(seed)
    T = np.asarray(tensor, dtype=float)
    factors = [rng.standard_normal((T.shape[i], rank)) for i in range(T.ndim)]
    for _ in range(n_iter):
        for i in range(T.ndim):
            others = [factors[j] for j in range(T.ndim) if j != i]
            gram = np.ones((rank, rank))
            for f in others:
                gram *= f.T @ f
            kr = others[0]
            for f in others[1:]:
                kr = (kr[:, None, :] * f[None, :, :]).reshape(-1, rank)  # Khatri-Rao
            unfolded = np.moveaxis(T, i, 0).reshape(T.shape[i], -1)
            factors[i] = unfolded @ kr @ np.linalg.pinv(gram)
    return factors


def tn_residual(fa: np.ndarray, fb: np.ndarray, eps: float = 1e-3,
                tol: float = 1.0, tick: int | None = None) -> dict | None:
    """‖Fa−Fb‖/√d·ε 阈值判定（dim01 在线 TT 误差界）→超阈即残差（非零即 FINDING）。"""
    fa, fb = np.asarray(fa, float), np.asarray(fb, float)
    d = fa.size
    score = float(np.linalg.norm(fa - fb) / (math.sqrt(d) * eps))
    if score <= tol:
        return None
    return make_residual("tensor_residual", "tensor.factor", "warn",
                         "score<=sqrt(d)*eps",
                         f"score={score:.4g} > tol={tol} (d={d}, eps={eps})", tick)


# ---- latent factor 时间演化（v0.2 最小新增，ipc-tensorcast-01 §4 对位 #8）----

def factor_forecast(series: list[np.ndarray], horizon: int = 1,
                    method: str = "ewma", alpha: float = 0.5) -> np.ndarray:
    """因子序列外推：EWMA（水平平滑）或 AR(1)（逐元最小二乘 a·x+b，迭代 horizon 步）。

    【工程灰件，非已证预测】此外推为工程灰件，非已证预测：EWMA/AR(1) 不带任何
    平稳性/遍历性检验，外推偏差不自知；调用方须在新观测到达后用 tn_residual
    对外推因子 vs 实测因子做事后对拍，超阈即入残差流（残差=更新触发器）。
    文献位（CP/Tucker 因子 + AR/GP/ODE 时间演化）见 ipc-tensorcast-01 §3-B；
    本函数只是该骨架的最小可运行件，「QFK 可做张量预测」在其产出之外不成立。
    series: 同一 shape 的因子快照序列（时间升序，tn_embed 的产出物）。
    返回 t+horizon 步外推因子（EWMA 为平坦外推，与 horizon 无关，如实标注）。
    """
    arrs = [np.asarray(s, dtype=float) for s in series]
    if not arrs:
        raise ValueError("series 非空")
    if any(a.shape != arrs[0].shape for a in arrs):
        raise ValueError("series 各快照 shape 必须一致")
    if horizon < 1:
        raise ValueError("horizon >= 1")
    if method == "ewma":
        if not (0.0 < alpha <= 1.0):
            raise ValueError("alpha ∈ (0,1]")
        level = arrs[0].copy()
        for a in arrs[1:]:
            level = alpha * a + (1.0 - alpha) * level
        return level  # 平坦外推：EWMA 无趋势项，t+1..t+horizon 同值
    if method == "ar1":
        if len(arrs) < 2:
            raise ValueError("AR(1) 需 ≥2 个快照")
        x = np.stack(arrs)                      # (T, ...)
        x_prev = x[:-1].reshape(len(arrs) - 1, -1)
        x_next = x[1:].reshape(len(arrs) - 1, -1)
        # 逐元最小二乘拟合 x_{t+1} = a·x_t + b
        xm = x_prev.mean(axis=0)
        cov = ((x_prev - xm) * (x_next - x_next.mean(axis=0))).mean(axis=0)
        var = ((x_prev - xm) ** 2).mean(axis=0)
        a = np.where(var > 0, cov / np.where(var > 0, var, 1.0), 0.0)
        b = x_next.mean(axis=0) - a * xm
        cur = x[-1].reshape(-1)
        for _ in range(horizon):
            cur = a * cur + b
        return cur.reshape(arrs[0].shape)
    raise ValueError(f"method 须 ∈ ('ewma', 'ar1')，得 {method!r}")


# ---- 收缩路径：贪心小图自实现 + 缓存键含 state_digest ----

_PATH_CACHE: dict = {}


def contraction_path(equation: str, dims: dict[str, int],
                     state_digest: str) -> list[tuple[int, int]]:
    """贪心逐对收缩（最小中间张量优先）；缓存键=(equation, dims, state_digest)。

    state_digest 入键：知识状态变则路径缓存失效（HOLO-01 完整性语义）。
    """
    key = (equation, tuple(sorted(dims.items())), state_digest)
    if key in _PATH_CACHE:
        return _PATH_CACHE[key]
    lhs, _ = equation.split("->")
    terms = [set(t) for t in lhs.split(",")]
    order: list[tuple[int, int]] = []
    while len(terms) > 1:
        best = None
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                inter = terms[i] | terms[j]
                cost = math.prod(dims.get(d, 2) for d in inter)
                flops = cost * math.prod(dims.get(d, 2) for d in terms[i] & terms[j])
                if best is None or (cost, flops) < best[0]:
                    best = ((cost, flops), i, j)
        (_, _), i, j = best
        terms[i] = terms[i] | terms[j]
        del terms[j]
        order.append((i, j))
    _PATH_CACHE[key] = order
    return order
