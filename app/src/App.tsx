import { useEffect, useMemo, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import {
  fetchLedgerEntries, fetchMetrics19, fetchPlan19, fetchRuns,
  fetchKG, fetchSched, fetchAgents,
  TYPE_STYLE, type LedgerEntry, type Metrics, type Plan, type WorkflowRun,
} from './qgo/api';
import { KGGraph, KGLegend, KGDetail, RelFilter, REL_STYLE, Lifecycle, type KG } from './qgo/KG';
import { SNAPSHOT } from './qgo/snapshot';
import { AtlasView } from './qgo/Atlas';
import { ConsoleView } from './qgo/Console';
import { TrackView } from './qgo/Track';
import { GlobalView } from './qgo/Global';
import { BeatView } from './qgo/Beat';

// ---------- 通用小组件 ----------
function Panel({ title, right, children, className = '' }: {
  title: string; right?: React.ReactNode; children: React.ReactNode; className?: string;
}) {
  return (
    <section className={`rounded-xl border border-neutral-800 bg-neutral-900/60 p-4 ${className}`}>
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-widest text-neutral-300">{title}</h2>
        {right}
      </header>
      {children}
    </section>
  );
}

function Kpi({ label, value, sub, tone = 'text-neutral-100' }: {
  label: string; value: string | number; sub?: string; tone?: string;
}) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <div className="text-[11px] tracking-widest text-neutral-500">{label}</div>
      <div className={`mt-1 font-mono text-2xl font-semibold ${tone}`}>{value}</div>
      {sub && <div className="mt-1 text-[11px] text-neutral-500">{sub}</div>}
    </div>
  );
}

const ROADMAP = [
  { id: 'P1', name: '19路 CI 主轨', status: 'live', desc: '自我博弈 + 蒸馏 + 自规划，每12小时' },
  { id: 'P2', name: 'AGZ full4000 ✓ / KataGo 待人工', status: 'blocked', desc: 'AGZ已接入(负结果); KataGo 403 — 人工工单 o_katago' },
  { id: 'P3', name: '元定势 M2 提取（跨尺度）', status: 'done', desc: '已完成：2 个跨尺度不变量 + 1 个标度依赖量，账本 #55' },
  { id: 'P4', name: 'Lean 形式化 7文件18定理', status: 'done', desc: '判定器/协议/D4/提子对偶/三角判据 N3·N4 全绿' },
  { id: 'P5', name: '复杂度脊柱驱动规划', status: 'active', desc: '模式数/熵轨迹 → 自主立项' },
];

const STATUS_STYLE: Record<string, string> = {
  live: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  active: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  queued: 'bg-neutral-500/15 text-neutral-400 border-neutral-600/30',
  blocked: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  done: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
};
const STATUS_LABEL: Record<string, string> = { live: '运行中', active: '推进中', queued: '排队', blocked: '待人工', done: '已完成' };

// 自适应调度: 下一周期 = scheduler.ts + eta_hours(由 CI 周期收尾按状态计算); 缺省回退 6h
interface Sched { ts: string; eta_hours: number; workload: Record<string, number>; rationale: string[]; queue_depth: number }
interface Order { id: string; node?: string; line: string; title: string; status: string; note: string }
interface CDE { Z: number; dz: number; stalled: boolean; series?: { Z: number; dz: number; ts: string }[] }
interface Audit { verdict: string; fails: string[]; warns: string[]; planes: Record<string, Record<string, unknown>>; chain?: { ts: string; verdict: string; hash: string }[] }
interface Progress { series?: { ts: string; verdict: string; reasons: string[]; discrepancies: string[]; hash: string; Z?: number }[] }
interface AgentRole { status: string; runs: number; errors: number; last_op?: string; last_ts?: string; last_error?: string }
const SCHED0 = (SNAPSHOT as unknown as { scheduler?: Sched }).scheduler;
const AGENTS0 = (SNAPSHOT as unknown as { agents?: { roles?: Record<string, AgentRole> } }).agents?.roles ?? {};
const KG0 = (SNAPSHOT as unknown as { kg?: KG }).kg ?? null;
const ORDERS0 = (SNAPSHOT as unknown as { orders?: { orders?: Order[] } }).orders?.orders ?? [];
const CDE0 = (SNAPSHOT as unknown as { cde?: CDE }).cde ?? null;
const AUDIT0 = (SNAPSHOT as unknown as { audit?: Audit }).audit ?? null;
const PROG0 = (SNAPSHOT as unknown as { progress?: Progress }).progress ?? null;
const INVAR0 = (SNAPSHOT as unknown as { invariants?: { invariants?: { id: string; name: string; strength: string }[] } }).invariants?.invariants ?? [];
function nextCronUTC(from = new Date(), sched: Sched | null = null): Date {
  if (sched?.ts) {
    const d = new Date(new Date(sched.ts).getTime() + (sched.eta_hours ?? 6) * 3.6e6);
    if (d > from) return d;
    return from; // 已到期 — 控制器节拍器随时可能触发
  }
  return new Date(from.getTime() + 6 * 3.6e6);
}

function fmtCountdown(ms: number) {
  if (ms < 0) ms = 0;
  const h = Math.floor(ms / 3.6e6), m = Math.floor((ms % 3.6e6) / 6e4), s = Math.floor((ms % 6e4) / 1e3);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function App() {
  const [entries, setEntries] = useState<LedgerEntry[]>([...SNAPSHOT.entries] as unknown as LedgerEntry[]);
  const [metrics, setMetrics] = useState<Metrics | null>(SNAPSHOT.metrics19 as Metrics);
  const [plan, setPlan] = useState<Plan | null>(SNAPSHOT.plan19 as unknown as Plan);
  const [runs, setRuns] = useState<WorkflowRun[]>([...SNAPSHOT.runs] as WorkflowRun[]);
  const [err, setErr] = useState<string | null>(null);
  const [now, setNow] = useState(new Date());
  const [sched, setSched] = useState<Sched | null>(SCHED0 ?? null);
  const [agents, setAgents] = useState<Record<string, AgentRole>>(AGENTS0);
  const [kg, setKg] = useState<KG | null>(KG0);
  const [syncedAt, setSyncedAt] = useState<Date | null>(null);
  const [selNode, setSelNode] = useState<string | null>(null);
  const [orders, setOrders] = useState<Order[]>(ORDERS0);
  const [cde, setCde] = useState<CDE | null>(CDE0);
  const [audit, setAudit] = useState<Audit | null>(AUDIT0);
  const [prog, setProg] = useState<Progress | null>(PROG0);
  const [relFilter, setRelFilter] = useState<Set<string>>(new Set(Object.keys(REL_STYLE)));
  const [view, setView] = useState<'beat' | 'os' | 'atlas' | 'console' | 'track' | 'global'>('beat');

  useEffect(() => {
    // 快照先行（构建期内嵌，任何网络环境可见）；实时拉取成功则静默覆盖，失败不打扰。
    const load = () => {
      Promise.all([fetchLedgerEntries(40), fetchMetrics19(), fetchPlan19(), fetchRuns(8)])
        .then(([e, m, p, r]) => { setEntries(e); setMetrics(m); setPlan(p); setRuns(r); setErr(null); setSyncedAt(new Date()); })
        .catch(() => { /* 预览沙箱可能拦截外发请求 — 快照已在界面上，静默回退 */ });
      fetchSched().then((v) => setSched(v as Sched)).catch(() => {});
      fetchAgents().then((v) => setAgents((v as { roles?: Record<string, AgentRole> })?.roles ?? {})).catch(() => {});
      fetchKG().then((v) => setKg(v as KG)).catch(() => {});
      fetch(`${'https://raw.githubusercontent.com/chepin-ai/quantum-go-ledger/main'}/ci/orders.json`).then((r) => r.json()).then((v) => setOrders(v.orders ?? [])).catch(() => {});
      fetch(`${'https://raw.githubusercontent.com/chepin-ai/quantum-go-ledger/main'}/ci/complexity_index.json`).then((r) => r.json()).then((v) => setCde(v as CDE)).catch(() => {});
      fetch(`${'https://raw.githubusercontent.com/chepin-ai/quantum-go-ledger/main'}/ci/audit.json`).then((r) => r.json()).then((v) => setAudit(v as Audit)).catch(() => {});
      fetch(`${'https://raw.githubusercontent.com/chepin-ai/quantum-go-ledger/main'}/ci/progress.json`).then((r) => r.json()).then((v) => setProg(v as Progress)).catch(() => {});
    };
    load();
    const t1 = setInterval(load, 60_000);
    const t2 = setInterval(() => setNow(new Date()), 1000);
    return () => { clearInterval(t1); clearInterval(t2); };
  }, []);

  const curve = useMemo(() => entries
    .filter((e) => e.type.startsWith('ci_cycle') && e.payload?.metrics)
    .map((e) => {
      const m = e.payload!.metrics as Metrics;
      return { seq: e.seq, track: m.track === '19x19' ? '19路' : '13路', patterns: m.patterns_total, entropy: m.entropy };
    }), [entries]);

  const last = entries[entries.length - 1];
  const lastRun = runs[0];
  const nextRun = nextCronUTC(now, sched);
  const queueOps = ((SNAPSHOT as { research?: { queue?: readonly { kind: string }[] } }).research?.queue ?? []).map((o) => o.kind);
  const ciCycles19 = entries.filter((e) => e.type === 'ci_cycle_19').length;

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-200">
      <div className="mx-auto max-w-6xl px-4 py-6">
        {/* 头部 */}
        <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-neutral-50">量子围棋 OS</h1>
            <p className="mt-1 text-xs text-neutral-500">
              哈希链账本 · 语法引擎 · Action CI 全自动主干 — chepin-ai/quantum-go-ledger
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setView('beat')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'beat' ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}`}>拍面</button>
            <button onClick={() => setView('os')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'os' ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}`}>监控 OS</button>
            <button onClick={() => setView('atlas')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'atlas' ? 'border-amber-500/50 bg-amber-500/10 text-amber-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}`}>战略全图</button>
            <button onClick={() => setView('console')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'console' ? 'border-violet-500/50 bg-violet-500/10 text-violet-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}` }>中控</button>
            <button onClick={() => setView('track')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'track' ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}`}>追踪</button>
            <button onClick={() => setView('global')}
              className={`rounded-lg border px-3 py-1.5 text-xs tracking-widest transition ${view === 'global' ? 'border-yellow-500/50 bg-yellow-500/10 text-yellow-300' : 'border-neutral-800 text-neutral-500 hover:text-neutral-300'}`}>全局</button>
          </div>
          <div className="text-right font-mono text-xs text-neutral-500">
            <div>链头 #{last?.seq ?? '…'} <span className="text-emerald-400">{last?.hash?.slice(0, 12) ?? ''}</span></div>
            <div>{last?.ts ? new Date(last.ts).toLocaleString('zh-CN') : ''}</div>
          </div>
        </header>

        {err && <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">数据拉取失败：{err}（60 秒后自动重试）</div>}

        {view === 'beat' ? (
          <BeatView />
        ) : view === 'atlas' ? (
          <AtlasView kg={kg} />
        ) : view === 'console' ? (
          <ConsoleView />
        ) : view === 'track' ? (
          <TrackView />
        ) : view === 'global' ? (
          <GlobalView />
        ) : (
        <>
        {/* OS 进程管理 */}
        <Panel title="操作系统 · 自驱多进程（监控 / 调度 / 诊断）" className="mb-4"
          right={<span className="text-[11px] text-neutral-500">节拍器每小时评估 · 60s 轮询即时同步{syncedAt ? ` · 已同步 ${syncedAt.toLocaleTimeString('zh-CN')}` : ' · 快照态'}</span>}>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* 调度卡 */}
            <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <div className="text-[11px] tracking-widest text-neutral-500">自适应调度器</div>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="font-mono text-xl text-emerald-300">{sched ? `${sched.eta_hours}h` : '…'}</span>
                <span className="text-[11px] text-neutral-500">下周期节奏</span>
                <span className="ml-auto font-mono text-sm text-emerald-300">
                  {sched && nextCronUTC(now, sched) <= now ? '到期·待触发' : fmtCountdown(nextCronUTC(now, sched).getTime() - now.getTime())}
                </span>
              </div>
              <ul className="mt-2 space-y-1 text-[11px] text-neutral-400">
                {(sched?.rationale ?? ['调度表未生成 — CI 周期收尾时自动计算']).map((r, i) => <li key={i}>· {r}</li>)}
              </ul>
              <div className="mt-2 text-[11px] text-neutral-600">
                依据: 栈积压/联赛在队→2h · 高增长→6h · 趋缓→12h深循环 · error→12h+诊断 · 保底 cron 24h
              </div>
            </div>
            {/* 进程表 */}
            <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <div className="text-[11px] tracking-widest text-neutral-500">进程表（多智能体角色）</div>
              <table className="mt-1 w-full text-xs">
                <tbody>
                  {(['player', 'distiller', 'verifier', 'planner', 'reporter'] as const).map((r) => {
                    const a = agents[r];
                    const cn = a?.status === 'ok' ? 'text-emerald-400' : a?.status === 'error' ? 'text-red-400' : 'text-neutral-500';
                    return (
                      <tr key={r} className="border-b border-neutral-800/40 last:border-0">
                        <td className="py-1 font-mono text-neutral-300">{r}</td>
                        <td className={`py-1 font-mono ${cn}`}>{a?.status ?? 'idle'}</td>
                        <td className="py-1 text-right text-neutral-500">{a ? `${a.runs}r/${a.errors}e` : '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {/* 诊断 */}
            <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <div className="text-[11px] tracking-widest text-neutral-500">诊断流</div>
              <ul className="mt-1 space-y-1 text-[11px]">
                {Object.entries(agents).filter(([, a]) => a.status === 'error').map(([r, a]) => (
                  <li key={r} className="text-red-300">{r}: {a.last_error ?? 'error'}</li>
                ))}
                {Object.values(agents).every((a) => a.status !== 'error') && (
                  <li className="text-emerald-300">全部进程健康 · 最近算子错误率 0</li>
                )}
                <li className="text-neutral-500">研究栈积压: {sched?.queue_depth ?? '…'} · 算子预算 2/周期 · 时间盒 240s</li>
              </ul>
            </div>
          </div>
        </Panel>

        {/* 工单台账 · 多线协同 */}
        <Panel title="工单台账 · 规划节点自动对账执行（多线协同突进）" className="mb-4"
          right={<span className="text-[11px] text-neutral-500">对账器每周期比对 KG未来节点↔研究栈, 缺失即播种 · 不遗漏</span>}>
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
            {(['formal', 'experiment', 'campaign', 'human'] as const).map((line) => {
              const LN: Record<string, string> = { formal: '形式化线', experiment: '实验线', campaign: '运动线', human: '人工线' };
              const LC: Record<string, string> = { formal: '#a78bfa', experiment: '#34d399', campaign: '#fbbf24', human: '#f87171' };
              const items = orders.filter((o) => o.line === line);
              return (
                <div key={line} className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-2.5">
                  <div className="mb-1.5 text-[10px] tracking-widest" style={{ color: LC[line] }}>{LN[line]}（{items.length}）</div>
                  <div className="space-y-1">
                    {items.map((o) => (
                      <div key={o.id} title={o.note} className="rounded border border-neutral-800/60 px-2 py-1">
                        <div className="flex items-center gap-1.5 text-[11px]">
                          <span className={`h-1.5 w-1.5 rounded-full ${o.status === 'running' ? 'bg-emerald-400' : o.status === 'blocked' ? 'bg-red-400' : o.status === 'done' ? 'bg-violet-400' : 'bg-neutral-500'}`} />
                          <span className="text-neutral-300">{o.title}</span>
                        </div>
                        <div className="mt-0.5 truncate text-[9.5px] text-neutral-600">{o.note}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        {/* 四面自审 */}
        <Panel title="自审/自检 · 语境-语法-语义-语用" className="mb-4"
          right={<span className={`text-[11px] ${audit?.verdict === 'ok' ? 'text-emerald-400' : audit ? 'text-amber-400' : 'text-neutral-500'}`}>
            {audit ? `裁决 ${audit.verdict}${audit.warns.length ? ' · warn: ' + audit.warns.join(',') : ''} · 自审链 ${audit.chain?.length ?? 0} 节点 ${audit.chain?.length ? '#' + audit.chain[audit.chain.length - 1].hash.slice(0, 8) : ''}` : '待首个审计周期'}
          </span>}>
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {([['syntax', '语法', '引擎/形式化/哈希链'], ['semantics', '语义', 'KG闸口/三元组/三角'], ['context', '语境', '观察者注册/分布'], ['pragmatics', '语用', '工单执行/CDE']] as const).map(([k, name, desc]) => {
              const pl = audit?.planes?.[k];
              const st = (pl?.status as string) ?? '…';
              const cc = st === 'ok' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : st === 'warn' ? 'text-amber-300 border-amber-500/30 bg-amber-500/10' : st === 'fail' ? 'text-red-300 border-red-500/30 bg-red-500/10' : 'text-neutral-500 border-neutral-800';
              return (
                <div key={k} className={`rounded-lg border p-2.5 ${cc}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">{name}</span>
                    <span className="font-mono text-[10px]">{st}</span>
                  </div>
                  <div className="mt-0.5 text-[10px] opacity-70">{desc}</div>
                  {pl && (
                    <div className="mt-1 font-mono text-[9.5px] opacity-80">
                      {k === 'syntax' && `账本${String(pl.ledger_entries ?? '…')} · Lean${String(pl.lean_files ?? '…')}文件`}
                      {k === 'semantics' && `冲突${String(pl.kg_alerts ?? '…')} · 开放三角${String(pl.open_triangles ?? '…')}`}
                      {k === 'context' && `观察者${String(pl.observers ?? '…')}`}
                      {k === 'pragmatics' && `工单${String(pl.orders_done ?? '…')}/${String(pl.orders_total ?? '…')} · Z ${String(pl.Z ?? '…')}`}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>

        {/* 进展裁决链 */}
        <Panel title="进展裁决 · 真实进展 vs 空转（哈希链自审）" className="mb-4"
          right={<span className="text-[11px] text-neutral-500">重算复核·反刷量闸·裁决链 {prog?.series?.length ?? 0} 节点</span>}>
          <div className="flex flex-wrap items-center gap-3">
            {(() => {
              const lastNode = prog?.series?.[prog.series.length - 1];
              const vc = lastNode?.verdict;
              const cc = vc === 'REAL' ? 'text-emerald-300 border-emerald-500/40 bg-emerald-500/10'
                : vc === 'MOTION' ? 'text-amber-300 border-amber-500/40 bg-amber-500/10'
                : vc === 'REGRESS' ? 'text-red-300 border-red-500/40 bg-red-500/10' : 'text-neutral-500 border-neutral-800';
              const CN: Record<string, string> = { REAL: '真实进展', MOTION: '空转警告', REGRESS: '倒退/不符' };
              return (
                <div className={`rounded-lg border px-4 py-2.5 ${cc}`}>
                  <div className="text-[10px] opacity-70">本周期裁决</div>
                  <div className="font-mono text-lg">{vc ? `${CN[vc] ?? vc}` : '待裁决'}</div>
                  {lastNode && <div className="mt-0.5 max-w-md truncate text-[10px] opacity-80">{lastNode.reasons.join(' · ')}</div>}
                </div>
              );
            })()}
            <div className="flex-1 space-y-1">
              {(prog?.series ?? []).slice(-5).reverse().map((n, i) => (
                <div key={i} className="flex items-center gap-2 text-[11px]">
                  <span className={`h-1.5 w-1.5 rounded-full ${n.verdict === 'REAL' ? 'bg-emerald-400' : n.verdict === 'MOTION' ? 'bg-amber-400' : 'bg-red-400'}`} />
                  <span className="text-neutral-500 font-mono">{n.ts.slice(5, 16)}</span>
                  <span className="text-neutral-300">{n.verdict}</span>
                  <span className="truncate text-neutral-600">{n.reasons.join(' · ')}</span>
                  <span className="ml-auto font-mono text-[9px] text-neutral-700">{n.hash.slice(0, 8)}</span>
                </div>
              ))}
              {!prog?.series?.length && <div className="text-xs text-neutral-500">裁决链待首个周期 — 裁决器每周期重算KPI并与声明比对, 防自报防刷量</div>}
            </div>
          </div>
        </Panel>

        {/* KPI */}
        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Kpi label="模式库 PATTERNS" value={metrics?.patterns_total ?? '…'} sub={`Δ +${metrics?.delta_patterns ?? 0}`} />
          <Kpi label="结局标签 LABELS" value={metrics?.labels_total ?? '…'} />
          <Kpi label="复发 ≥3" value={metrics?.['recurrent(>=3)'] ?? '…'} sub="元定势候选池" />
          <Kpi label="验证 / 证伪" value={`${metrics?.verified ?? '…'} / ${metrics?.falsified ?? '…'}`} tone="text-emerald-300" />
          <Kpi label="熵 ENTROPY" value={metrics?.entropy ?? '…'} sub={`Δ +${metrics?.delta_entropy ?? 0}`} />
          <Kpi label="擂主胜率" value={metrics ? `${Math.round(metrics.champion_winrate * 100)}%` : '…'} sub={`AGZ 先验 ${metrics?.agz_prior_size ?? 400}`} />
        </div>

        {/* 复杂度驱动引擎 */}
        <div className="mb-4 flex flex-wrap items-center gap-4 rounded-xl border border-neutral-800 bg-neutral-900/60 px-4 py-3">
          <div>
            <div className="text-[10px] tracking-widest text-neutral-500">复杂度驱动引擎 Z</div>
            <div className="font-mono text-xl text-emerald-300">{cde ? cde.Z.toFixed(2) : '…'}</div>
          </div>
          <div>
            <div className="text-[10px] text-neutral-500">dZ/dt</div>
            <div className={`font-mono text-lg ${(cde?.dz ?? 0) > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {cde ? (cde.dz > 0 ? '+' : '') + cde.dz.toFixed(3) : '…'}
            </div>
          </div>
          <div className="text-[11px] text-neutral-500">
            Z = 熵 + 0.5·ln模式 + 0.02·复发池 + 5·KG密度 + 0.2·定理数 · 连续2周期停滞⇒攻坚模式(提速加局)
            {cde?.stalled && <span className="ml-2 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-amber-300">攻坚模式</span>}
          </div>
          <span className="ml-auto text-[10px] text-neutral-600">终极目标: 提升/超越自身算法复杂度 — 评估+驱动闭环</span>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* 复杂度曲线 */}
          <Panel title="复杂度脊柱 · 模式数 / 熵（按账本序号）">
            <div className="h-56">
              <ResponsiveContainer>
                <LineChart data={curve} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="#262626" strokeDasharray="3 3" />
                  <XAxis dataKey="seq" tick={{ fill: '#737373', fontSize: 11 }} />
                  <YAxis yAxisId="l" tick={{ fill: '#737373', fontSize: 11 }} />
                  <YAxis yAxisId="r" orientation="right" domain={[0, 'auto']} tick={{ fill: '#737373', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#171717', border: '1px solid #404040', fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line yAxisId="l" type="monotone" dataKey="patterns" name="模式数" stroke="#34d399" strokeWidth={2} dot={{ r: 2 }} />
                  <Line yAxisId="r" type="monotone" dataKey="entropy" name="熵" stroke="#60a5fa" strokeWidth={2} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-[11px] text-neutral-500">19路主轨（#47 起） · 13路已降级为探针测试床 · 共 {ciCycles19} 个 19路 CI 周期</p>
          </Panel>

          {/* 驱动迭代 */}
          <Panel title="驱动迭代 · Action CI"
            right={<a className="text-[11px] text-neutral-500 underline hover:text-neutral-300" href="https://github.com/chepin-ai/quantum-go-ledger/actions" target="_blank" rel="noreferrer">Actions ↗</a>}>
            <div className="mb-3 flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <div>
                <div className="text-[11px] text-neutral-500">下一周期（自适应调度 · 节拍器每小时评估）</div>
                <div className="font-mono text-xl text-emerald-300">{fmtCountdown(nextRun.getTime() - now.getTime())}</div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-neutral-500">最近运行</div>
                {lastRun ? (
                  <a href={lastRun.html_url} target="_blank" rel="noreferrer"
                    className={`font-mono text-sm ${lastRun.conclusion === 'success' ? 'text-emerald-300' : lastRun.conclusion === 'failure' ? 'text-red-300' : 'text-amber-300'}`}>
                    {lastRun.conclusion ?? lastRun.status} ↗
                  </a>
                ) : <span className="text-neutral-500">…</span>}
              </div>
            </div>
            <ul className="space-y-1.5">
              {runs.slice(0, 5).map((r) => (
                <li key={r.id} className="flex items-center justify-between rounded-md border border-neutral-800/60 px-3 py-1.5 text-xs">
                  <span className="text-neutral-400">{new Date(r.created_at).toLocaleString('zh-CN')}</span>
                  <span className={`font-mono ${r.conclusion === 'success' ? 'text-emerald-400' : r.conclusion === 'failure' ? 'text-red-400' : 'text-amber-400'}`}>
                    {r.conclusion ?? r.status}
                  </span>
                </li>
              ))}
            </ul>
          </Panel>

          {/* 规划指导 */}
          <Panel title="指导规划 · 路线图 P1–P5">
            <ul className="space-y-2">
              {ROADMAP.map((r) => (
                <li key={r.id} className="flex items-start gap-3 rounded-lg border border-neutral-800/60 p-2.5">
                  <span className="mt-0.5 font-mono text-xs text-neutral-500">{r.id}</span>
                  <div className="flex-1">
                    <div className="text-sm text-neutral-200">{r.name}</div>
                    <div className="text-[11px] text-neutral-500">{r.desc}</div>
                  </div>
                  <span className={`rounded-full border px-2 py-0.5 text-[11px] ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>
                </li>
              ))}
            </ul>
          </Panel>

          {/* 全生命周期全图 */}
          <Panel title="全生命周期 · 路径网络全图（考古 → 现在 → 未来前缘）" className="lg:col-span-2"
            right={<span className="text-[11px] text-neutral-500">绑定知识图谱基底 · ⇠在队 = 与研究栈联动</span>}>
            {kg ? <Lifecycle kg={kg} queueOps={queueOps} /> : <div className="text-xs text-neutral-500">知识图谱加载中…</div>}
          </Panel>

          {/* 同构网络 */}
          <Panel title="同构网络 · 知识谱系基底全貌（米田嵌入）" className="lg:col-span-2"
            right={<span className="text-[11px] text-neutral-500">每 CI 周期即时重构 · {kg ? `${kg.nodes.length}节点/${kg.edges.length}边+${kg.derived.length}导出` : '…'}</span>}>
            {kg ? (<>
              <RelFilter active={relFilter} onToggle={(r) => setRelFilter((prev) => {
                const nx = new Set(prev); if (nx.has(r)) nx.delete(r); else nx.add(r); return nx;
              })} />
              <KGGraph kg={kg} activeOps={queueOps} selected={selNode} onSelect={setSelNode} relFilter={relFilter} />
              {selNode && <KGDetail kg={kg} nodeId={selNode} />}
              <KGLegend kg={kg} />
              <div className="mt-2 rounded-lg border border-violet-500/30 bg-violet-500/10 p-2.5 text-[11px] text-violet-200">
                米田嵌入：{kg.yoneda.law} · 观察者谱系：{(kg.yoneda.observers ?? []).join(' / ')}
              </div>
              {INVAR0.length > 0 && (
                <div className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-[11px] text-amber-200">
                  序关系不变量登记（弱普遍棋理·跨观察者同号）：
                  {INVAR0.map((v) => `${v.id} ${v.name}〔${v.strength}〕`).join(' · ')}
                </div>
              )}
            </>) : <div className="text-xs text-neutral-500">知识图谱加载中…</div>}
          </Panel>

          {/* 递归引擎 */}
          <Panel title="递归引擎 · 研究栈与算子史"
            right={<span className="text-[11px] text-neutral-500">周期 {(SNAPSHOT as { research?: { cycle?: number } }).research?.cycle ?? '…'}</span>}>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {((SNAPSHOT as { research?: { queue?: readonly { kind: string; priority: number }[] } }).research?.queue ?? []).map((o, i) => (
                <span key={i} className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-[11px] text-cyan-300">
                  {o.kind} ·p{o.priority}
                </span>
              ))}
              {((SNAPSHOT as { research?: { queue?: readonly unknown[] } }).research?.queue ?? []).length === 0 && (
                <span className="text-xs text-neutral-500">队列空 — 下周期自举播种</span>
              )}
            </div>
            <ul className="space-y-1.5">
              {((SNAPSHOT as { researchHist?: { runs?: readonly { cycle: number; ts: string; results: readonly { op: string; res: unknown; spawned: readonly string[] }[] }[] } }).researchHist?.runs ?? []).slice(-4).reverse().map((r, i) => (
                <li key={i} className="rounded-md border border-neutral-800/60 px-3 py-2 text-xs">
                  <div className="mb-1 flex justify-between text-neutral-500">
                    <span>周期 {r.cycle}</span><span>{new Date(r.ts).toLocaleString('zh-CN')}</span>
                  </div>
                  {r.results.map((x, j) => (
                    <div key={j} className="truncate text-neutral-300">
                      <span className="text-cyan-400">{x.op}</span>
                      <span className="text-neutral-500"> → {JSON.stringify(x.res).slice(0, 90)}</span>
                      {x.spawned.length > 0 && <span className="text-emerald-400"> ⇢ {x.spawned.join(',')}</span>}
                    </div>
                  ))}
                </li>
              ))}
            </ul>
          </Panel>

          {/* CI 自规划 */}
          <Panel title="CI 自规划目标"
            right={<span className="text-[11px] text-neutral-500">{plan?.ts ? new Date(plan.ts).toLocaleString('zh-CN') : ''}</span>}>
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-neutral-300">
              {plan?.objectives.map((o, i) => <li key={i}>{o}</li>) ?? <li>…</li>}
            </ul>
            <div className="mt-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-200">
              授权已确认：W1 — Lean 云端 lean-action CI（P4）与 P2 — AGZ full4000 + KataGo 公开谱接入，均已开工（账本 #56）。
            </div>
          </Panel>
        </div>

        {/* 账本流 */}
        <Panel title="账本流 · 哈希链（最近 20 条）" className="mt-4">
          <ul className="space-y-1.5">
            {[...entries].slice(-20).reverse().map((e) => {
              const st = TYPE_STYLE[e.type] ?? { label: e.type, color: '#a3a3a3' };
              return (
                <li key={e.seq} className="flex items-center gap-3 rounded-md border border-neutral-800/50 px-3 py-2">
                  <span className="font-mono text-xs text-neutral-600">#{e.seq}</span>
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                    style={{ color: st.color, background: st.color + '1f', border: `1px solid ${st.color}44` }}>
                    {st.label}
                  </span>
                  <span className="flex-1 truncate text-xs text-neutral-300">{e.title}</span>
                  <span className="hidden font-mono text-[10px] text-neutral-600 sm:block">
                    {(e.hash ?? '').slice(0, 10)} · {new Date(e.ts).toLocaleString('zh-CN')}
                  </span>
                </li>
              );
            })}
          </ul>
        </Panel>
        </>
        )}

        <footer className="mt-6 text-center text-[11px] text-neutral-600">
          量子围棋 OS — 内嵌快照 {new Date(SNAPSHOT.fetchedAt).toLocaleString('zh-CN')} · 实时通道可用时静默覆盖 · 语法引擎 w8 + LV2 + AGZ 先验 · 白皮书 v6.27a · 全图 v1 · 中控 v1
        </footer>
      </div>
    </div>
  );
}
