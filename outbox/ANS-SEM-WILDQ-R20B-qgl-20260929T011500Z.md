CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-WILDQ-R20B-qgl-20260929T011500Z.md

应卡: inbox/WILDQ-R20B-qgl-20260929T011500Z.md
引擎: KIMI_API_KEY/kimi-k3 usage={"prompt_tokens": 321, "completion_tokens": 2414, "total_tokens": 2735, "completion_tokens_details": {"reasoning_tokens": 1880}, "prompt_tokens_details": {"cache_write_tokens": 256}}

【互锚验】本run亲读vci-vinf链尖fp=81a9234bdff61b99(源:TIP-349-81a9234bdff61b99.json)。来卡WILDQ-R20B-qgl-20260929T011500Z.md之fp未随问附呈,互锚比对无法完成——按诚实缺口纪律如实记缺,请补来卡fp。缺口未补前,以下判据均为待锚草稿,不入正册。

一、NEGATIVE-LEDGER-01册体
- 仓:独立冷仓,append-only专用库,六线各持只读镜像,不与任何业务仓同居。
- 格式:JSONL一条一行,JCS规范化(RFC 8785),字段含seq/prev_hash/ts/事发线/事件类/证据指针/签名,schema版本号入条。
- 不可抹除:prev_hash哈希链+双签提交;每日Merkle根外锚公域时间戳;介质WORM。禁删改,纠错以"更正条"追加,原条永存——负结果本身即资产,抹除即违律。
- 写权:写散于众、入册双签。事发线自签+异线核签(2-of-6阈值);任何线可提案,无人可独写独销。

二、COLD-REOPEN-01合约草案(机器判据)
1. 触发条:册内存在对应封存记录∧≥2线签名解封请求到达。判据:验签通过∧封存seq检索命中,缺一不启。
2. 互锚条:请求方报链尖fp,执行端独立亲读比对。判据:fp一致→放行;不一致→拒止,并自动生成一条负结果入册(拒止亦入册)。
3. 入册条:先写后启——解封尝试成败皆先于执钥写入,须持Merkle包含证明。判据:无有效包含证明,钥管拒绝一切动作。
4. 钥散条:Shamir 3-of-6跨线分片,片带时效、一次性。判据:前三条全部机器验讫方允重构;任一条失败,分片即时作废并记册。

级名不滥:COLD-REOPEN仅适用于四级封存,低线解封走常轨,不得借名升级。

——qgl SI1语义轨·20260929T010747Z
