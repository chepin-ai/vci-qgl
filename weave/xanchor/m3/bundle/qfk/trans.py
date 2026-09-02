"""qfk.trans — 四语域互译契约（proof 五档谱系的落地面）。

对应洞察 I4（LLM 生成+符号机判过滤：T4 当闸不当证——ITPEval 实证
type-check 仅确认 54% 真等价）与 I1（未接档位即残差生产：T1/T2/T3 hook
返回 proof_tier_unavailable，非 ∅ 残差入引擎）。
对应深研件 qf-know_dim05.md §1：trans(src,dst,payload,ctx)->{artifact,
proof,residual}；L0 NL/L1 LEAN/L2 code/L3 chain；实装 T4（ast.parse+
py_compile 闸）与 T5（链见证：artifact hash 入链+inclusion proof），
T5 与 T1–T4 正交互补、不可互替——T5 只证存在性/完整性/来源。
残差 schema SHACL 化，五域共用（见 findings.make_residual）。
"""

from __future__ import annotations

import ast
import py_compile
import tempfile
import os

from .chain import Chain, canon, sha256
from .findings import make_residual

LEVELS = {"L0": "natural_language", "L1": "lean", "L2": "code", "L3": "chain"}
IMPLEMENTED_TIERS = ("T4", "T5")
HOOK_TIERS = ("T1", "T2", "T3")  # hook 接口：未接返回残差


def _t4_gate(code: str) -> tuple[bool, str]:
    """T4 闸：ast.parse + py_compile。语法/类型零语义保证（当闸不当证）。"""
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"ast.parse: {e}"
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"py_compile: {e}"
    finally:
        os.unlink(path)
    return True, "ast.parse+py_compile ok"


def trans(src: str, dst: str, payload, ctx: dict) -> dict:
    """trans()->{artifact, proof, residual}。ctx: {tier, chain?, tick?}。"""
    tier = ctx.get("tier", "T5" if dst == "L3" else "T4" if dst == "L2" else "T1")
    tick = ctx.get("tick")

    if tier in HOOK_TIERS:  # T1/T2/T3：hook 未接 → 残差（I1：非 ∅ 入引擎）
        return {"artifact": None,
                "proof": {"tier": tier, "evidence": None, "checker_id": None,
                          "cost_log": "unwired"},
                "residual": make_residual(
                    "proof_tier_unavailable", f"trans:{src}->{dst}", "info",
                    "tier_wired", f"{tier} hook not wired in prototype", tick)}

    if tier == "T4":  # L2 code 闸
        ok, msg = _t4_gate(payload if isinstance(payload, str) else payload.decode())
        artifact = payload if ok else None
        proof = {"tier": "T4", "evidence": msg, "checker_id": "ast+py_compile",
                 "cost_log": "~0", "passed": ok}
        residual = None if ok else make_residual(
            "t4_gate_fail", f"trans:{src}->{dst}", "breaking",
            "ast.parse+py_compile", msg, tick)
        return {"artifact": artifact, "proof": proof, "residual": residual}

    if tier == "T5":  # 链见证：artifact hash 入链 + inclusion proof（只证 provenance）
        chain: Chain = ctx["chain"]
        data = payload if isinstance(payload, bytes) else str(payload).encode()
        ah = sha256(data)
        e = chain.append("trans", canon({"artifact_hash": ah.hex(),
                                         "src": src, "dst": dst, "tick": tick}))
        try:
            incl = chain.prove(e.seq)  # 未过 TILE 边界则 pending（如实返回）
        except ValueError:
            incl = {"status": "pending_tile", "seq": e.seq}
        return {"artifact": data, "proof": {"tier": "T5", "evidence": incl,
                "checker_id": "qfk.chain", "cost_log": "sha256",
                "artifact_hash": ah.hex(), "seq": e.seq}, "residual": None}

    raise ValueError(f"未知 proof tier: {tier}")
