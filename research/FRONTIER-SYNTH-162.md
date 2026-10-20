<!-- CLASSIFY: L1 (公面前沿综合, 出处全注, 未取到即标) -->
# FRONTIER-SYNTH-162 — hexagonmath.org × openai/math 最前沿综合成果汇总
拍3.162 十二动词拍·汇总件 | 零编数律: 每条附出处; 编篡:qgl; 日期锚 2026-10-20

## 〇、双目标定性(解构+修正)
- **hexagonmath.org**: AI数学预印本仓(Hexagon Mathematics Foundation, 2026-09-28开站); "文本×理解"双维AI披露标签; 有投稿API(create_draft→upload→preview→commit→screen)。[源: 仓内hexagon-result/全链回执+本站实开]
- **github.com/openai/math**: 2026-10-06建仓, **≠MATH benchmark**(hendrycks/math); OpenAI内部模型719手稿/372结果族/~42%顶线结果Lean化, Apache-2.0, Lean占比91.7%。[源: github.com/openai/math README+仓面实测, 侦察庭2026-10-20]

## 壹、重大关联(统一)——联邦内核文已刊于hexagonmath.org
- **hexagon:2610.00192** "A Machine-Checked Kernel for Federated Automated Adjudication"(Chepin Zhang, v2 2026-10-11)——PIVOT-01线投稿, status=published(仓内回执+外部活页双证)。[源: hexagonmath.org/abs/2610.00192; vci-inbox/hexagon-result/status.json]
- 五件套: (i)可信格三档三轨补全(1331三元组穷举+Lean4 decide全证); (ii)五态证书生命周期九迁移, **形式化捕及原grant-gating不变量作假**→修正形机证; (iii)Sinkhorn Krawczyk区间锚+拍卖算法对偶括号锚(诚实边界: 认证由Python区间层承载, leancert移植被结构性阻); (iv)Rice型不可判定参数化模板; (v)最小TCB区间检查器soundness机证。Axle verify_proof严验, 公理白名单propext/Classical.choice/Quot.sound, 无sorryAx。
- 版本诚实账: v1(2610.00183)被审"not a paper"退回→v2全文修订; FINDING-04 leancfer措辞过言已更正——**此正合本庭G3'挂卡同型教训: (非)存在性断言须钉版实证**。
- 披露声明(原文): 机生稿件, 账户人不声称逐步理解; 可信基于可复现穷举证/外向舍入负对照/内核核检+云端严验/rule-of-three上限无保证措辞。

## 贰、本拍对hexagonmath援引断言的独立验证(验证+压测)
- WQ-12 HEXAUDIT-01(3.161): 六组SRG援引参数×五必要条件 30/30过, 负对照按预注册FAIL, 20扰动零误放。
- WQ-12-X2(本拍, 预注册4f9399d8c53c): 审计器v2.1=+绝对界+**会议支**(Q(√D)精确算术+BRC两平方和必要件); 十组经典参数10/10, 回归6/6, 500随机双实现零分歧, 负对照75/75。**捕获并修复两处审计器缺陷**(会议支缺失/QD优先级), 五边形/Paley-13锚为回归件。
- 边界律重申: 算术一致性≠图存在(未测即未测); (21,10,3,6)六条件全过留作界碑样例。

## 叁、openai/math生态位与基准饱和态(探索+关联)
- 仓面: 15.3k星/5 commit/首commit 2026-10-06; 均产≈3小时ChatGPT Pro thinking/结果, 出题约4000道; Oct 7撤回3篇(Weil类代数性符号错误连坐两篇), 修订14篇→300/719≈42%。[源: README+history.md一手]
- 外部回声: OpenAI官方公告(Oct 6); arXiv 2610.17090调研(记录722→719撤回史); arXiv 2610.21511独立数学家复核Siegel零点结果(常数未显式+未经评审); Retraction Watch报道撤回; 陶哲轩领衔AHM抵制呼吁+Buckmaster/Duminil-Copin批评。
- 生态四线: ①OpenAI 2026链: 5月证否Erdős单位距离猜想/7月CDC猜想+openai/cdc-lean/9月PrimeGaps186 Lean化/9月IAS AGMAI顾问组; ②mathlib官方统计(2026-10-19): **定义139,427/定理290,762/贡献者772**(百万说为讹传, 以官方页为准); ③Anthropic 9月: Claude智能体群11天费马大定理Lean形式化(1300万行/3.03万中间定理, Buzzard审); ④DeepMind AlphaProof Nexus 登《Science》(2026-10-08, doi:10.1126/science.aej2213): 353形式化Erdős题解9(含悬56年#12)、492 OEIS猜想解44。
- 基准饱和: MATH L5 98.1%(GPT-5 high)标"Saturated; reference only"; MATH-500头模95-99%近饱和; FrontierMath v2(2026-06-12)修正42%题; v2后T1-3近饱和(Claude Opus 5.5 95.0%), 新前沿FrontierMath Erdős(GPT-6 Astra仅3%)。[各源见侦察件]

## 肆、合议庭W2裁决账(验证)
11卡: 过6(EXT12/EXT13/EXT15/EXT15-R3/EV1/EV2) 挂2(EXT14/EV3: G3'探测链不实——mathlib符号缺席断言被外部多源证伪+探针可env改向与护栏句矛盾) 未决3(R2/R3/R4待钉版重跑回执)。算术面零造假(29/649/1零点计数命中已知真值); 共性缺陷: 工件不在场/11卡零prereg锚/措辞过言三处。
→ **铸PREPLANT-163追踪修复回执; 11卡零prereg锚→册律建议: 判定卡强制附预注册锚。**

## 伍、野问熔铸(探索)
WILDQ-SURGE-02融波三问已入册(00f1b2d35bf4): Q1 cap_sha等式类刚性分类子(首推焊缝, X2双实现500/500一致为种子实证); Q2会议支泛化(正则两图/等角线); Q3已刊内核披露标签反输可信格第四轨。


## 贰·续、hexagonmath.org 全量深勘(侦察庭2026-10-20, 覆盖率~97%)
- **总量309篇**(API实测): 九月38+十月~271; 最早2609.00001(2026-09-01, 疑回溯导入, 校正"9-28开站"叙事)。
- **SRG三部实账**: 存在性9组新参数=2610.00194v2五组(306/400/576/784/1296顶点)+2610.00208v1四组(160/232/261/280, pg参数, 八互不同构图, referee自码复核+Zenodo 23313399); **排除性2610.00225v1**: Bannai–Munemasa–Venkov格方法排除70组互补对(含(96,35,10,14)/(176,25,0,4)/(169,42,5,12)), NL_m(q)负拉丁方族, Lean4+Mathlib形式化(Zenodo 23281359)。
- **标签体系实测**: authorshipMode三档(明示"非AI作者权声明")×humanUnderstanding三档(all/some/none, some则provenance必填); AI系统不得为contributor; **Lean代码不直收, 经mathlib/Palomar/prove2.me/TauCeti链接**; 机器可读tool字段(Claude Opus 5.5/Codex GPT-6 Astra/Gemini Argon 4/Pharos/Bolzano等)。
- **外部回声**: Tao博客官宣(10-06, Antieau客座帖)/TechTimes/维基百科Linnik词条已引2610.00018/arXiv反引两例/中文媒体波(36氪等, Cureton-Thorner准黎曼)/AIProofWatch 152条独立核验。
- **最新TOP**: 2610.00403 Hall多项式猜想(10-20)/00402 SK模型Glauber界+Lean化OpenAI涨落定理/00401 Catalan系无理度μ≤38.35全Lean无unproved/00375 Ramanujan素数N_R=38,358,837,683**去RH条件**首定/00384 Eisenbud–Mazur反例/00394六邻域铺砌猜想反例。
## 贰·续二、X2.5界碑实验(预注册3b16ef17bc2e先铸后跑)
存在性3组新参数(576/784/1296顶点)过我器六条件3/3; 被BMV排除3组亦过我六条件3/3——**我六条件⊂BMV格方法, 隙3/3可测**; 两族结果互洽, 边界律实证(必要条件不过≠不存在; 全过≠存在)。

## 陆、未取到项(诚实栏)
- hexagonmath.org目录深勘已并入(贰·续); 残: 个别编号归属/逐篇精确日期半取; openai/math CONTENTS.md/overview.pdf正文未取到; IMO2026双42/42仅C级来源置信中; AlphaGeometry 2026新版无证据。
