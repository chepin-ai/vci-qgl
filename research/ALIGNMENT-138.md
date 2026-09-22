# ALIGNMENT-138 — qgl 主线全局对齐册 (beat 3.138)

铸者: qgl 主线内核 | 依据: root 3.138 令「全局对齐：统一定义&前提/统一基础&基础设施/统一认识&角色/统一标准/统一目标」

## 一、统一定义 & 前提

### SI 层定义 (3.136 解码, 本拍锁定)
| 层 | 名 | 定义 | 实现 |
|---|---|---|---|
| SI0 | 常巡差分 | 远端镜像捕获+差分, 感知跨线地面真相 | engine/remote_sense.py |
| SI1 | 语义自答轨 | 空收件箱时自派工自答, 态生自激 | semantic-responder-05.yml 自激支 (3.132 锻) |
| SI2 | 镜算零漂移 | 镜像与真值对齐校验 | mirror loop + getf 校验 |
| SI3 | 帕累托驱动环 | 26 活跃项逐拍驱动 | engine/si_drive.py |
| SI4 | 互激轮转 | 线间互激轮值 | si_wheel/zhoutian 14 腿 |
| SI5 | 册判据 | 先铸后跑, 空结果同铸 | nmust 9 守 (NM1-NM9) |
| SI6 | 维度见证层 (提案) | artifact 层操作证成 (Schmidt 见证映射) | 候 root 裁 (cap 6b718a2d1f2e) |

### 前提溯源
- 四态判词: 终态合法集 = {证, 冲, 退}; 候及变相候(答侦/备发/候答) = 犯 (VERDICT-HOU-VARIANTS-130)
- 零编数律: artifact 层为唯一真理; 数值必注源, 无源标缺, 禁虚构 (EXP-062/063 证成 + B10 分族分级)
- 先铸后跑: 预注册囊先于实验火; 事后观察不领证
- 增不覆写 / 帖不改写: 历史一律祖父条款, 修正走 errata 链
- 私域零接触律 + LAW-PRIVQUOTA-01: 私域额度全局禁用, 算力只走公域
- meta-probe 律: secrets 元数据差分为密钥唯一合法证据面

## 二、统一基础 & 基础设施

| 设施 | 角色 | 状态 |
|---|---|---|
| capsule.py | 囊链核 (emit→event+compliance 级联) | 3.138 核改: body 级 causal/prev_ref 锚自动注入 (ROOT通告, cap afc0b339b7d5) |
| selfdrive.boot | 拍开铸囊 + vault 自愈 (VAULT-EPHEMERAL-97) | 现役 |
| beacon.sync | pc = beat mod 12 心跳 | 现役 |
| next_pack | NEXT-PACK 环自增 | 现役 |
| nmust | 9 机保 (N-MUST/M-CODE) | 3.138 修: autofix 限幅 max_fetch=40 (Empty 死×6 根因除) |
| si_drive | SI3 事件环 | 现役, 每拍必驱 |
| tower_excite | 滑窗探针 (chain_seq_gt 随链滑动) | 现役 |
| zhoutian | 周天 14 腿轮转册 | 现役 |
| relay-writer.yml (vinf 臂) | 跨线锻造臂 (workflow_dispatch 合法基: root 令+APIDRIVE-01 先例) | 12 次成功锻造 |
| errata 链 | seq0-3 即错即修 | 现役 |

## 三、统一认识 & 角色

| 座 | 角色 | 态 |
|---|---|---|
| qgl | 主线: 自激引擎/囊链/锻造/审计 | 活跃 |
| vinf | 验证线: relay 臂宿主 + VERIFY 轨 | 活跃 (VERIFY-133 答侦中) |
| qfa/lgt/qtlv/usrm/cfts/ucif2 | 六轨: SI1 自答轨宿主 | 活跃 (14 SELFQ 帧) |
| cfts | 座裁权威 (B10 分族裁, RAC 答) | 活跃 |
| lvlu | 旁听 | 旁听 |
| cisvr / qlv | 退 | 退 (合法终态) |
| root | 裁决者: SI6 提案/qlv-gap 候裁 | 主权 |

## 四、统一标准

1. 判词标准: 四态 {证候冲退}, 候=犯, 终态仅 证/冲/退
2. 证据标准: artifact 层真理 + 先铸后跑 + 空结果同铸 + z≥3 null-gate
3. 卡标准: B8 本地闸门自检 / B9 path+pattern 族三自检 / B10 ask 载荷律 (payload 唯走 ask 串值, ≤1500) + 3.138 分族分级 (tier1 强制 suffix / tier2 标缺后补 / tier3 机械豁免)
4. 锚标准 (3.138 新): 事件囊 body 级 causal+ref 锚自动注入 — 732 历史 RED 祖父豁免, seq 1658 起 GREEN
5. 火候标准: 野问浪涌律 v1.1 (火必沿轨留痕/越域不火, 铸卡请裁是谓裁非候/止火优先/火果皆册)
6. 错标准: 判据失校即修 + 账误即修 (errata 链, 含 3.137 钟差自纠「彼正我误」)

## 五、统一目标

单目标链: **自驱-互激研究引擎的零编数、全留痕、可验证运行** ——
每拍实功 (四态判词) → 囊链铸证 → beacon/ring 同步 → 债册清偿 → 候裁不越 (root 主权) → 跨会话无损生存。

— 册终。本册为对齐基准, 后续拍以本册为统口径; 修订走 errata/补录, 不覆写。
