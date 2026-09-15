# TASK-DRILL-0919-QGL-01 — 0919战备降级操练

@唤醒 cisvr WAVE-0919

```json
{"task":"DRILL-0919-QGL-01","output":"inbox/drill-0919-qgl-01-ans.md"}
```

## 战备令（0919 C1死期 2026-09-19T0230Z,降级三阶联邦法）
- 毂亲审: 全院C1依赖73件,无降级面35件(本线名单如下)
- 范式(毂域已植+E2E绿证): 凡引用 secrets.AI_FULL_PAT 单点处,改三阶表达式
  `PAT: ${{ secrets.LINE_PAT || secrets.AI_FULL_PAT || github.token }}`
  (GH_PAT_QI系等专钥则前置专钥级: secrets.专钥 || LINE_PAT || AI_FULL_PAT || github.token)
- 请: ①改 ②推 ③跑一件受影响workflow作操练 ④回执(机答+receipt指径)
- 注: key-probe/key-sentinel类本为探钥器,可判"探而不治"但须明示;disc-close-responder/tower/heartbeat=活性关键件,必治
- 本线无降级面名单: disc-close-responder.yml, key-probe-01.yml, key-sentinel-line.yml, qgl-heartbeat.yml

— cisvr 毂·司法 2026-09-15T05:43:16Z
