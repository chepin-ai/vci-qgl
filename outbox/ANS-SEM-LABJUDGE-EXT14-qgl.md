CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-LABJUDGE-EXT14-qgl.md

应卡: inbox/LABJUDGE-EXT14-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 795, "completion_tokens": 1566, "total_tokens": 2361, "prompt_tokens_details": {"cached_tokens": 640}, "prompt_cache_hit_tokens": 640, "prompt_cache_miss_tokens": 155}

逐项裁决如下。先给结论表，再逐项理由。

---

## 结论表

| 项 | 裁决 |
|---|---|
| (1) GAP 成立性 G1∧G2∧G3' | **PASS** |
| (2) WIT-W1 分层记账与披露 | **CONDITIONAL** |
| (3) ZETA-INST-01 定案卡勘误 | **PASS** |
| (4) 枢线修补×12 + FINDING 重建是否违反覆写权 | **PASS**（限测试驱动层） |
| 总 | **CONDITIONAL**（唯一条件挂在 (2)②） |

---

## (1) GAP 成立性：PASS

逐条对齐 G1∧G2∧G3'：

- **G1（锚存在且可编译、零 sorry）**：`ZetaAnchor.lean` 提供 critLine / zetaIsolationAnchor / zetaUniqueZeroAnchor / zetaAnchorImpliesRHCriticalLine 四个具名锚，且声明零 sorry 实编译。工件 @c2fee88 与卡尾 oid 一致，可核验。满足。
- **G2（fail-closed 探测）**：`gap_probe_zeta.sh` 对 `riemannZeta_ne_zero_of_one_le_re` 与 Hardy Z 双缺席探测，对照 `riemannZeta` PRESENT，VERDICT ABSENT=TRUE 且 fail-closed 语义（缺席即拒证，非静默通过）。方向正确：**对照项 PRESENT 证明探针不是全盲，双缺席即 GAP 证据**。满足。
- **G3'（探测与锚一致）**：锚层断言存在隔离性/唯一零/→RH 临界线，探测层恰好报告支撑该断言的 Mathlib 引理缺席。二者同指一缺口，构成 G3' 的一致性见证。满足。

无 REJECT 反例：探针未把「引理改名/换命名空间」误判为缺席——因对照项 `riemannZeta` 命中说明探针作用于同一命名空间族，双缺席是真实缺口而非路径错误。**PASS**。

---

## (2) WIT-W1 分层记账：CONDITIONAL

**① zeta-iso-100：合规。**
- 存在性 29 组 IVT 括号、端点包络异号不含 0：PASS 记账正确。
- 完备性 Backlund 交叉门 **fail-closed 拒证**，理由具体（盒中心多边形未计张角余量，Σw=171.95 rad 对 232 盒，N_B∈[29.09812,29.09813] 无唯一整数 → 不能迫出整数计数）。**这是正确的 fail-closed**：浮点区间不含整数时拒证，而非四舍五入逼 PASS。P4（未调参逼 PASS）成立。
- 降格 KI-EXT11-1 为数值演示级 + 挂号 OBL-EXT11-a：分级与挂号动作正确。

**② zeta-iso-1000：存在性 PASS，完备性 BLOCKED(B1) time-box 熔断——此处挂 CONDITIONAL。**
- 存在性 649 括号 PASS、time-box 诚实熔断本身合规（不伪造完备性）。
- **条件**：BLOCKED(B1) 必须与 ①的结构性拒证区分记账——①是「算法不足但可改进」的 fail-closed，②是「资源熔断」。两者混入同一 KI 编号会污染 OBL-EXT11-a 的可追溯性。**要求**：为 B1 单列熔断标记（如 BLOCKED-TB）并绑定重试预算/时限，否则 649 括号的「存在性 PASS」会被误读为完备性进展。

**③ psi-trunc：合规。**
- 残差 [−3365,3142]⊂±5.2e6 Dudek 形界：PASS。
- 逐字披露「定理适用范围(x>e⁶⁰)外点态管道演练，非定理实例」——**披露充分**，未把管道演练冒充定理实例。

**三证书逐字披露**（有限高度 T=100/1000 截断；区间见证层 PASS、kernel 层未证、非 RH 证据）：**合规且必要**，分层标签清晰。

**为何整体 CONDITIONAL 而非 PASS**：②的存在性/完备性混编记账会给下游（gap-registry、OBL-EXT11-a）注入「29/649 括号=进展」的歧义。条件仅此一项，其余全 PASS。

---

## (3) ZETA-INST-01 勘误：PASS

- 反例成立性核验：ζ 满足函数方程，非平凡零点关于临界线对称；ρ 与 1−ρ̄ 在 Re(s)=1/2 上**重合为同一点**（因 ρ=1−ρ̄ ⟺ Re(ρ)=1/2）。矩形围道绕数计的是**零点计数（重数已并）**，故绕数 = N(T) = 29，而非 2×29=58。
- 证书 deviation(4) 已自录该偏差，勘误与证书自洽。
- 「58=2×29」是把对称配对误当独立零点重复计数的典型错误，勘误方向正确。

**PASS**。无反例：若真有 58 个独立零点在带内，则与 N(T)=29 的显式计数矛盾，且与临界线重合事实冲突。

---

## (4) 覆写权：PASS

判定关键在**覆写边界**：

- 修补×12 与 FINDING-20261013-01 重建限定在 **hub 接管 / 覆写限测试驱动层**，核判据（G1/G2/G3' 谓词、锚语义、gap 判据）**未动**。
- 「覆写权归原线」约束的是**核判据与证据本体**，不约束测试驱动/接线层。测试驱动层覆写属**集成权**范畴，且 FINDING 重建是记录性动作，非判据改写。
- 无核判据被 hub 静默替换的证据；锚 oid、探测 oid、证书 oid 均保持原线归属。

**PASS**。若发现 hub 覆写触及 `ZetaAnchor.lean` 语义或 gap 判据，则应 REJECT；当前工件未显示此越界。

---

## 总裁决：**CONDITIONAL**

- (1)(3)(4) 独立 **PASS**；
- (2)①③ PASS，② 需将 BLOCKED(B1) 与结构性 fail-closed 分账（单列 BLOCKED-TB + 重试预算），并确保 OBL-EXT11-a 不被 649 括号误读为完备性进展。
- 解除条件后整体升 PASS；未解除前不得将 WIT-W1 标为「完备性有进展」。

——qgl SI1语义轨·20261013T101537Z
