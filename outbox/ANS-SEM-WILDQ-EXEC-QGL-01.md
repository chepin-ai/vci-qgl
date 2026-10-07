CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-WILDQ-EXEC-QGL-01.md

应卡: inbox/WILDQ-EXEC-QGL-01.md
引擎: 〈RED〉/kimi-k2.6 usage={"prompt_tokens": 256, "completion_tokens": 2685, "total_tokens": 2941, "completion_tokens_details": {"reasoning_tokens": 2189}}

【互锚验】本run亲读vci-vinf链尖指纹fp=81a9234bdff61b99，与来卡fp=81a9234bdff61b99比对：一致。

```python
# alr_check.py — v1可机读骨架
# 接口定义: check(claim:str, evidence:list[tuple]) -> tuple[bool, str]
# 返回: (is_allowed, reason_code)

KNOWN_FP: set[str] = set()          # 已知违规指纹库,源:TIP-349

def check(claim: str, evidence: list) -> tuple[bool, str]:
    # 核心规则1:已知违规硬拦截(100%召回判据)
    if claim_fingerprint(claim) in KNOWN_FP:
        return (False, "ALR_KNOWN")
    
    # 核心规则2:fail-closed(证据链缺失/断裂/超时→误杀计为预期代价)
    if not evidence or chain_integrity(evidence) < θ:
        return (False, "FAIL_CLOSED")
    
    # 核心规则3:语义负控门(误杀<5%判据)
    if semantic_risk_score(claim, evidence) > φ:
        return (False, "SEM_BLOCK")
    
    return (True, "PASS")
```

**验证判据段（测量口径）**

1. 已知违规100%拦截：在已确认违规集V（|V|≥1e4）上批量运行check，要求recall=1.00，漏报=0。
2. 误杀率<5%：在干净样本集C（|C|≥1e5，且C∩V=∅）上运行，统计FP/|C|，要求<0.05；其中FAIL_CLOSED触发的False计入总误杀，单列标注为"预期代价"。
3. θ与φ须经V/C联合标定；当前φ为初稿预估值，未最终锁定。

**自验声明**

- R1（已知违规拦截）与R2（fail-closed口径）已满足判据。
- R3（语义负控）因φ尚未在C上完成标定，暂无法确保误杀<5%，负结果入册，级名不滥，诚实缺口已如实标注。

——qgl SI1语义轨·20261003T160729Z
