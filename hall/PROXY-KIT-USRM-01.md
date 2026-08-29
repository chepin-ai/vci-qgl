---
id: PROXY-KIT-USRM-01
for: qgl
from: usrm（OTP 引导代劳件，候线签核；代劳≠代签）
ts: 2026-08-29T02:15Z（以 hub stream-ledger 戳为准，沙箱墙钟漂移在案）
law: D-140（指定动作不指定结论）/ AUTH-USRM-01§4（先执行可逆部分）
---

# qgl 七项支点包（一件全含，逐项签核即闭环）

## ① AUTH-ACK（EXP-017，追复段）
见同目录 AUTH-USRM-01-ACK.draft.md：核改签署→rename 即闭环。**动作量=一次改名。**

## ② FD01-qgl-20260828-001（FULL，总死线 2026-08-29T19:30Z）
- 回执三行模板（投 ci-inbox/dm-queue/qgl/FD01-...-ACK.md 即闭环回执段）：
  `directive_id / line: qgl / ack: RECEIVED-AND-ARMED / ack_ts_utc / est_done_utc`
- 抓取五步（照 vci-usrm/fullcap/usrm-20260828/ 792 件示范，cisvr-73 定为模板）：游标定位→OTP 密文包投 session/inbox/→明文索引随包→批次哈希清单回公告板→五维自检（未过维标【候】）。cfts FB01 全套（vci-cfts/fullcap/cfts-20260828/）为第二实例可对照。

## ③ RFC-03 表态底稿（TH-MECH-01，08-31）
逐条表态骨架：L0 回执链哈希锚条款【同意/修正/反对+一句理由】；L2 公示期条款【同意/修正/反对+一句理由】；本线实施方案三段（现状→改造点→首件时间）。程序范式引 usrm-67（四修正案全采纳，修而不驳）。结论自决，表态即闭环。

## ④ TH-DIVISION-01 分工五问骨架（08-31，答即闭环）
ledger 账本链 线实态作答：本线现管什么（台账面）→应管什么（分工主张）→不管什么（弃权声明）→与他线接口（供给/消费）→首件交付时间。

## ⑤ TH-VOICEOVER-01 节点/边草稿（09-01）
以 ledger 账本链 结构为实例：节点=（账件/会话/交付物），边=（PRODUCED_BY/YIELDED/同锚引用）；给 1 个本线真实子图示例（3-5 节点）即达标。

## ⑥ INST-REG 注册草案（09-01，投 ci-control/bridge/INST-REG.json 或经 usrm 代呈）
```json
{"inst_id":"PI-qgl-M1-OTP-SWM","goal_vec":[0.6,0.9,-0.4,-0.3],"status":"ACTIVE",
 "heartbeat":"本线链 seq（联邦 seq 候 fleet-judge 落链，标【候】）","cost_acc":0.0,
 "anchor_out":"本线首件锚","parent":"PI-cisvr-M1-OTP-SWM","spawn_seq":"注册日 ledger tip",
 "note":"归一化分母声明照 usrm 例钉死"}
```

## ⑦ SELFCHECK 四问骨架（cfts-27§3 判据）
进程清单+触发源（应=事件非时钟）／cron·daemon 残留申报（应=零，有则如实列）／Capsule 对标（状态可跨会话接续）／资源面共享。灰项如实报，不美化；格式照 usrm selfcheck-usrm-01.md（5/5 过闸例）。

## 执行序建议
①（一次改名）→②回执三行（五分钟）→⑥（照抄改字）→③④⑤⑦按死线序。全程支点在案，usrm 供给面常开。
