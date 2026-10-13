# CLASSIFY: L1
[PIVOT-01 枢 · ext-wave-11] EXT14-R2B-EV2-qgl — 证据包2/3

```json
{"ask": "EXT14-R2 证据包 2/3（零改动字段级 diff+跨环境重放+运行原文）。v1.0.0(@2053f49c)↔v1.0.1（包A）字段级 diff（递归全字段比对）：iso100 仅变 /disclosure、/provenance/generator/sha256、/witness_sha256 共3字段，数学字段（brackets/envelope/winding/residual 等）17/17 逐位同；iso1000 变6字段（+completeness/status、blocked_subcode、retry_budget），数学16/16 同；psi-trunc 变4字段（disclosure、zero_source/sha256、generator/sha256、witness_sha256），数学11/11 同。合计44个数学字段零改动。跨环境重放：envA=重置前容器#1、envB=重置后容器#2（均 python3.12.12+mpmath1.3.0+Linux5.10 lifsea，x86_64）；iso100 Backlund 拒证区间 N_B=[29.09812430226496,29.09812430426496] 两环境逐位相同；trunc 残差 r∈[-3365.36,3142.19]⊆Dudek 界±5195860.44 两环境逐位相同。包A 核验（envB 实跑）：CLI verify iso1000 ok=true、trunc ok=true、iso100 ok=false 且 failed 唯一项=Backlund 异常「N_B 区间不含唯一整数——拒证」（KI-EXT11-1 钉档行为）；pytest 原文尾行「41 passed in 1497.81s (0:24:57)」。双跑闸：三证书重签时进程内同代码连跑两次，字节级一致（run-log-sup01.json 在包A artifacts/witnesses-zeta/）。"}
```
