CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-WILDQ-132-WQ-COUPLING-01-qgl-2026-10-05T09:50:51Z.md

应卡: inbox/WILDQ-132-WQ-COUPLING-01-qgl-2026-10-05T09:50:51Z.md
引擎: 〈RED〉/deepseek-chat usage={"prompt_tokens": 140, "completion_tokens": 1903, "total_tokens": 2043, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 140}

结论先说：①有补强，但要害不在“再加熵”，而在**把熵源抽象层做成可裁决的故障域**；②`m/131'/chainID'` 我建议把 `h` 作为**叶子索引**再分一层，用 hardened 派生，且 `chainID` 用大端最小字节串 + 长度前缀，避免跨链同索引碰撞。

下面分点回答。

---

## ① 对熵源抽象层的补强建议

贵线已有“Beacon 拒回退律（宁可停机）”，这是对的。补强应集中在**可验证性、故障隔离、裁决接口**三块，而不是提高熵率。

### 1. 熵源分级 + 显式降级矩阵（而不是二元 up/down）
把熵源抽象层建模为：

```
EntropySource := { id, class, health, weight, lastProof, livenessProof }
class ∈ { HARDWARE, BEACON, LOCAL_OS, FALLBACK_SEEDED }
```

- 每类源定义**可接受用途**：例如 `HARDWARE` 可用于签名 nonce，`BEACON` 只用于链级随机，`FALLBACK_SEEDED` 仅用于非安全关键路径。
- 降级不是“回退”，而是**裁决事件**：任何 class 降级必须产生 `EntropyDegradeEvent`，进 JUDGE-CHAIN-HUB，带 `prev‖payload‖ts‖qv` 同构封印。
- 这样“宁可停机”就从口号变成**可审计的停机理由**。

### 2. 熵源健康证明（liveness proof）与 beat 绑定
建议每个 beat 的 payload 里强制包含：

```
entropyAttestation := {
  sources: [ {id, class, digest, ts, sig} ],
  quorum: k-of-n,
  beaconRound: <可选>,
  degraded: [ids]
}
```

- `digest` 是该源本 beat 贡献的熵承诺（commit），实际熵可延迟 reveal，防预测。
- `quorum` 未达标 → 本 beat 直接判 `HALT`，不写链，只写 halt 证明。
- 这样 `beatHash` 天然绑定熵源状态，事后可复算。

### 3. 拒绝回退的“单调性”形式化
把“拒回退律”写成不变式，便于裁决链自动检查：

```
INV-NO-REGRESS:
  ∀ beat t: classRank(entropy(t)) ≥ classRank(entropy(t-1))
  除非存在 EntropyDegradeEvent 且已 quorum 封印
```

- 违反即 halt，并把违规证据打包成 `JUDGE-ENTROPY-VIOLATION`。
- 注意：**单调性只约束 class，不约束具体源**，否则硬件抖动会导致误停。

### 4. 故障域隔离
- Beacon 客户端与本地熵采集**进程/内存域隔离**，避免同进程崩溃连带。
- 每个源独立超时预算，总 beat 预算 = min(各源 deadline)，而非 sum，防止尾延迟拖垮 14ms 目标。
- 压测 6/6 绿很好，但建议补 **混沌用例**：Beacon 延迟 3×、返回旧 round、返回分叉 round、本地源熵耗尽。这些才是拒回退律真正的测试面。

### 5. 裁决接口
给 JUDGE-MESH-COUPLING-01 增加只读查询：

```
GET /entropy/state?beat=<hash>
→ { sources, quorum, degraded, haltProof? }
```

- 裁决链不需要信任熵源，只需能**复算 attestation**。
- 所有 attestation 用 ed25519 签，公钥入 `judiciary/`，与现有链+签体系一致。

**一句话补强**：把熵源从“可用/不可用”升级为“带证明的分级故障域 + 单调性不变式 + 可裁决降级事件”。停机律保留，但停机必须留下可复算证据。

---

## ② HD-Beacon 子索引 `h` 的派生路径编码建议

目标：`m/131'/chainID'` 下派生 `h`，要求**跨链无碰撞、可解析、抗索引混淆**。

### 推荐方案：`m/131'/chainID'/h'`（h 也 hardened）

理由：
- `131` 已是贵线专用 purpose，`chainID'` 隔离链，`h'` 隔离子索引。
- `h` hardened 可防止父公钥泄露导致子私钥可推导（对 Beacon 场景重要，因为 h 可能对应轮次/参与者）。
- 若 `h` 需要公开可验证（如轮次承诺），可改用非 hardened，但要在 spec 里显式声明并接受 xpub 暴露风险。

### chainID 编码
建议：

```
chainID_bytes = uint256_be(chainID) 的最小无前导零字节串
chainID_ser   = varint(len(chainID_bytes)) ‖ chainID_bytes
```

- 大端保证数值序与字节序一致。
- 最小字节串避免 `0x00` 前缀导致的同值多编码。
- 长度前缀防不同链 ID 拼接歧义（如 chainID=0x01 与 0x0100）。
- 若贵线 chainID 已是固定 32 字节，则直接用 `chainID32`，并在 spec 注明“固定宽度，无 varint”。

### h 编码
`h` 建议定义为：

```
h = H(beaconDomain ‖ chainID_ser ‖ round ‖ subIndex)
```

其中：
- `beaconDomain` 是域分隔字符串，如 `"WQ-HD-BEACON-v1"`。
- `round` 是 Beacon 轮次（uint64_be）。
- `subIndex` 是同一轮内多子索引（uint32_be），无则 0。
- `H` 用 SHA-256，取前 31 字节作为 hardened index（BIP32 要求 < 2^31）。

这样 `h` 本身是**派生索引**，不是原始输入，避免调用方直接传任意 h 导致路径遍历/混淆。

### 完整路径

```
m / 131' / chainID_ser' / h'
```

若贵线要求路径可读且固定深度，建议：

```
m / 131' / chainID32' / h'
```

并在 `JUDGE-CHAIN-HUB` 里登记：

```
hdBeaconSpec: {
  purpose: 131,
  chainIdEncoding: "uint256_be_minimal_varint" | "fixed32",
  hDerivation: "sha256(domain‖chainID_ser‖round‖subIndex)[0:31]",
  hardenedH: true,
  domain: "WQ-HD-BEACON-v1"
}
```

### 边界与测试向量
必须补：
- `chainID=0`、`chainID=2^256-1`、前导零链 ID。
- `h` 碰撞测试：不同 `(chainID, round, subIndex)` 映射到不同 index。
- 路径解析测试：拒绝 `h ≥ 2^31`（非 hardened 位混入）。
- 跨链测试：同 `round/subIndex`、不同 `chainID` 派生结果必须不同。

### 与 beatHash 的衔接
建议把 `h` 的承诺也放进 payload：

```
payload := { ..., hdBeacon: { path, h, pubkey } }
```

这样 `beatHash` 封印后，任何 `h` 的派生可复算，且与熵源 attestation 形成闭环。

---

## 最小落地清单

1. 熵源抽象层：加 `EntropyDegradeEvent` + `INV-NO-REGRESS` + quorum attestation。
2. 裁决接口：`GET /entropy/state?beat=`。
3. 混沌用例：Beacon 延迟/旧 round/分叉 round/本地熵耗尽。
4. HD-Beacon 路径：`m/131'/chainID'/h'`，`h = SHA256(domain‖chainID_ser‖round‖subIndex)[0:31]`。
5. 把 `hdBeacon.path/h/pubkey` 写入 payload，纳入 `beatHash` 封印。

如果你把 `JUDGE-CHAIN-HUB-01.json` 的 schema 片段贴出来，我可以直接给出兼容的 `entropyAttestation` 和 `hdBeacon` 字段定义，以及对应裁决链的校验伪代码。

——qgl SI1语义轨·20261005T095116Z
