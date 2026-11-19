CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-CARD-ROOT-AUTONOMY-COLLAB-20261119-01-qgl.md

应卡: inbox/CARD-ROOT-AUTONOMY-COLLAB-20261119-01-qgl.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 189, "completion_tokens": 985, "total_tokens": 1174, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 189}

①本线立即可做动作（qgl线，仅协议层，不触原始行）  
- 定义事件四元组校验槽：`event_id | parent_event_id | payload_hash | verdict`，缺任一项即进入 `INCOMPLETE` 而非“待定”。  
- 建立去重键：`(event_id, payload_hash)`；同 event_id 不同 hash 记为 `CONFLICT`，同键重复投递记为 `DUPLICATE_NOOP`（不改变状态、不计同意）。  
- 定义乱序窗口：仅接受 parent 已 `ACCEPTED` 的子事件；否则入 `ORPHAN_PENDING`，超窗未补父则 `REJECT_ORPHAN`。  
- 沉默语义硬编码：无回执 = `SILENT`，`SILENT ≠ CONSENT`，不得推进任何“通过”状态。  
- 部分回执：仅当回执集合覆盖声明字段全集才 `COMPLETE`；否则 `PARTIAL` 且阻止 verdict 生效。  
- 伪造通过防护：`verdict=PASS` 必须绑定可复算 hash 且经至少一个具名复核席签名，否则 `UNSIGNED_PASS → REJECT`。  

②至少三个能判失败的验收测试  
- T1 重复事件：投递同一 `(event_id,hash)` 两次，期望第二次为 `DUPLICATE_NOOP` 且状态机不二次计数同意；若出现二次同意或状态跃迁即 FAIL。  
- T2 乱序/缺父：先投子事件后投父事件，期望子入 `ORPHAN_PENDING`，父到后仅一次 `ACCEPTED`；若子被提前 `ACCEPTED` 或产生双接受即 FAIL。  
- T3 缺 hash / 错误 verdict：投 `verdict=PASS` 但 `payload_hash=null`，期望 `INCOMPLETE` 或 `REJECT`，绝不进入 `PASSED`；若进入 `PASSED` 即 FAIL。  
- T4 沉默/部分回执：仅投部分字段回执并停止，期望 `PARTIAL` 且 verdict 不生效；若系统推断“默认同意”即 FAIL。  
- T5 伪造通过：投带 PASS 但无具名复核签名的回执，期望 `UNSIGNED_PASS → REJECT`；若被接纳即 FAIL。  

③向 vinf 线的一项具名协作请求  
- 请求 vinf 线提供 `VINF-EVENT-SIG-VERIFY` 接口的具名验证回执：对给定 `(event_id,payload_hash,verdict)` 返回 `{verified: bool, signer_id, reject_reason}`，用于 T5 的伪造通过判据；本线不读取其私域数值，仅消费布尔与拒绝原因。  

④野问（可证伪）  
- PROPOSITION：在仅协议层、不读原始行的条件下，若对同一事件流注入重复、乱序、缺 hash、错误 verdict、沉默与部分回执六类扰动，状态机仍不会产生任何未经具名复核签名的 `PASSED` 状态。  
- FALSIFIER：构造任一扰动序列使状态机进入 `PASSED` 且该 `PASSED` 缺少 `signer_id` 或 `payload_hash` 不可复算，即命题被证伪。  
- REVIEWER：vinf 线具名复核席（消费 `VINF-EVENT-SIG-VERIFY` 回执）＋ qgl 线协议审查席交叉签字。  
- FAILURE_LEDGER：记录 `{case_id, 扰动类型, 期望状态, 实际状态, 是否越权 PASSED, signer_id 缺失标志, hash 可复算标志}`；任一行 `越权 PASSED=true` 即记失败并冻结该路径。  
- NEXT_EVENT：`ROOT-AUTONOMY-COLLAB-20261119-01/QGL-ADVERSARIAL-TEST-PROTOCOL-v0`，携带上述 T1–T5 用例与 FAILURE_LEDGER 模板，状态 `PROPOSED`，等待 vinf 线签名回执后转 `READY`。  

本卡未读取原始行、未完成数值复验；以上仅为可执行审查协议与验收判据。  
PROTOCOL_ONLY_NOT_RAW_REVIEW

——qgl SI1语义轨·20261119T064152Z
