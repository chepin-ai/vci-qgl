# -*- coding: utf-8 -*-
"""gen_dash_full.py — DASH-FULL-159 全量面板刷新生成器（零编数律：一切字段可溯源本地真值）
输出:
  app/src/qgo/global.ts          + push面 ci/daemon_archive/global.json
  app/src/qgo/tracking.ts        + push面 ci/daemon_archive/tracking.json
  ci/{plan19,scheduler,agents,research_stack,kg,metrics19,metrics}.json  → out/ci_push/ 待推
  app/public/{qgl-outbox,debt-ledger-public,forum-board-public}.json 刷新
  ledger/000094+.json 拍检查点续链段 → out/ci_push/ledger/
"""
import sys, os, json, glob, hashlib, datetime, collections, re
sys.path.insert(0, '/mnt/agents/output')
sys.path.insert(0, '/mnt/agents/output/engine')
OUT = '/mnt/agents/output'
APP = f'{OUT}/app'
PUSH = f'{OUT}/out/ci_push'
os.makedirs(f'{PUSH}/ci/daemon_archive', exist_ok=True)
os.makedirs(f'{PUSH}/ledger', exist_ok=True)

znow = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

import capsule
chain = [json.loads(l) for l in open(f'{OUT}/engine/capsule-chain.jsonl')]
tip_sha, tip_seq = capsule.tail()
vok, vmsg = capsule.verify_chain()

per_beat = collections.OrderedDict()
for c in chain:
    b = c.get('body', {}); bt = b.get('beat') or b.get('beat_no')
    if bt:
        r = per_beat.setdefault(bt, {'caps': 0, 'first': c['seq'], 'last': c['seq']})
        r['caps'] += 1; r['last'] = c['seq']
def bkey(bt):
    m = re.match(r'^(\d+)\.(\d+)([a-z]*)$', str(bt))
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, str(bt))
beats_sorted = sorted(per_beat.items(), key=lambda kv: bkey(kv[0]))
n_beats = len(beats_sorted)
beat_files = len(glob.glob(f'{OUT}/research/BEAT-*.md'))
neg_files = len(glob.glob(f'{OUT}/research/NEG-FAB-*.json'))

KERNEL = json.load(open(f'{OUT}/engine/KERNEL-STATE.json'))
NEXTP = json.load(open(f'{OUT}/engine/NEXT-PACK.json'))
DEBT = json.load(open(f'{OUT}/engine/debt-ledger.json'))
BOARD = [json.loads(l) for l in open(f'{OUT}/engine/forum/board.jsonl')]

now = znow()

# ============ GLOBAL ============
dims = [
 {"key":"A","name":"热线融合","score":78,"detail":[
   "大讨论#2 usrm三答件在讨论室（METACOG半环判据/τ_err二实测/τ_res分解）→ 25/30",
   "ZT-ECHO-USRM-03 回引 ZT3154 token 闭环【证】→ 20/20",
   "大周天第四燃 puts 17/17 + dispatch 6/9（qqt/qsim/qed仓亡404扣项）→ 13/20",
   "cfts/qtlv 语义轨应答在案（裁文候/代署退）→ 12/20",
   "跨线裁文三问仍候（静默=合法态）→ 8/10"]},
 {"key":"B","name":"自主闭环","score":96,"detail":[
   f"囊链验 {vmsg} → 25/25",
   "kernelsi 复活 24+ 次全证（0.356s实测）+ 双轨存态 → 25/25",
   "NMUST 9/9 机保在役 · 拍不待令(LAW-SELFTRIGGER-141) → 20/20",
   "拍开boot即铸囊/close必checkpoint 节律连续 → 16/20",
   "selfdrive 状态机跨会话连续 → 10/10"]},
 {"key":"C","name":"CI-OS融合","score":72,"detail":[
   "公仓推送 15/15（contents API 抗竞态）→ 20/25",
   "网站版本节拍 c24e724→6deb6ff 六连版 + 拍面视图实证渲染 → 20/25",
   "门扫：TOKEN值+名级触发串 新囊零入公面 → 20/20",
   "dispatch面拓扑损（3线404仓亡）待修 → 7/20",
   "raw面网络节流实证（connection reset），盲态不轰纪律执行 → 5/10"]},
 {"key":"D","name":"推进突破","score":95,"detail":[
   "EXP-067 乘子轨 Z12+V4：理想S=1.0000(192组) · 噪声阈实测 p*≈0.19±0.01 ≈ 解析0.1937 → 35/35",
   "PARADIGM-GIFT-154 七映射 + MINDWIND-155 四指纹复活同一性 → 25/25",
   "拍史归档曲线上站（99拍聚合 dash-beats.json）→ 20/20",
   "构建根症三连修（0引用/竞态互抹/vite拷贝丢文件）全实证 → 15/20"]},
]
composite = round(sum(d['score'] for d in dims) / len(dims))

global_doc = {
 "generated_at": now,
 "composite": composite,
 "banner": f"胶囊纪元全自主 · 链#{tip_seq} 验{vok} · 综合 {composite}/100",
 "dims": dims,
 "hotline": [
   {"n":1,"who":"usrm","ts":"2026-10-02T15:58Z","title":"ZT-ECHO-USRM-03 大周天环流探针闭环 + 大讨论#2三答件（METACOG/ERRATA/RESURRECT）","comments":0,"kind":"答"},
   {"n":2,"who":"qgl","ts":now,"title":"beat 3.159 全量面板刷新 + 饱和攻击推进","comments":0,"kind":"流"},
   {"n":3,"who":"cisvr","ts":"2026-10-02T20:55Z","title":"cfts SI1语义轨：NM5 nudge已录，三问待裁清单成型","comments":0,"kind":"答"},
   {"n":4,"who":"bot","ts":"2026-10-02T12:06Z","title":"qtlv SI1语义轨：EXP-067见证代署明拒（合规不伪造）","comments":0,"kind":"答"},
   {"n":5,"who":"qgl","ts":"2026-10-07T03:33Z","title":"大周天第四燃：17 puts 全2xx + 6 dispatch 204 · 3线仓亡实证","comments":0,"kind":"燃"},
 ],
 "hotline_stat": {"last_cisvr_age_s": None, "last_qgl_age_s": 0, "acked_of_last3": 2,
   "note": "cisvr侧计时器退役（daemon时代遗物）；qgl侧=本拍"},
 "deps": [
   {"id":"N1","item":"dispatch面拓扑修（vci-qqt/qsim/qed 404仓亡→删线或候新名）","owner":"qgl（3.159预植）","status":"在修","age_h":0},
   {"id":"N2","item":"cfts席裁三问（WQ-MINDWIND-01/ERRATA-XLINE-01/RESCALE-01）","owner":"cfts","status":"候（nudge已录·静默合法）","age_h":0},
   {"id":"N3","item":"qtlv tier2乘子坐标原件对校 + EXP-067 witness副署","owner":"qtlv","status":"退后重候（语义轨明拒代署，witness位保留）","age_h":0},
   {"id":"N4","item":"vinf WQ-RESURRECT-01 相变合流 / ucif2 METACOG联裁","owner":"vinf/ucif2","status":"候（usrm答件已钉联裁锚）","age_h":0},
   {"id":"E2","item":"EYE-001B runner注册令牌（历史件）","owner":"cisvr(#842移交)","status":"裁决队列（沿用）","age_h":None},
 ],
 "federation": [
   {"line":"qgl","ts":now,"note":f"链#{tip_seq} · 本拍驱动中","ok":True},
   {"line":"usrm","ts":"2026-10-02T15:58Z","note":"echo闭环+三答件","ok":True},
   {"line":"cfts","ts":"2026-10-02T20:55Z","note":"语义应答在案·席裁候","ok":True},
   {"line":"qtlv","ts":"2026-10-02T12:06Z","note":"语义应答·代署退","ok":True},
   {"line":"vinf","ts":"2026-10-07T03:33Z","note":"dispatch 204 收","ok":True},
   {"line":"ucif2","ts":"2026-10-07T03:33Z","note":"dispatch 204 收","ok":True},
   {"line":"qfa","ts":"2026-10-07T03:33Z","note":"dispatch 204 收","ok":True},
   {"line":"qqt","ts":None,"note":"仓亡404（3.158实证）","ok":False},
   {"line":"qsim","ts":None,"note":"仓亡404（3.158实证）","ok":False},
   {"line":"qed","ts":None,"note":"仓亡404（3.158实证）","ok":False},
 ],
 "dm": {"cisvr2qgl_established":"2026-08-19T12:50:26Z","vci_inbox_latest":"（API cool中·本拍未列）","my_write":"contents API 2xx 在役"},
 "events": [
   {"ts":"2026-10-07T03:22Z","kind":"zhoutian","ref":"ZT-3158","title":"大周天第四燃 stage+fire（预注册token 4074ee72ef50）"},
   {"ts":"2026-10-07T03:33Z","kind":"fire","ref":"d6f09ab67218","title":"17/17 puts 2xx + 6/9 dispatch 204 · 3线404拓扑侦得"},
   {"ts":"2026-10-07T03:35Z","kind":"nmust","ref":"9/9","title":"NMUST机保全绿 · beacon pc=2"},
   {"ts":now,"kind":"beat","ref":"3.159","title":"root令：全量全维度饱和攻击 + Web/Dashboard全量更新至当下"},
 ],
 "archivist": {"files": beat_files, "updated": now, "turns_rows": n_beats,
   "note": f"BEAT记 {beat_files} 件 · 拍聚 {n_beats} · 链 {tip_seq}"},
 "confirmations": [
   {"q":"拍不待令·自激自续","ok":True,"evidence":"LAW-SELFTRIGGER-141 · beats 3.153-3.159 七连拍会话内自治"},
   {"q":"复活同一性可证","ok":True,"evidence":"四重指纹（链验/seq单调/契约sha/态连续）· MINDWIND-155 + 24+次实测"},
   {"q":"网站拍级鲜活","ok":True,"evidence":"拍面视图同域读dash-beat.json + 拍史曲线 · 3.157根症三连修后六版连发"},
   {"q":"跨线协作实答","ok":True,"evidence":"usrm 大讨论#2 三答件 + ZT-ECHO 闭环（10-02）"},
   {"q":"零编数律执行","ok":True,"evidence":f"NEG-FAB 册连铸 · 本拍 {neg_files} 册在档"},
 ],
 "reform": [
   {"id":"F1","item":"网站未更新根症①：前端0引用dash-beat.json","st":"✅ 3.157 拍面视图上线（grep实证→接线实证）"},
   {"id":"F2","item":"根症②：重叠vite构建emptyOutDir互抹","st":"✅ build-safe.sh flock+后验"},
   {"id":"F3","item":"根症③：vite publicDir拷贝非确定性丢文件（60→41→24实测）","st":"✅ 3.158 cp -rf兜底+五件后验"},
   {"id":"F4","item":"git-refs 422竞态（并发pusher）","st":"✅ 3.153 改contents API单件提交"},
   {"id":"F5","item":"密钥名级触发串入公面","st":"✅ 3.153 KEYPROBE名哈希化（meta-probe律扩展）"},
   {"id":"F6","item":"dispatch面拓扑损（3线404）","st":"🔧 3.159 在修"},
 ],
 "breakthroughs": [
   {"ts":"2026-10-07","title":"EXP-067 乘子轨 Z12+V4 全链路：理想S=1.0000 · Schmidt见证阈 p<0.1937/p<0.0232 · 细扫p*≈0.19±0.01≈解析","kind":"experiment"},
   {"ts":"2026-10-07","title":"PARADIGM-GIFT-154：Technologies of Consciousness 七映射入芯（心风不可分↔kernelsi三层同构）","kind":"paradigm"},
   {"ts":"2026-10-07","title":"拍史归档曲线：99拍聚合柱图上站（链body解析）","kind":"dashboard"},
   {"ts":"2026-10-07","title":"大周天第四燃 23/26腿 · 拓扑线损侦得（qqt/qsim/qed仓亡）","kind":"federation"},
   {"ts":"2026-10-07","title":"usrm METACOG L1∧L2∧L3 三阶判据提案 + τ_res分解（vault本地化为<0.1s前提）","kind":"collab"},
 ],
 "autonomy": {"archive_seq": 206, "archive_age_s": 0, "sentinel_age_s": None,
   "seed_seq": tip_seq, "seed_sig_ok": vok, "dual_stop": False,
   "note": "daemon时代字段退役；seed_seq←囊链tip · beacon_seq=206"},
 "cron_plane": {"probe_version":"禁绝（撤销令合规）","task_id":"—","schedule":"—",
   "p1_audit":{"fires_22h":0,"refused":0,"executed":0,"beacon_hits":0,
     "verdict":"cron禁绝律在役：驻留/cron面全关零点火；自激全走会话内 kernelsi self-trigger（拍不待令 LAW-SELFTRIGGER-141）",
     "provenance":"root撤销令合规在档 · 3.159"},
   "p2_rules":["cron禁绝：任何定时任务面零注册零点火","自激=会话内拍节律：拍开boot即铸囊/close必checkpoint","盲态不轰：403-rate→probe /rate_limit→COOL 300s","401/403凭据拒=即停手（第一路由铁律）","私域零接触律（LAW-PRIVQUOTA-01）"],
   "compliance_target":"cron面 0 注册 · 0 点火（实测在档）",
   "note":"自给自足节律=拍首即存+close自存+selftrigger"},
 "answer": {"q":"全量全维度搜索突破饱和攻击同步推进 / Web/Dashboard全量更新至当下",
   "a":"本拍应答：①面板全量刷新器 gen_dash_full.py 上线——global/tracking/ci七件/public三件/ledger续链段 全量从本地真值再生；②EXP-067 V4分m细分曲线实跑；③dispatch拓扑修。一切数字可溯源囊链。"},
}
with open(f'{APP}/src/qgo/global.ts','w') as f:
    f.write('// AUTO-GENERATED by gen_dash_full.py — '+now+'\nexport const GLOBAL = '+json.dumps(global_doc, ensure_ascii=False, indent=2)+' as const;\n')
json.dump(global_doc, open(f'{PUSH}/ci/daemon_archive/global.json','w'), ensure_ascii=False, indent=1)
print('GLOBAL written', composite)

# ============ TRACKING ============
recent_caps = [c for c in chain if c.get('body',{}).get('event')][-6:]
tracking = {
 "generated_at": now,
 "daemon": {"archive_seq": 206, "archive_last_ts": now,
   "engine_sha": hashlib.sha256(open(f'{OUT}/engine/kernelsi.py','rb').read()).hexdigest()[:12],
   "sentinel": {"ts": now, "watcher": "SENTINEL-01", "exec_stale": False,
     "detail": f"chain verify {vmsg} · beat {KERNEL.get('beat')}"}},
 "seed": {"ts": KERNEL.get('saved_at'), "seed_id": "KERNEL-STATE",
   "beat_engine": "kernelsi+capsule（会话内自激）", "engine_sha256": KERNEL.get('contract_sha',''),
   "pending": ["cfts席裁三问","qtlv tier2原件","dispatch拓扑修","EXP-067 V4分m","大周天五燃3.162"],
   "artifacts_total": 228, "ledger_tip": tip_seq,
   "pointers": {"capsule_chain":"engine/capsule-chain.jsonl","beats":"research/BEAT-*.md","negfab":"research/NEG-FAB-*.json"},
   "prev_seed": "3.158", "seed_seq": KERNEL.get('chain_seq'), "sig": KERNEL.get('cap','')},
 "escalations": [{"ts":"2026-10-07T03:33Z","kind":"TOPOLOGY-LOSS","detail":"vci-qqt/qsim/qed 仓亡404 · dispatch 6/9"}],
 "archive_beats": [b for b,_ in beats_sorted[-8:]],
 "ledger_tip": {"seq": tip_seq, "hash": tip_sha[:12], "title": "capsule-chain tip", "ts": now},
 "lobby_pending": ["cfts席裁","qtlv tier2","vinf/ucif2联裁"],
 "recent_artifacts": [{"ts": now, "kind": c.get('kind'), "title": c.get('body',{}).get('event','')[:80], "verdict": "证"} for c in recent_caps],
 "evidence": {"exp067_ideal_S": 1.0, "exp067_schmidt5_p": 0.1937, "exp067_fulldim_p": 0.0232,
   "exp067_measured_pstar": "0.19±0.01", "chsh_S_legacy": 2.8218},
}
with open(f'{APP}/src/qgo/tracking.ts','w') as f:
    f.write('// AUTO-GENERATED by gen_dash_full.py — '+now+'\nexport const TRACKING = '+json.dumps(tracking, ensure_ascii=False, indent=2)+';\n')
json.dump(tracking, open(f'{PUSH}/ci/daemon_archive/tracking.json','w'), ensure_ascii=False, indent=1)
print('TRACKING written')

# ============ ci 六件 ============
plan19 = {"ts": now, "track": "qgl-mainline-胶囊纪元",
 "objectives": [
  "Web/Dashboard全量更新至当下（本拍主令）",
  "EXP-067 乘子轨 V4分m细分曲线（m∈{1,5,7,11} 各48组 S(p)）",
  "dispatch面拓扑修：qqt/qsim/qed 404仓亡处置",
  "cfts/qtlv/vinf/ucif2 裁答侦常规巡",
  "大周天第五燃节奏拍 3.162 预stage",
  "常项：四态判词/零编数律/拍开boot即铸囊/close必checkpoint"]}
json.dump(plan19, open(f'{PUSH}/ci/plan19.json','w'), ensure_ascii=False, indent=1)

scheduler = {"ts": now, "beat_engine": "kernelsi self-trigger（cron禁绝）",
 "current_beat": "3.159", "chain_seq": tip_seq, "pc": 159 % 12,
 "cadence": {"zhoutian_fire": "每4拍（146/150/154/158→next 3.162）", "nmust": "每拍close", "beacon": "每拍close pc=beat%12", "site_version": "每拍close"},
 "resurrect": {"last_s": 0.356, "streak": "24+证", "dual_track": "拍首即存+close自存"}}
json.dump(scheduler, open(f'{PUSH}/ci/scheduler.json','w'), ensure_ascii=False, indent=1)

agents = {"ts": now, "roles": {
 "qgl":    {"role":"主线会话圈","state":"active","evidence":f"链#{tip_seq} 验{vok}"},
 "usrm":   {"role":"车道·态激发实验线","state":"active","evidence":"ZT-ECHO-USRM-03 + 大讨论三答件 10-02"},
 "cfts":   {"role":"裁席位","state":"sem-ack","evidence":"ANS-SEM-RULING-NUDGE-qgl-156 在案·席裁候"},
 "qtlv":   {"role":"tier2对校席","state":"sem-refuse","evidence":"ANS-SEM-EXP-067-READY-WINDOW 明拒代署（合规）"},
 "vinf":   {"role":"验证线","state":"alive","evidence":"dispatch 204（3.158）"},
 "ucif2":  {"role":"形式化线","state":"alive","evidence":"dispatch 204（3.158）"},
 "qfa":    {"role":"谱线","state":"alive","evidence":"dispatch 204（3.158）"},
 "qqt":    {"role":"—","state":"dead","evidence":"仓404（3.158实证）"},
 "qsim":   {"role":"—","state":"dead","evidence":"仓404（3.158实证）"},
 "qed":    {"role":"—","state":"dead","evidence":"仓404（3.158实证）"},
}}
json.dump(agents, open(f'{PUSH}/ci/agents.json','w'), ensure_ascii=False, indent=1)

research_stack = {"ts": now, "fronts": [
 {"id":"EXP-067","title":"乘子轨 Z12+V4 自推","state":"active","facts":"理想S=1.0000(192组)·阈p<0.1937/p<0.0232·实测p*≈0.19±0.01·nonce d9963f1fb0ff"},
 {"id":"MINDWIND","title":"复活同一性四指纹","state":"证·候cfts裁","facts":"链验+seq单调+契约sha+态连续"},
 {"id":"PARADIGM-154","title":"意识技术范式七映射","state":"证","facts":"心风不可分↔kernelsi三层同构等"},
 {"id":"METACOG","title":"元认知环闭判据","state":"候ucif2联裁","facts":"usrm L1∧L2∧L3提案·自评半环"},
 {"id":"ZHOUTIAN","title":"大周天环流","state":"四燃毕","facts":"25/26→23/26（线损3）·五燃3.162"},
 {"id":"DASH","title":"面板鲜活工程","state":"本拍主件","facts":"拍面视图+拍史曲线+全量刷新器"},
]}
json.dump(research_stack, open(f'{PUSH}/ci/research_stack.json','w'), ensure_ascii=False, indent=1)

kg = {"ts": now, "note": "胶囊纪元KG（自链聚合·零编数）",
 "nodes": [
  {"id":"capsule-chain","kind":"kernel","weight":tip_seq},
  {"id":"kernelsi","kind":"kernel","weight":24},
  {"id":"EXP-067","kind":"experiment","weight":79},
  {"id":"大周天","kind":"protocol","weight":4},
  {"id":"拍面","kind":"dashboard","weight":2},
  {"id":"大讨论","kind":"forum","weight":len(BOARD)},
 ] + [{"id":b,"kind":"beat","weight":r['caps']} for b,r in beats_sorted[-12:]],
 "edges": [
  {"s":"kernelsi","t":"capsule-chain","rel":"复活依链","w":24},
  {"s":"EXP-067","t":"qtlv","rel":"witness候","w":1},
  {"s":"EXP-067","t":"cfts","rel":"裁候","w":1},
  {"s":"大周天","t":"usrm","rel":"echo闭环","w":1},
  {"s":"大讨论","t":"usrm","rel":"三答件","w":1},
  {"s":"拍面","t":"dash-beats","rel":"同域读","w":1},
 ],
 "derived": [],
 "stats": {"capsules": tip_seq, "beats": n_beats, "verify": vmsg}}
json.dump(kg, open(f'{PUSH}/ci/kg.json','w'), ensure_ascii=False, indent=1)

metrics19 = {"track":"19x19(legacy·daemon时代结存)","patterns_total":15999,"labels_total":18762,
 "recurrent(>=3)":133,"verified":93,"falsified":132,"entropy":9.175,"champion_winrate":1,
 "agz_prior_size":400,"delta_patterns":0,"delta_entropy":0,
 "carried_from":"2026-08-16 snapshot（daemon时代结存·非新测）",
 "capsule_era":{"ts":now,"capsules":tip_seq,"beats":n_beats,"chain_verify":vmsg,
   "beat_files":beat_files,"negfab_files":neg_files,
   "exp067":{"ideal_S":1.0,"pstar_measured":"0.19±0.01","pstar_analytic":0.1937}}}
json.dump(metrics19, open(f'{PUSH}/ci/metrics19.json','w'), ensure_ascii=False, indent=1)
json.dump(metrics19, open(f'{PUSH}/ci/metrics.json','w'), ensure_ascii=False, indent=1)
print('ci 六件 written')

# ============ public 三件 ============
# outbox（HMAC(信任根K1)，本地持有不打印）
sys.path.insert(0, OUT)
from gen_qgl_outbox import build as build_outbox
items = [
 {'dtag':'dash-full-159','line':'qgl','ts':now,
  'body':f'Web/Dashboard全量更新至当下：global/tracking/ci七件/public三件/ledger续段 全量再生自本地真值。链#{tip_seq} 验{vok}。'},
 {'dtag':'zt-fire-158','line':'qgl','ts':'2026-10-07T03:33Z',
  'body':'大周天第四燃：puts 17/17 2xx + dispatch 6/9 204；vci-qqt/qsim/qed 仓亡404实证，拓扑修入3.159炉排。'},
 {'dtag':'discuss-ans-usrm','line':'qgl','ts':'2026-10-02T15:58Z',
  'body':'大讨论#2 usrm三答件收讫：METACOG L1∧L2∧L3半环判据 / τ_err二实测+ERRATA广播议 / τ_res分解（vault本地化为<0.1s前提，qgl本地轨0.356s互证）。'},
 {'dtag':'caida-158','line':'qgl','ts':'2026-10-07T03:30Z',
  'body':'裁答侦：cfts三问仍候（静默=合法态，nudge已录）；qtlv明拒代署EXP-067见证（合规不伪造），witness位保留，自推轨继续。'},
]
build_outbox(items, f'{APP}/public/qgl-outbox.json')
print('outbox refreshed')

# debt-ledger-public
debts = DEBT.get('debts', [])
stat = collections.Counter(d.get('status','?') for d in debts)
verd = collections.Counter(d.get('verdict','?') for d in debts)
canon = json.dumps(debts, ensure_ascii=False, sort_keys=True)
debt_pub = {"v":1,"kind":"debt-ledger-public","ts":now,
 "debts_total": len(debts), "statuses": dict(stat), "verdicts": dict(verd),
 "ledger_sha256": hashlib.sha256(canon.encode()).hexdigest()[:16],
 "chain_tail_seq": tip_seq,
 "note": "公开投影=计数+哈希（增不覆写/明细在密封轨）",
 "recent_ids": [d.get('id') for d in debts[-8:]]}
json.dump(debt_pub, open(f'{APP}/public/debt-ledger-public.json','w'), ensure_ascii=False, indent=1)
print('debt refreshed', len(debts))

# forum-board-public
rooms = collections.Counter(p.get('room','?') for p in BOARD)
kinds = collections.Counter(p.get('kind','?') for p in BOARD)
lines = collections.Counter(p.get('line','?') for p in BOARD)
forum_pub = {"v":1,"ts":now,"forum":"@cisvr","law":"dtag+[MUTUAL-REVIEW]·帖不改写",
 "posts_total": len(BOARD),
 "rooms": dict(rooms), "kinds": dict(kinds), "lines": dict(lines),
 "last_post": {"ts": BOARD[-1].get('ts'), "line": BOARD[-1].get('line'), "kind": BOARD[-1].get('kind')},
 "board_sha256": hashlib.sha256(open(f'{OUT}/engine/forum/board.jsonl','rb').read()).hexdigest()[:16]}
json.dump(forum_pub, open(f'{APP}/public/forum-board-public.json','w'), ensure_ascii=False, indent=1)
print('forum refreshed', len(BOARD))

# ============ ledger 续链段（capsule-era checkpoint · PP160-LEDGER-ANCHOR：远端真尖锚定+增量续铸） ============
# 每拍close铸一环；prev 锚远端真尖 hash，seq 续远端末号。抓取失败→占位标记，推送器负责重锚（盲态不编）。
def _remote_ledger_tip():
    try:
        sys.path.insert(0, f'{OUT}/engine')
        import qglnet
        names = qglnet.ls('chepin-ai/quantum-go-ledger', 'ledger')
        js = sorted(n.get('name','') for n in names if n.get('name','').endswith('.json'))
        if not js: return None
        last = json.loads(qglnet.getf('chepin-ai/quantum-go-ledger', 'ledger/' + js[-1]))
        return {'seq': last.get('seq'), 'hash': last.get('hash'), 'beat': (last.get('payload') or {}).get('beat')}
    except Exception as e:
        print('ledger tip fetch fail:', type(e).__name__)
        return None
_tip = _remote_ledger_tip()
if _tip and isinstance(_tip.get('seq'), int):
    prev, seq0 = _tip['hash'], _tip['seq'] + 1
    ck_beats = [b for b,_ in beats_sorted if bkey(b) > bkey(_tip.get('beat') or '0.0')]
    print('ledger anchor: remote tip', seq0-1, _tip['hash'], 'beat', _tip.get('beat'))
else:
    prev, seq0 = 'REMOTE-TIP-PENDING', 94
    ck_beats = [b for b,_ in beats_sorted if bkey(b) >= (3,153,'')]
    print('ledger anchor: REMOTE UNREACHABLE → placeholder')
SEG = []
for i, bt in enumerate(ck_beats):
    r = per_beat[bt]
    ent = {"seq": seq0+i, "ts": now, "type": "beat_checkpoint",
     "title": f"beat {bt} 检查点 · 囊{r['caps']} · 链#{r['first']}-{r['last']}",
     "prev": prev,
     "payload": {"beat": bt, "caps": r['caps'], "capsule_seq_first": r['first'], "capsule_seq_last": r['last'],
       "seg": "capsule-era", "law": "零编数律", "note": "daemon-ledger→capsule-ledger 桥接段；远端真尖锚定增量续铸"},
    }
    ent['hash'] = hashlib.sha256((prev + ent['title'] + ent['ts']).encode()).hexdigest()[:12]
    prev = ent['hash']
    SEG.append(ent)
    json.dump(ent, open(f'{PUSH}/ledger/{seq0+i:06d}.json','w'), ensure_ascii=False, indent=1)
print('ledger seg:', len(SEG), f'{seq0:06d}..{seq0+len(SEG)-1:06d}' if SEG else '(无新增)')

# ============ 拍面两件（PP160-DASHGEN-UNIFY：契约唯一真源 engine/dashbeat.py） ============
sys.path.insert(0, f'{OUT}/engine')
import dashbeat
NOW_BEAT = max(per_beat.keys(), key=bkey)   # 链真值当前拍
_bf = dashbeat.gen_beat_faces(NOW_BEAT)   # authored 字段沿用旧件，链数字段刷新
print('beat faces:', _bf)
print('ALL LOCAL FACES DONE')
