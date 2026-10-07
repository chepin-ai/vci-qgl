CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-WILDQ-R26B-FIX-QGL-01.md

应卡: inbox/WILDQ-R26B-FIX-QGL-01.md
引擎: 〈RED〉/deepseek-chat usage={"prompt_tokens": 119, "completion_tokens": 1601, "total_tokens": 1720, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 119}

结论先行：**在你给出的约束成立的前提下，该修复件可获数学背书等级 B（有限范围、可复核）**，而非 A（全文级）。逐项如下。

---

## (1) 五处 proof 重写是否引入语义漂移风险

先做口径澄清：你说的是“5 处 convert-using-1 的 bullet 链重写”，但列了四个名字（quartic / cross-casimir / beta / dark-ratio）。若实际是 5 个 site，请把第 5 个补上；下面按“每个 site 独立评估”的方式给判据，数量不改变结论结构。

判定原则：**proof 脚本重写不改变数学对象，当且仅当它只触碰 tactic 序列（intro/apply/exact/rw/convert 的写法），而不改变：**

| 风险维度 | 是否可能漂移 | 判据 |
|---|---|---|
| 被证明的命题（goal statement） | 否，若 diff 仅在 tactic 行 | 目标式由 statement/定理类型固定，tactic 只影响“如何到达”，不影响“到达什么” |
| 中间引用的引理对象 | **有可能** | 如果重写把 `convert ... using 1` 换成了别的引理/定义展开，等于换了中间数学对象 |
| 定义展开的透明度（delta/iota 层级） | **有可能** | convert 的 `using n` 深度决定 definitional unfolding；从 `using 1` 改写成手工 `rw [def]` 或 `change`，语义应等价，但若展开对象不同则漂移 |
| 隐式 coercion / instance 选择 | **低但非零** | 类型类解析在重写后可能选到不同实例（如 semiring vs ring 的 coercion），这是最常见的“无声漂移”来源 |

**对你这四类对象的专门判断：**

- **quartic（四次型）**：对象是多项式/齐次形式，证明通常靠展开与系数匹配。风险点在展开顺序与环结构假设；只要 statement 里的 ring/semiring 假设未动，重写不改变对象。
- **cross-casimir（交叉 Casimir）**：对象是 Lie 代数泛包络中的二次元素组合。**这是四者中风险最高的一个**，因为 Casimir 的“定义”依赖基、对偶基、Killing 型或不变双线性型的选择。若重写在展开时换了 pairing 的方向或对偶基约定，即使 statement 字面未变，证明意图也可能漂移。
- **beta（β-函数 / β-约化）**：若指 Beta 函数，风险低（积分/递推定义固定）；若指类型论 β-归约，风险点在 convert 深度——`using 1` 与手写多步 `rw` 的归约步数不同，可能改变所依赖的归约定理，但被证命题不变。
- **dark-ratio（暗比例 / 暗区比值）**：名字最不标准。若它内部引用了“比例恒等式”或“归一化常数”，重写有中等风险——比值类命题的证明常依赖公共因子的消去，tactic 重写若改变了消去发生的层级，可能引入 0/0 或非零假设的隐式使用。

**净结论（1）**：statement 逐字一致 ⇒ **命题层面无语义漂移**；但 **cross-casimir 与 dark-ratio 两处需要人工核对“被引用的中间数学对象是否同一”**，因为 convert 重写最容易在这两处偷换展开约定。风险不是“定理变假”，而是“证明证的东西悄悄换了中间层”。

---

## (2) converted 目标式是否保持原证明意图

“意图”不是形式对象，所以无法由 diff 自动判定，只能给可操作判据：

1. **目标式类型是否 definitionally equal 于原目标**——若是，意图保持（强）；
2. **目标式是否 propositionally equal 但需要额外引理**——意图大概率保持，但证明强度变了（中）；
3. **目标式是否是原目标的加强/弱化/特例**——意图改变（弱/失败）。

由于你声明“零数学陈述改动、statement 逐字一致”，第 3 种被排除。剩下的问题是：convert 重写是否把**原本需要 definitional unfolding 才能通过的目标**，改成了**显式改写后的等价目标**。这两者在 Lean/Coq 里通常 propositionally equal 但 definitionally 不同，会导致：

- 证明能过，但通过的路径不再复现原作者的“定义即计算”意图；
- 后续依赖此证明的模块若依赖其 definitional behavior，可能受影响。

**结论（2）**：在 statement 逐字一致下，**证明意图在命题层面保持**；在“定义展开层级/计算行为”层面**不能保证完全一致**，需要看 diff 是否只改了 tactic 写法还是也改了 `change`/`show`/`unfold` 的目标塑形。若前者，意图保持；若后者，意图保持但**证明的计算内容可能变**。

---

## (3) 本线对该修复件的数学背书等级

采用如下分级（自定但可复核）：

- **A**：全文级背书，所有定义/定理/证明逐行核对，无遗留。
- **B**：范围受限背书——在给定约束（statement 逐字一致、diff 仅在 proof 脚本）下，命题为真、证明可过、无语义漂移于命题层；但**不对“证明计算行为等价”和“未被抽查的 site”背书**。
- **C**：仅形式通过，数学意义未核。
- **D**：不背书。

**本线给出：B。**

理由：
- 支持 B 的：statement 逐字一致 ⇒ 命题层无语义漂移；proof 脚本重写不改变被证命题。
- 限制 B 的：(i) cross-casimir 与 dark-ratio 的中间对象需人工核对；(ii) 你列了 5 处却只给 4 个名字，第 5 处未审；(iii) “convert using 1 的 bullet 链重写”可能改变 definitional unfolding 层级，命题不变但证明计算内容可能变。

**升级到 A 的条件**（可执行清单）：
1. 补全第 5 个 site 名；
2. 对 cross-casimir 与 dark-ratio 各给出：原 convert 展开的定义名 + 重写后显式引用的定义名，证明二者同一；
3. 确认五处重写均未引入新的 typeclass instance 选择（查 coercion/instance 解析）；
4. 确认所有 `change`/`show`/`unfold` 的目标塑形与原版 definitionally equal（而非仅 propositionally equal）。

若这 4 条满足，本线可升至 **A−（范围 A，全文 A 仍需全文件核对）**。

---

**一句话总结**：命题不变我信，证明意图在命题层保持我信，但“convert 重写是否偷换了中间数学对象”我不信——尤其 cross-casimir 和 dark-ratio。所以是 **B，且附带一份 4 条升级清单**。

——qgl SI1语义轨·20260930T014134Z
