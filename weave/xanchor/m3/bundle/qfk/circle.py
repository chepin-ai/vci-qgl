"""qfk.circle — 圈签链头（RCCH v0.1 简化面）。

对应洞察 I2（L2 中证：m-of-n 共签 checkpoint.root，全离线可验）与
I4（LLM 只作软层：llm_advice() 产出永不入 verify 路径，权重恒 0）。
对应深研件 qf-know_dim02.md：sigsum witness cosigning 近同构移植——
submitter/log/witness/verifier 消息流压缩为「成员对 checkpoint.root 签
Ed25519 + policy 离线验证 + RECONFIG 链上自指生效（免 DKG）」。
规模钉死 I7：圈≤30（CIRCLE_MAX）；超过仅降级标注不硬拦。
@gray 圈>30：BFT 成熟区外，签名成本与 hung 风险未实证，verify 仍放行
但 policy 自带 oversized 标记；LLM 仲裁合法位=软层建议+残差生产（I4）。
"""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .chain import Chain, Entry, canon, sha256

# CZ-4 角色分层：本上限属「签者圈」（checkpoint 共签角色，BFT 圈 5–30 成熟区），
# 与 field.py 的「写者前沿」（直写角色，≤5）是两个角色类，上限不得混用。
CIRCLE_MAX = 30  # I7：圈≤30（dim02：BFT 圈 5–30 成熟区）


@dataclass(frozen=True)
class Policy:
    m: int
    n: int
    members: tuple[bytes, ...]  # ed25519 公钥（32B raw）
    policy_hash: bytes

    def to_dict(self) -> dict:
        return {
            "m": self.m,
            "n": self.n,
            "members": [p.hex() for p in self.members],
            "oversized": self.n > CIRCLE_MAX,  # @gray 如实标注，不硬拦
        }


def gen_keypair() -> tuple[Ed25519PrivateKey, bytes]:
    sk = Ed25519PrivateKey.generate()
    return sk, sk.public_key().public_bytes_raw()


def make_policy(m: int, members: list[bytes]) -> Policy:
    if not (1 <= m <= len(members)):
        raise ValueError("需要 1 <= m <= n")
    if len(set(members)) != len(members):
        raise ValueError("members 有重复")
    n = len(members)
    body = {"m": m, "n": n, "members": sorted(p.hex() for p in members)}
    return Policy(m=m, n=n, members=tuple(members), policy_hash=sha256(canon(body)))


# ---- v0.2（F-3）：tag 化内部签验件，checkpoint/verdict 两调用面共用 ----
CHECKPOINT_TAG = b"qfk:circle:checkpoint:"
VERDICT_TAG = b"qfk:ipmp:verdict:"  # ipmp m5 verdict 共签域分隔串（钉死）


def _sign(sk: Ed25519PrivateKey, tag: bytes, digest32: bytes) -> bytes:
    """内部签名件：Ed25519(tag‖digest32)。tag 域分隔防跨协议重放。"""
    return sk.sign(tag + digest32)


def _verify(tag: bytes, digest: bytes, sigs: dict[bytes, bytes], policy: Policy) -> bool:
    """内部验证件：≥m 个不同成员有效签 + policy_hash 匹配 → PASS。全离线。

    永不读 llm_advice 产出（I4 硬层一分不让）；policy_hash 由成员集重算，
    防「拿旧圈签名套新政策」。
    """
    if policy.policy_hash != make_policy(policy.m, list(policy.members)).policy_hash:
        return False
    ok = set()
    for pub, sig in sigs.items():
        if pub not in policy.members or pub in ok:
            continue
        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(sig, tag + digest)
            ok.add(pub)
        except Exception:
            continue
    return len(ok) >= policy.m


def sign_checkpoint(sk: Ed25519PrivateKey, cp_root: bytes) -> bytes:
    return _sign(sk, CHECKPOINT_TAG, cp_root)


def verify(cp_root: bytes, sigs: dict[bytes, bytes], policy: Policy) -> bool:
    """≥m 个不同成员有效签 + policy_hash 匹配 → PASS。全离线（薄封装，向后兼容）。"""
    return _verify(CHECKPOINT_TAG, cp_root, sigs, policy)


def sign_verdict(sk: Ed25519PrivateKey, verdict_digest: bytes) -> bytes:
    """ipmp m5 verdict 共签（v0.2，F-3）：与 checkpoint 签域分隔，互不通用。"""
    return _sign(sk, VERDICT_TAG, verdict_digest)


def verify_verdict(verdict_digest: bytes, sigs: dict[bytes, bytes], policy: Policy) -> bool:
    """ipmp m5 verdict 共签核验（v0.2，F-3）：复用 policy_hash 重算防旧圈套新政策。"""
    return _verify(VERDICT_TAG, verdict_digest, sigs, policy)


# ---- RECONFIG：新政策=domain="circle" 的链 entry，自指生效（免 DKG） ----

def reconfig_payload(policy: Policy) -> bytes:
    return canon({"type": "RECONFIG", "policy": policy.to_dict(),
                  "policy_hash": policy.policy_hash.hex()})


def commit_reconfig(chain: Chain, policy: Policy) -> Entry:
    return chain.append("circle", reconfig_payload(policy))


def effective_policy(chain: Chain, genesis_policy: Policy) -> Policy:
    """扫描链上 domain="circle" 的 RECONFIG entry，最新一条自指生效。"""
    import json
    cur = genesis_policy
    for e in chain.entries_of("circle"):
        try:
            body = json.loads(e.payload.decode())
        except Exception:
            continue
        if body.get("type") != "RECONFIG":
            continue
        p = body["policy"]
        cand = make_policy(p["m"], [bytes.fromhex(h) for h in p["members"]])
        if cand.policy_hash.hex() == body.get("policy_hash"):
            cur = cand
    return cur


def llm_advice(question: str, context: dict | None = None) -> dict:
    """LLM 软层占位接口（I4）：权重恒 0，无任何 LLM 调用面。

    产出可入链留证（domain="llm-advice"），但 verify()/任何硬路径永不读；
    生效必经机判或链证。原型内不接模型，固定返回占位建议。
    """
    return {
        "advice": None,
        "weight": 0,
        "note": "placeholder: no LLM wired; verify path never reads this",
        "question_hash": sha256(question.encode()).hex(),
        "context_keys": sorted((context or {}).keys()),
    }
