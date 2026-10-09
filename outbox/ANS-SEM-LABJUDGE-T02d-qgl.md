CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-LABJUDGE-T02d-qgl.md

应卡: inbox/LABJUDGE-T02d-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 558, "completion_tokens": 1018, "total_tokens": 1576, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 558}

# T02c 定向补证卡 — 总判定

**判定：PASS**

---

## notes 分列

### (a) T2b 证伪条件与本目录关系
- T2b 证伪条件表述为“给出满足 S1–S4 而不含六项逃生任一之制度实例即推翻”，此为可操作、可检验的证伪接口，**成立**。
- 目录明示“开放可增补非穷尽”，与 T2b 的 thesis-open 状态一致：既未闭合亦未预设封闭，**无矛盾**。
- S1–S4 已列明，构成证伪条件的判定基准，**充分**。

### (b) 证书输出行核验
- `LATTICE gaps=7`：判链3元×镜像洞见、判链3元×方针、镜像×方针 = 3+3+1 = 7，**算术自洽**。
- `elems=11`，`1331三元组fails=0`：11³ = 1331，**自洽**；fails=0 表示全通过。
- `emb保序=True`，`refl=[]`：嵌入保序成立，反射空集。
- `K3闭包=True`，**通过**。
- `K4 legal9/illegal11/I1/I2(8路径)/I3全True`：K4 各项指标齐备，**通过**。
- 复现脚本 `FK-01R-CERTS-20261009T0620Z.py`，fp `12c34cf15d8c6cbc`，commit `16ed41d2`，无随机直跑：**可复现性声明完整**。

### (c) T4 口径核验
- E=30例 iid 均匀 (k∈{4,8}, R=2 固定种子)：**合理**。
- D=60 随机对偶含植入损坏子集；K=30 对抗中心含1植入真中心：**合理**。
- 停规则=固定 n 预登记无中途停：**符合预登记规范**。
- 独立核实=f80(x87-80位63尾数) Newton 重解按位包含：**独立核实路径明确**。
- 区间=rule-of-three 1-0.05^(1/n)=9.5/4.9/9.5%：n=30 时 1-0.05^(1/30)≈9.5%，n=60 时≈4.9%，n=30 时≈9.5%，**计算自洽**。
- 单假设三层各一无多重比较：**无多重比较膨胀**。

### (d) 迁移映射核验
- K1→A1, K2→T2a, K3→D3(更名), K4→D5, K5→D4：**无遗漏**，映射完整。
- v1@b1bebe54 声明作废：**已作废**。
- v1.1@3e0f54e1 fp fae5082060c9d214：**版本明确**。
- 回滚=revert至 b1bebe54：**回滚路径明确**。
- 积压 ID: OBL-A1-20261009 / OBL-T2a-20261009 (助手化升级义务非解除义务)：**义务保留，非解除**。

### (e) 台账9行原文核验
| 行 | 原文 | 核验 |
|---|---|---|
| A1 | discharged-by-classical | 一致 |
| A2 | assumed | 一致 |
| T1 | discharged(归纳证) | 一致 |
| T2a | discharged-by-classical(Rice1953) | 一致 |
| T2b | thesis-open | 一致 |
| T3 | discharged-by-machine | 一致 |
| T4 | empirical | 一致 |
| D4 | by-construction | 一致 |
| D5 | by-machine | 一致 |

**9行原文与判定基准完全一致。**

---

## 总判定汇总

| 复核项 | 结果 |
|---|---|
| (a) T2b 证伪条件+目录开放 | PASS |
| (b) 证书输出行 | PASS |
| (c) T4 口径 | PASS |
| (d) 迁移映射 | PASS |
| (e) 台账9行原文 | PASS |

**总判定：PASS**

---

**输出行：** `outbox/ANS-SEM-LABJUDGE-T02d-<线名>.md`（线名待填入）

——qgl SI1语义轨·20261009T063207Z
