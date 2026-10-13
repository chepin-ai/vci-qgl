CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-EXT14-R2B-EV2-qgl.md

应卡: inbox/EXT14-R2B-EV2-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 443, "completion_tokens": 1416, "total_tokens": 1859, "prompt_tokens_details": {"cached_tokens": 256}, "prompt_cache_hit_tokens": 256, "prompt_cache_miss_tokens": 187}

# EXT14-R2 证据包 2/3 整理与研判

## 一、字段级 diff（v1.0.0@2053f49c ↔ v1.0.1 包A）

| 证书 | 变更字段数 | 数学字段 | 是否零改动 | 明细分项 |
|---|---|---|---|---|
| **iso100** | 3 | 17/17 逐位同 | ✅ | /disclosure、/provenance/generator/sha256、/witness_sha256 |
| **iso1000** | 6 | 16/16 逐位同 | ✅ | 上述3 + /completeness/status、/blocked_subcode、/retry_budget |
| **psi-trunc** | 4 | 11/11 逐位同 | ✅ | /disclosure、/zero_source/sha256、/provenance/generator/sha256、/witness_sha256 |
| **合计** | **13** | **44/44 零改动** | ✅ | — |

**研判**：变更字段全部落在 *元数据/披露/引用哈希* 层——即"包装层"。三个证书共 44 个数学字段（brackets / envelope / winding / residual / block 边界等）逐位一致，说明 v1.0.0→v1.0.1 是**纯 SDK/打包层版本跃迁**，未触碰任何受证明约束的数值实参。这是最干净的一种 diff 形态：*可审计、可回滚、可证伪*。

---

## 二、跨环境重放（envA=重置前#1 ↔ envB=重置后#2）

**运行时对齐**：`python3.12.12 + mpmath1.3.0 + Linux 5.10 lifsea, x86_64` — 两环境栈全同。

### 关键逐位对拍

- **iso100 Backlund 拒证区间**
  ```
  N_B = [29.09812430226496, 29.09812430426496]
  ```
  envA ↔ envB **逐位相同**。<br>
  区间宽度 2×10⁻⁹，不含整数 → 触发 KI-EXT11-1「拒证」行为，符合规范预期（Backlund 计数在该窗口不能唯一钉住零点整数指标）。

- **psi-trunc 残差**
  ```
  r ∈ [-3365.36, 3142.19] ⊆ Dudek 界 ±5195860.44
  ```
  envA ↔ envB **逐位相同**。<br>
  裕度 ≈ 3 个数量级，残差被界严格包住，且跨容器重放数值完全复现 → 证明**确定性浮点路径无环境漂移**。

**结论**：跨容器、跨重置的重放产生**位级一致输出**，说明判据依赖的不是隐式状态（缓存/时区/随机种子/RNG 状态），而是纯函数式数值管线。

---

## 三、包A 核验（envB 实跑）

### CLI verify 结果

| 证书 | ok | 备注 |
|---|---|---|
| iso1000 | **true** | — |
| psi-trunc | **true** | — |
| iso100 | **false** | failed 唯一项 = Backlund 异常：「N_B 区间不含唯一整数——拒证」 |

**研判**：iso100 的 `ok=false` **不是失败，而是设计内的"拒证"路径**——被 KI-EXT11-1 钉档。这正是 Backlund 计数在 2 ns 窗口上不能给出唯一整数指标的**诚实响应**。把它报为 `fail` 反而说明验证器没有把"无法判定"偷偷升级为"通过"。**这是审计友好行为**，不是缺陷。

### pytest

```
41 passed in 1497.81s (0:24:57)
```
全绿，耗时约 25 分钟——与 mpmath 高精度 Backlund/Dudek 类计算的典型成本一致。

---

## 四、双跑闸（确定性再确认）

三证书重签时，在**同进程内同代码连跑两次**，输出**字节级一致**。

- 证据：`run-log-sup01.json`
- 位置：包A `artifacts/witnesses-zeta/`

**研判**：字节级一致 = 强于"数值一致"的确定性证据。排除：哈希盐、时间戳泄漏、字典序扰动、浮点路径抖动、文件系统遍历序。**双跑闸通过**。

---

## 五、整体评估

| 维度 | 结论 |
|---|---|
| 数学不变性 | ✅ 44/44 字段零改动 |
| 跨环境可重放 | ✅ envA↔envB 逐位一致 |
| 判据诚实性 | ✅ iso100 拒证被如实报出，未偷偷升格 |
| 确定性 | ✅ 双跑字节级一致 |
| 运行时对齐 | ✅ py3.12.12 / mpmath1.3.0 / lifsea 全同 |

**总判定**：包A 构成 v1.0.0→v1.0.1 的**零数学改动、满元数据可追溯、跨环境可重放、字节级确定性**的完整证据链。`iso100 ok=false` 是**预期内拒证**，与 KI-EXT11-1 规范一致，不构成回归，也不削弱其余两证书的 `ok=true`。

---

## 六、待决/建议（包 3/3 之前）

1. **拒证语义归类**：建议在 CLI 层区分 `ok=false (reject)` 与 `ok=false (error)`，避免下游 CI 把 KI-EXT11-1 拒证当作红。当前语义由 failed 项文本承载，机器可读性偏弱。
2. **N_B 窗口宽度审计**：2×10⁻⁹ 窗口宽度是否需要随 t 或 N 自适应，值得在包 3/3 里与 Dudek 界的推导阈值一并复核。
3. **run-log 补齐**：`run-log-sup01.json` 建议随包附 SHA-256 摘要，与 witness_sha256 并列，形成"输入哈希 + 输出哈希 + 运行日志哈希"三锚。

请发**包 3/3**，我按同一粒度对拍并做最终封包裁定。

——qgl SI1语义轨·20261013T125542Z
