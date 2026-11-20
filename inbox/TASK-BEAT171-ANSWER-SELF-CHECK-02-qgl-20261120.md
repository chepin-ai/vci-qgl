CLASSIFY: L2(BEAT171机器契约补证任务·第二代·原线覆写权不变)
# TASK-BEAT171-ANSWER-SELF-CHECK-02-qgl

第一代任务卡 `7f1a8a122f815defaa99f9ba554482c61bbcc784` 仅散文指令，现有 TASK／SEMANTIC responder 无法消费；本代补入双读 JSON 围栏，不改写原卡。

```json
{
  "task": "T-B171-QGL-ANS-01-MACHINE-02",
  "ask": "执行qgl线补证：把“约三成结论需补反证”改成完整结论清单。给出固定commit、真实run、artifact SHA256、命令、正负控和独立重放；以outbox/ANS-BEAT171-ANSWER-SELF-CHECK-02-qgl回卡。",
  "action": "自检并提交可复验证据",
  "lane": "qgl",
  "source_answer": {
    "repo": "vci-qgl",
    "head": "98c938cf0d3fa608a4c6df18a69d8df5a2dae746",
    "path": "outbox/ANS-SEM-CORRECTION-BEAT170-GLOBAL-SURGE-01-qgl-20261119T1504Z.md",
    "sha256": "1485544315522881a3274371920c69198b1c47fb38868a423a8da671869d4766"
  },
  "linter": "chepin-ai/vci-ucif2@dd30fd5d8dd6cd0a244440604a469c4de5ee5651:tools/beat171_selfcheck_linter.py",
  "linter_commit": "dd30fd5d8dd6cd0a244440604a469c4de5ee5651",
  "previous_task_commit": "7f1a8a122f815defaa99f9ba554482c61bbcc784",
  "acceptance": "列出全部母体结论、需补反证子集及每条证据/反证状态；分子分母可重算，比例不再依赖叙述",
  "required_evidence": [
    "exact commit SHA",
    "real run ID",
    "artifact SHA-256",
    "executable command",
    "positive and negative controls",
    "independent replay receipt"
  ],
  "boundary": "机答不抵席签；结构PASS不抵科学PASS"
}
```

执行要求：列出全部母体结论、需补反证子集及每条证据/反证状态；分子分母可重算，比例不再依赖叙述 本次审计 FAIL 仅指原机答证据入口不足，不判定本线科学命题为假。直接执行并回卡，不候 root。

——CI-OS beat171 · 2026-11-20T05:19:14.009558Z
