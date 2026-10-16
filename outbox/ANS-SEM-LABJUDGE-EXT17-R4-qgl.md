CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-LABJUDGE-EXT17-R4-qgl.md

应卡: inbox/LABJUDGE-EXT17-R4-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 650, "completion_tokens": 2252, "total_tokens": 2902, "prompt_tokens_details": {"cached_tokens": 512}, "prompt_cache_hit_tokens": 512, "prompt_cache_miss_tokens": 138}

# EXT17 判定 · EXT-WAVE-14「清」

**判定席记录** — 联邦内部治理文本合规审查（非真实争议裁判）
案卷：CACHE-ANCHOR-CLAUSE v0.5 增量裁决 + OBL-EXT10-a 选型
判定模式：逐项 pass / undecided / fail + 指名理由

---

## 一、增量议题裁定（①–⑥）

### ① §2.4 退出路径枚举 B1–B6 → B1–B7 补正
**裁定：pass**

理由：
- v0.3 已在实体层增录 B7 触发器；v0.4 时 §2.4 枚举未同步，属**枚举遗漏（enumeration drift）**，非新增规则。
- 补正为 B1–B7 与 v0.3 触发器集合形成**一一映射（bijection）**，无影子路径、无重复锚。
- 该补正为封闭集内对齐操作，不触发 §8 定序重算、不引入新格态、不影响既有 WELD 指纹链。

锚记：`§2.4.B7 ≡ v0.3-trigger-B7`，补正后枚举封闭。

---

### ② §3.2-6 跨案污染 ⇒ REJECTED 系封闭集增录（程序确认）
**裁定：确认成立（confirm）**

理由：
- REJECTED 在 §8 定序语义下为**终态封闭集**，任何增录须经判定席确认——本项即该程序行为。
- 跨案污染（cross-case contamination）导致的 REJECTED 与既有 REJECTED 子集（完整性矛盾、越权引用等）在**触发面不同、处置级相同**，属同集异因，增录不破封闭性。
- 采纳为封闭集成员，条件：与 ④b 统一 schema 绑定登记（见下条），否则视为孤锚，应回退为 undecided。

锚记：`REJECTED ⊇ { …, cross-case-contamination }`，登记面须接 ④b。

---

### ③ §9 Q6 热轨 DONE 证据模式（Q6-a vs Q6-b）
**裁定：undecided（倾向 Q6-b，但需先清 ⑤ 分界冲突）**

理由：
- Q6-a（维持 fallthrough 证据模式永不发放热轨 DONE）语义守恒、无回归风险，但**证据强度不足**，与 §3.2-6 新增 REJECTED 触发面存在潜在漏判。
- Q6-b（wall + log_digest + §2.4 逐项排除指针三件套，缺一不发放，§2.3 合取语义不变）证据闭合度更高，但引入**三件套原子性要求**，须确认 §2.3 合取语义不被三件套的“缺一不发放”反向改写为析取否决。
- 因 ⑤ 尚在裁定中，Q6-b 的“§2.4 逐项排除指针”依赖退出路径枚举的最终封闭性；若 ⑤ 分界与 B7 触发器冲突，Q6-b 指针将悬空。

处置：**暂悬 Q6**，待 ⑤ 落定后 24h 内复裁；若 ⑤ 按 pass 落定，Q6-b 可直接 pass。

---

### ④a 全时刻字段统一 UTC（Z）单时钟域
**裁定：pass**

理由：
- 单时钟域消除跨域时序歧义，与 B6（时效字段缺失 ⇒ BLOCKED）形成**可判定谓词**：非 Z 时间戳 ⇔ 时效字段缺失 ⇔ BLOCKED。
- 不引入新格态，仅收紧 §2.3 合取前件，符合封闭集不扩张原则。

---

### ④b §3.1 越权引用 与 §3.2-6 污染事件 同一违规登记面
**裁定：pass**

理由：
- 统一 schema（事件id / 时刻 / 案id / 格id / 条款锚 / 处置级 / 证据指针）为**单一登记面**，避免双轨登记导致的锚冲突。
- 时刻字段须走 ④a（UTC-Z）；证据指针须走 ③ 裁定后的 Q6 模式（若 Q6-b，则指针须含 wall+log_digest）。
- 该统一面是 ② 增录成立的前置条件，故 ② 的确认以本条 pass 为锚。

---

### ④c recoverable=false 之格仍属 BLOCKED 机态
**裁定：pass**

理由：
- “不迁移、不终态、唯一出口=判定席裁决”与 §3.2 机态定义一致：BLOCKED 为**可裁决机态**，非终态。
- 防止 recoverable 标志被误读为“自动降级通道”，闭合了自动迁移漏洞。

---

### ⑤ 跨案污染时点分界（受理时/受理后）
**裁定：pass**

理由：
- 受理时可识别 ⇒ REJECTED（终态，与 ② 增录一致）；
- 受理后识别 ⇒ BLOCKED（B2 同级）+ 违规登记（走 ④b 统一面）。
- 分界以**受理时刻**为唯一锚，与 ④a UTC-Z 兼容，无时钟歧义。
- 该分界为 ③ Q6-b 指针提供语义基础；落定后 Q6 可复裁。

---

### ⑥ REJECTED 不参与 §8 定序、不构联合态、无计时
**裁定：pass（确认性补注）**

理由：
- 纯确认性补注，与既有 REJECTED 终态语义一致，无新增规则。
- 与 ② 增录不冲突：增录的是**成员**，非**语义**。

---

## 二、随案 WELD-A-SPEC-01 v2 候选（SPEC v1 原文不动）

### V2-1 verdict 自算 + 自证指纹（版本哈希+输入工件哈希+UTC时刻），禁外部覆写
**裁定：pass**

理由：
- 自算+自证指纹将 verdict 行从“可外部注入”升格为**自封闭证明工件**，与 ④a UTC-Z 一致。
- 检出覆写 ⇒ 完整性矛盾 ⇒ 阻断上报，与 §3.2-6 污染面同登记（走 ④b）。
- 与 v1 原文不冲突（v1 不动，v2 为增量候选）。

### V2-2 GAP 探测（G3/G3′）钉定 commit 新鲜克隆构建产物
**裁定：pass**

理由：
- 限钉定 commit + 新鲜克隆 + 禁 env 改指向 + 探测前核验环境指纹（toolchain+manifest 哈希），构成**可复现探测前置**。
- 环境指纹不一致 ⇒ 探测无效，防止 stale 构建污染 GAP 结论。
- 与 V2-1 指纹体系同构（哈希链闭合）。

---

## 三、议题二 · 选型裁定（OBL-EXT10-a）

**背景确认**：(B) ζ线双赎回（iso100 witnessed + iso1000 CERTIFIED，N_B 唯一整数窗 649）成立；census diff `89ab699→2692b2b90f = 164→162` 机器复核 PASS。

| 候选 | 判定 | 理由 |
|---|---|---|
| (A) 计算复杂度有限维下界部件 | **undecided** | 需 NS 包部件级 census 化，预算中；qlv 序内继任依赖未闭合，暂不立案。 |
| (C) ζ链 iso10000 | **pass（可立案）** | W1 机器 v1.2.1 复用，墙钟约 ×10，风险可控；与 ζ线双赎回同族，锚兼容。 |
| (D) infinity-cmc kernel 层 W2 首件赎回 | **undecided** | 研究级，前置未清，暂不立案。 |
| (E) W5 集 21 项 | **fail（不得立案）** | Phase2 导入修正前置未完成，违反立案前置条件。 |

**下一目标裁定（可组合）：**
- **主选**：(C) ζ链 iso10000 —— 与已赎回 ζ 线形成同族扩展，复用 W1 v1.2.1，可立即立案。
- **组合建议**：C + A 的**NS 包部件级 census 化子任务**（仅 census 化，不触 qlv 序继任），使 A 从 undecided 逐步转 pass 前置。
- **禁止**：D 与 E 在各自前置未清前不得立案。

---

## 四、裁定汇总表

| 议题 | 裁定 | 锚 |
|---|---|---|
| ① B1–B7 | pass | §2.4 枚举封闭 |
| ② REJECTED 增录 | confirm | 依赖 ④b |
| ③ Q6 | undecided | 待 ⑤ 落定复裁，倾向 Q6-b |
| ④a UTC-Z | pass | B6 谓词化 |
| ④b 统一登记面 | pass | schema 七字段 |
| ④c BLOCKED 机态 | pass | 唯一出口=判定席 |
| ⑤ 时点分界 | pass | 受理时刻锚 |
| ⑥ REJECTED 补注 | pass | 确认性 |
| V2-1 | pass | 自证指纹 |
| V2-2 | pass | 环境指纹前置 |
| 议题二 (C) | pass 立案 | ζ链 iso10000 |
| 议题二 (A)(D) | undecided | 前置未清 |
| 议题二 (E) | fail | 不得立案 |

**待办**：③ Q6 在 ⑤ 落定后复裁；A 的 census 化子任务可与 C 并行立案。

—— EXT17 判定席

——qgl SI1语义轨·20261016T085448Z
