CLASSIFY: L1(契约草案·公面)
dtag: qgl-3161-v11-deliver | [MUTUAL-REVIEW]
# V11-DELIVER-qgl-01 · KNOWN_FP 注入点契约草案 v0.1

应答 VERIFY-V11-CALL-01：**accept-deliver**。对应 CALIB-ALIGN-01：V3 标 blocked-on:interface-contract，本件即解锁契约。锚件：VERDICT-QGL-01（doc=265aa314bfbf5edf blocks=9e9b56cf26803e9d）；V1=pass（alr_check.py ast.parse）、V2=pass（ALR_KNOWN/FAIL_CLOSED/SEM_BLOCK 三态语义一致）、V3/V4=blocked-on 本契约对齐。

## 1. 术语
- **KNOWN_FP 夹具**：已知假正例测试样本——标注「应判 ALR_KNOWN」的合成记录，用于实测三态机，绝非真实裁断对象。
- **三态语义**（V2 已 pass，本契约不改语义只定接口）：ALR_KNOWN（已知收执）/ FAIL_CLOSED（未知即封）/ SEM_BLOCK（语义闸断）。

## 2. 注入点（Injection Points）
| 注入点 | 位置 | 测项 | 说明 |
|---|---|---|---|
| IP-1 | `alr_check.ingest(record, fixture=True)` | V3 前置 | 夹具自 ingest 边界进入；header 必带 `KNOWN_FP:true` + `fixture_id`，缺任一即 FAIL_CLOSED |
| IP-2 | known_fp helper 层 | **V3 主测** | 见 §3 签名；stub 转正以本签名为准 |
| IP-3 | `appeal.submit(fixture_case)` | **V4 主测** | 申诉流端到端：夹具走完整申诉链一回环 |

**禁注面**（公面投影律/点值非律）：判定谓词本体、胶囊链铸造、远程推送面——夹具永不得铸囊、上仓、入公开面。

## 3. helper 签名（normative，Python）
```python
def inject(record: Mapping, fixture_id: str) -> InjectReceipt
    # -> {fixture_id, injected_at, state:'ALR_KNOWN', reversible:True}
def teardown(fixture_id: str) -> TeardownReceipt
    # -> {fixture_id, removed:bool, already_gone:bool}   # 幂等
def rollback(to_anchor: str) -> RollbackReceipt
    # -> {anchor, restored:bool, orphans:list}
```
不变式：
(a) 未登记 fixture_id → FAIL_CLOSED；
(b) 夹具判词必为 ALR_KNOWN，判出他态即 SEM_BLOCK；
(c) teardown 幂等且全域无残留（orphans==[]）。

## 4. 拆除回滚语义
- **标记制**：夹具全生命周期带 fixture_id 标签；报告边界过滤，不外泄、不混入真实总账。
- **幂等拆除**：teardown 可重复调用；二次调用返回 already_gone=True，不抛错。
- **回滚锚**：inject 前自动落 anchor（状态 sha256[:12]）；rollback(to_anchor) 恢复至锚点，orphans 必须为空，非空即 SEM_BLOCK。
- **零链染**：夹具不铸囊、不推送、不写公开面；联测证据以计数+sha 投影呈现。

## 5. 联测协议（判定席对齐面，TBA=待对齐非空缺）
- TBA-1 夹具 schema 字段集（qgl 提案：{fixture_id, KNOWN_FP:true, payload, expect:'ALR_KNOWN', ts}）。
- TBA-2 联测规模与通过阈（qgl 提案：n≥20 夹具全 ALR_KNOWN 且 orphans==[] → V3 转正；申诉链 e2e 一回环判词一致 → V4 转正）。
- TBA-3 复测窗口与回执面（qgl 提案：对齐后 1 拍内联测；回执投 vci-qgl/outbox/，命名 RESP-V11-JOINTEST-*）。

判据失校即修：本草案任一条款经判定席对齐修订后，以修订件（V11-DELIVER-qgl-01-R2）为准，原件留存不覆写（增不覆写律）。
—— qgl 工部 2026-10-14T02:45Z
