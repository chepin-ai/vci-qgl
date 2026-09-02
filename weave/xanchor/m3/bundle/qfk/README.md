# QFK（qf-know）— QF-OS 链-哈希知识底座 · 快速原型 v0.2

**最小原型 = 残差引擎（I1）× 三档验证节拍（I2）× Git+prolly+beacon 场（I5）× 圈签链头（D2）× TT/TensorLogic 微内核（D1）× trans() 五档 proof（D5）× 熵锚+抽签（I6）× 三机 MIP（无星）互证（v0.2），一切规模钉在 I7 物理面内。**

运行交验：在 `/mnt/agents/output` 下 `python3 -m pytest qfk/test_all.py qfk/test_ipmp.py -q`（34 测全绿为完成定义；或分别 `python -m qfk.test_all` 23 测 / `python -m qfk.test_ipmp` 11 测；纯 Python≥3.11，依赖仅 numpy+cryptography，测试零网络）。

## v0.2 新增件清单（ipmp 三机互证 + factor_forecast）

**判词照录（全文贯彻，不升格）：本协议是 MIP（无星）+ 绑定承诺互锚 + 信标挑战 的结构同构工程构造，不是字面 MIP\*——「MIP 无星结构同构不升格」。** 一切 soundness 陈述只覆盖 A 档 1–6 的诚实上界；纠缠编译档由 A2 类闸门整体移出；硬件 Bell 数字永不入验证路径。

| 件 | 文件 | 内容 |
|---|---|---|
| 第八模块 | `ipmp.py`（新增） | 六相位状态机 COMMIT→CHALLENGE→WINDOW→RESPOND→JUDGE→SETTLE→终态；7 dataclass（MachineSpec/PropositionCommit/Challenge/ResponseCommitment/ResponseReveal/Verdict/WindowPolicy）；纯函数 `judge_verdict`（gap=None 钉死 GAP_UNKNOWN）+ `collusion_probe`（M-probe 审计探针，命中=违规证据、未命中≠清白）；`IPMPSession`/`IPMPEngine`（含 `replay` 争议重放与 `judge_set_for` 灰区#10 角色轮换接口）；异常五件（PhaseError/WindowLockedError/BindingError/ClassGateError/SelfJudgeError） |
| F-1 | `findings.py` | `DOMAINS` 追加 `"mutual-proof"`；`CLASSIFY_MAP` 追加 collusion_suspect/proposition_class_rejected/binding_mismatch/replay_mismatch/gap_unknown |
| F-2 | `beacon.py` | `Beacon.entropy_grade()`（任一 OfflineSource→"classical-sim"）；`BeaconTick.source_names` 快照字段（默认 `()` 兼容旧构造） |
| F-3 | `circle.py` | 抽内部 `_sign`/`_verify`（tag 域分隔）；`sign_checkpoint/verify` 改薄封装（向后兼容）；新增 `VERDICT_TAG=b"qfk:ipmp:verdict:"` + `sign_verdict/verify_verdict` |
| F-4 | `__init__.py` | import 追加 `ipmp`，七模块→八模块，`__version__="0.2.0"` |
| 外推灰件 | `tensor.py` | `factor_forecast(series, horizon, method="ewma"\|"ar1", alpha)`——**此外推为工程灰件，非已证预测**（ipc-tensorcast-01 §4 对位 #8；无平稳性检验，外推偏差须 `tn_residual` 事后对拍入残差流） |
| 测试 | `test_ipmp.py`（新增） | T-01~T-11（编号 24–34），含串谋负例 T-06（test_29）；全部零网络，负例与正例共享同一公开接口路径 |

窗口强度如实标注：M1 绑定=密码学级、时序=纪律级；M2 审计=纪律级；M3 代码绑定=密码学级、重放忠实=纪律级；三者叠加联合强度仍为「纪律级主体 + 密码学级绑定件」。灰区#10（NP 双帽）只实装轮换接口（`judge_rotation`/`judge_set_for`/`register_machine`），风险无形式化消解、依旧未闭合。B 档 7–9 不触及、不留假接口。设计正本：`/mnt/agents/output/research/ipc-ipmp-design-01.md`。

## 主叙事：残差引擎

本底座不以零残差为目标。张量收缩残差、四语互译残差、场漂移残差是**同一类对象**——「期望失配流」。主循环只有一条：

```
produce → classify(type×severity) → route(breaking→人工闸) → resolve(≤3 轮注记) → commit(domain="finding" 入链)
```

五域（chain/circle/field/tensor/trans）共用同一 SHACL 化残差 schema `{type, focus, severity, constraint, detail, tick}`，severity∈{info,warn,breaking}。非零残差即入队并入链：**LLM/启发式是残差制造机，符号层是残差判定机，链是残差留证机**（I1×I4）。链-哈希脊柱不是存储引擎，是这条主循环的留证骨架。

## 架构映射表（八模块 ↔ 七洞察 ↔ 深研件）

| 模块 | 职责 | 洞察 | 深研件 |
|---|---|---|---|
| `chain.py` | 链-哈希脊柱：Entry{seq,ts,domain,payload,prev,hash}、TILE=8 tile 化、checkpoint 链、inclusion+consistency 双证明、`alias()` 12-hex 显示别名 | I2（L1 每拍轻承诺挂点） | qf-know_dim04（可验索引）、substrate §4 HOLO-01 |
| `beacon.py` | 量子锚：BeaconTick{seq,qrand,prev,hash}、HKDF(ANU‖drand‖os‖prev, info=seq)、离线 classical-sim 默认、`leader_draw` 软抽签、`qubo_hook` 北星接口 | I6（诚实分层：只实装硬熵锚+软绑定）、I2（相位分频 `seq%N==p`） | qf-know_dim06 |
| `circle.py` | 圈签链头：Policy{m,n,members,policy_hash}、Ed25519 m-of-n 共签 checkpoint.root 离线验证、RECONFIG 链上自指（免 DKG）、`llm_advice()` 权重恒 0 占位 | I2（L2 中证）、I4（LLM 只作软层） | qf-know_dim02（sigsum 近同构移植） |
| `field.py` | 直通场：prolly-lite 排序键滚动哈希分块树、root=全息指纹、AOI 切片订阅、reconcile 二分下钻、漂移→FINDING(drift)、rebuild_from 链重放、claim 写者门禁 | I5（Git 外壳+prolly 指纹+beacon 对拍）、I1（漂移即主燃料） | qf-know_dim03（Willow AOI/指纹对账、Eg-Walker 投影可弃） |
| `tensor.py` | 张量微内核：稀疏 dict einsum、Datalog-ish 不动点、CP-ALS `tn_embed`、`tn_residual`(‖Fa−Fb‖/√d·ε 阈值)、贪心收缩路径+state_digest 缓存 | I1（√d·ε=确定性 FINDING 阈值）、I7（CPU 线 log10FLOPs≲12，禁稠密） | qf-know_dim01（方案 C 混合内核） |
| `trans.py` | 四语契约：trans(src,dst,payload,ctx)→{artifact,proof,residual}；实装 T4（ast.parse+py_compile 闸）与 T5（链见证）；T1/T2/T3=hook 返回 proof_tier_unavailable 残差 | I4（T4 当闸不当证，实证仅 54% 真等价）、I1（未接档位即残差生产） | qf-know_dim05（proof 五档谱系） |
| `findings.py` | 残差引擎：Finding 队列主循环，六域同 schema（v0.2 追加 mutual-proof），breaking 人工闸，≤3 轮注记，commit 入链 | I1（主循环本体） | qf-know_dim05 §3（SHACL 词表）、qf-know_dim03（漂移对拍） |
| `ipmp.py`（v0.2） | 三机 MIP（无星）互证：六相位状态机、commit-then-reveal 绑定窗口（M1）、审计钩/串谋探针挂点（M2/M-probe）、应答函数预承诺位（M3）、`judge_verdict` 确定化裁定 + `replay` 重放、verdict m-of-n 共签入链 | I1（残差分流）、I2（信标挑战+链留证）、I6（熵档快照诚实分层） | ipc-ipmp-design-01（A4 §5.2 A 档 6 条工程落点） |

I3（三个「无人闭合」交界面）不对应单模块，对应全包差异化定位：动态知识×张量、协同×留证、智能体×场三个交界面做成原生面；同时诚实声明——空白可能因为难，原型只做最小面，不承诺闭合。I7 物理面散落各模块钉死：`field.MAX_WRITERS=5`、`circle.CIRCLE_MAX=30`、`tensor.MAX_FLOPS_LOG10=12`。

## 验证三档（I2 分频）

| 档 | 节奏 | 机制 | 落点 |
|---|---|---|---|
| L1 | 每拍 | 哈希链+Ed25519 签 | `Chain.append` / `circle.sign_checkpoint` |
| L2 | 每 epoch | ADS 根入链：tile_root→checkpoint 链，圈签共签 cp.root | `Chain._finalize_tile` / `circle.verify` |
| L3 | 争议时 | 全量重放+独立证明核验 | `Chain.verify` / `Chain.verify_proof` |

beacon 相位 `seq%N==p`（`Beacon.phase`）是档位点火器；checkpoint 可选挂 `beacon_anchor` 与熵锚交叉。

## 角色分层（CZ-4：两个上限，两类角色，不得混用）

| 角色类 | 模块 | 上限 | 依据 |
|---|---|---|---|
| **写者前沿**（直写场者） | `field.py` `MAX_WRITERS` | **≤5** | CodeCRDT/AgentRoom 实证：无协调并行 < 单 agent，上限 3–5 |
| **签者圈**（checkpoint 共签者） | `circle.py` `CIRCLE_MAX` | **5–30** | BFT 圈成熟区（dim02） |

写者是场的内容生产者，签者是链头的见证者；同一物理体可兼任两角色，但两个上限各管各的门禁，代码中字段、注释、测试均分开。

## 灰色地带（如实标注，README 专节 + 模块 docstring `@gray`）

| # | 灰区 | 现状 | 出处 |
|---|---|---|---|
| G1 | 收缩寻路 QUBO=北星试件，**禁性能承诺** | `beacon.qubo_hook` 仅登记问题入残差流，无求解器；dim06：无直接 QUBO 先例，演示价值>性能价值 | `beacon.py` |
| G2 | 删除无原语、半闭合 | `Field` 只有 put/覆写，Willow prefix-prune 删除语义未实装；删除诉求记残差流入研究队列 | `field.py` |
| G3 | LLM 仲裁 | `llm_advice()` 权重恒 0、无 LLM 调用面，verify 路径永不读；实证：良性 41.6% 有效、17/18 hung jury | `circle.py` |
| G4 | 圈>30 | `make_policy` 不硬拦，policy 自带 `oversized` 标记；成熟区外风险未实证 | `circle.py` |
| G5 | 写者>5 | 门禁硬拒第 6 写者并发，并发诉求转残差流（`write_gate_denied`） | `field.py` |
| G6 | 12-hex 降级 | `alias()` 仅显示别名，一切 verify 对非 32B 输入直接拒绝；genesis 可绑旧 12-hex 链头但 `evidence_level="degraded-12hex"`。生日界修正：12-hex（48 bit）50% 碰撞点 ≈ **1.18×2^24 条**（交验复算为准），故只配作别名/过渡证据，永不入验证路径 | `chain.py` |
| G7 | 三元组增删→TT 核 enrich→收缩树增量重寻 三件套无人闭合 | 本面只做冻结快照 CP 因子比对；增量闭合诉求入残差流不承诺 | `tensor.py` |
| G8 | 无通信窗口时序强制=纪律级 | `max_commit_skew_s` 靠本地时钟（可伪造），仅靠 m6 入链 seq 序事后佐证；可信时戳未闭合 | `ipmp.py` |
| G9 | 串谋探针=审计启发式非完备检测 | `collusion_probe` 命中=违规证据、未命中≠清白；完备性未闭合，detector 可注入 | `ipmp.py` |
| G10 | NP 双帽（裁定者自证） | 只实装角色轮换接口（`judge_rotation`/`judge_set_for`，剔除后无人可裁→`SelfJudgeError` 宁停不让自证）；风险无形式化消解，依旧未闭合 | `ipmp.py` |
| G11 | `factor_forecast` 外推=工程灰件 | 非已证预测：EWMA/AR(1) 无平稳性检验，偏差须 `tn_residual` 事后对拍入残差流 | `tensor.py` |

## 性能声明纪律（P14）

原型一切性能输出**只报绝对值 + config_digest**（如 `contraction_path` 的 FLOPs/中间张量量纲、测试耗时），**禁横向倍数声明**——各论文基线环境不可横比（交验实证）。任何「比 X 快 N 倍」式表述在本包内不出现，也不应在外层报告中引用本包数字做横向比较。

## 与 QF-OS 内场件对接

- **beacon-mirror**（BEACON-FABRIC-01 影子钟）：`Beacon` 的离线源可整只替换为读 `bridge/beacon-mirror.json` 的适配器（实现 `fetch()->32B` 即插入熵混合式），fleet 广播节拍不变。
- **outboxes 链**（substrate §2/INTEGRITY-01「链⊂一切」）：`Chain` 即其最小同构——domain 分流（field/finding/trans/circle）对应 outboxes 分类投递；`checkpoint.beacon_anchor` 预留跨链互织锚（CURBy/Twine 式互时间界的挂点）。
- **WAKE-01**（相位点火）：`Beacon.phase(n,p)` 即点火律 `seq%N==p` 的本地面；L1/L2/L3 验证深度档位由它驱动，cron 仅兜底，与 WAKE-01 事件驱动语义一致。

## 已知边界（非缺陷，如实声明）

- `contraction_path` 贪心逐对，非 cotengra 级寻优；缓存键含 state_digest，状态变即失效。
- T5 见证未过 TILE 边界时返回 `pending_tile`（如实），调用方须等 tile 落盘后取 inclusion proof。
- `Field.reconcile` 树级二分下钻+键集兜底，diff 集精确但下钻深度未作通信量优化。
- ANU/drand 真客户端存在但默认离线；启用即引入网络与限速（ANU ~5 req/s），测试永不触网。
