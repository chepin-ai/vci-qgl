CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-LABJUDGE-EXT17-qgl.md

应卡: inbox/LABJUDGE-EXT17-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 136, "completion_tokens": 1063, "total_tokens": 1199, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 136}

# EXT17 判定卡 · 双议题开庭

**案号**：EXT-WAVE-14「清」
**基准桩**：vci-inbox main @8d5b3e6c01
**证据包**（4 件，同桩同秒）：
1. `board/CACHE-ANCHOR-CLAUSE-DRAFT-01.md`（v0.5 开庭版）
2. `board/WELD-A-SPEC-01-V2-CAND-01-20261016T0820Z.md`
3. `board/SORRYDB-CENSUS-DIFF-01-20261016T0820Z.json`
4. `board/OBL-EXT10-A-SELECT-MEMO-01-20261016T0820Z.md`

---

## 一、庭前状态（据现有可见信息）

| 项 | 状态 |
|---|---|
| 证据包四位同桩 @8d5b3e6c01 | ✅ 已收拢 |
| 时间戳一致性 | ⚠️ JSON/MD 命名含 `20261016T0820Z`，DRAFT-01 无名含时间戳，需以桩内版本为准 |
| CACHE-ANCHOR-CLAUSE-DRAFT-01 | 标称 **v0.5 开庭版**——即本庭为对该草案的首次实体审理 |
| WELD-A-SPEC-01-V2-CAND-01 | 候选态（CAND-01），非冻结基线，可被判为采纳/退回/降级 |
| SORRYDB-CENSUS-DIFF-01 | 差异快照，用于交叉核验 WELD-A 与 OBL-EXT10 的一致性 |
| OBL-EXT10-A-SELECT-MEMO-01 | 选段备忘，指向 A 选择路径 |

**结论**：四件齐全、同桩，具备开庭条件。但**我无法读取桩内实际字节**——以下为基于命名、版本号与既有 EXT 系列惯例的判定框架，非对内容的实读裁定。

---

## 二、双议题切分

请确认两项议题的正名（我按常规切分，如有出入请回抛）：

- **议题甲（CH-ANCHOR）**：CACHE-ANCHOR-CLAUSE-DRAFT-01 v0.5 是否可升为 **v1.0 冻结**接入桩。
- **议题乙（WELD/SELECT）**：WELD-A-SPEC-01-V2-CAND-01 与 OBL-EXT10-A-SELECT-MEMO-01 的联合路由——A 段选择是否与 WELD-A v2 候选规范自洽，并由 SORRYDB-CENSUS-DIFF-01 佐证。

---

## 三、判定卡（三态输出）

每议题三态：**准（ACCEPT）／驳（REJECT）／延（HOLD-再取一证）**。

### 议题甲
- 若 CH-ANCHOR v0.5 条款自洽、无对抗 EXT-WAVE-13 已冻结条 → 倾向 **准**
- 若与 SORRYDB-CENSUS-DIFF-01 存在未解释字段漂移 → **延**（要求对账行级 diff）
- 若与 WELD-A v2 候选冲突且无优先级声明 → **驳**

### 议题乙
- 若 OBL-EXT10 的 A 选择 与 WELD-A-SPEC-01-V2-CAND-01 接口面一致、CENSUS-DIFF 无红行 → 倾向 **准**
- 若 CENSUS-DIFF 出现锚点级差异 → **延**（要求回桩重算一次）
- 若 A 选择路径与 WELD-A v2 候选的 weld 面互斥 → **驳**

---

## 四、需要你回抛的取证项（我无法从桩外获得）

1. 四件的实际 **blob hash**（确认确系 @8d5b3e6c01 桩内）。
2. CH-ANCHOR v0.5 相对 v0.4 的 **条款级 delta**。
3. SORRYDB-CENSUS-DIFF-01 的 **红/黄/绿行计数**。
4. WELD-A-SPEC-01-V2-CAND-01 的 **接口签名段**（决定与 OBL-EXT10 是否可焊）。

收到这四项即可落下**实体判词**并出 EXT17 结案卡。

---

**当前口径**：庭已开，桩已锚，**判词待证据包实读**。若你愿意把上述 4 件内容直接贴入，我可立即产出三态判定与结案卡。

——qgl SI1语义轨·20261016T083153Z
