// 量子围棋 OS — 账本 / CI 数据接入层
// 仓库为公开仓库，前端只读匿名拉取，无需 token。

const REPO = 'chepin-ai/quantum-go-ledger';
const API = `https://api.github.com/repos/${REPO}`;
const RAW = `https://raw.githubusercontent.com/${REPO}/main`;

export interface LedgerEntry {
  seq: number;
  ts: string;
  type: string;
  title: string;
  prev?: string;
  prev_hash?: string;
  hash?: string;
  payload?: Record<string, unknown>;
}

export interface Metrics {
  track: string;
  patterns_total: number;
  labels_total: number;
  'recurrent(>=3)': number;
  verified: number;
  falsified: number;
  entropy: number;
  champion_winrate: number;
  agz_prior_size?: number;
  delta_patterns?: number;
  delta_entropy?: number;
  oracle_games?: number;
  oracle_fallbacks?: number;
}

export interface Plan {
  ts: string;
  track: string;
  objectives: string[];
}

export interface WorkflowRun {
  id: number;
  name: string;
  status: string | null;
  conclusion: string | null;
  created_at: string;
  updated_at: string;
  html_url: string;
}

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url, { headers: { Accept: 'application/vnd.github+json' } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return (await r.json()) as T;
}

export async function fetchLedgerEntries(limit = 40): Promise<LedgerEntry[]> {
  const listing = await getJSON<{ name: string }[]>(`${API}/contents/ledger`);
  const names = listing
    .map((f) => f.name)
    .filter((n) => n.endsWith('.json'))
    .sort()
    .slice(-limit);
  const entries = await Promise.all(
    names.map((n) => getJSON<LedgerEntry>(`${RAW}/ledger/${n}`).catch(() => null)),
  );
  return entries.filter((e): e is LedgerEntry => !!e);
}

export const fetchMetrics19 = () => getJSON<Metrics>(`${RAW}/ci/metrics19.json`);
export const fetchKG = () => getJSON<unknown>(`${RAW}/ci/kg.json`);
export const fetchSched = () => getJSON<unknown>(`${RAW}/ci/scheduler.json`);
export const fetchAgents = () => getJSON<unknown>(`${RAW}/ci/agents.json`);
export const fetchResearch = () => getJSON<unknown>(`${RAW}/ci/research_stack.json`);
export const fetchPlan19 = () => getJSON<Plan>(`${RAW}/ci/plan19.json`);
export const fetchMetrics13 = () => getJSON<Metrics>(`${RAW}/ci/metrics.json`).catch(() => null);

export async function fetchRuns(limit = 8): Promise<WorkflowRun[]> {
  const d = await getJSON<{ workflow_runs: WorkflowRun[] }>(
    `${API}/actions/runs?per_page=${limit}`,
  );
  return d.workflow_runs ?? [];
}

export const TYPE_STYLE: Record<string, { label: string; color: string }> = {
  ci_cycle_19: { label: 'CI·19路', color: '#34d399' },
  ci_cycle: { label: 'CI·13路', color: '#6ee7b7' },
  research_cycle: { label: '研究周期', color: '#60a5fa' },
  proof_accepted: { label: '证明·接受', color: '#a78bfa' },
  proof_rejected: { label: '证明·拒绝', color: '#f87171' },
  governance: { label: '治理', color: '#fbbf24' },
};

// ── PP160-API-GUARD（beat 3.160 融构：3.159 highlights 崩案教训铸械）──
// 远端 live 数据只有通过 schema 校验方可覆盖内嵌快照；坏 schema 静默回退，不崩视图。
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);

export function okLedgerEntries(v: unknown): v is LedgerEntry[] {
  return Array.isArray(v) && v.every((e) => isObj(e) && typeof e.seq === 'number' && typeof e.type === 'string');
}
export function okMetrics(v: unknown): v is Metrics {
  return isObj(v) && typeof v.track === 'string' && typeof v.patterns_total === 'number';
}
export function okPlan(v: unknown): v is Plan {
  return isObj(v) && Array.isArray(v.objectives);
}
export function okKG(v: unknown): boolean {
  if (!isObj(v) || !Array.isArray(v.nodes) || !Array.isArray(v.edges) || !Array.isArray(v.derived)) return false;
  return (v.nodes as unknown[]).every((n) => isObj(n) && Array.isArray(n.refs) && typeof n.label === 'string');
}
export function okSched(v: unknown): boolean {
  return isObj(v) && 'queue_depth' in v;
}
export function okAgents(v: unknown): boolean {
  return isObj(v) && isObj(v.roles);
}
export function okRuns(v: unknown): v is WorkflowRun[] {
  return Array.isArray(v) && v.every((r) => isObj(r) && typeof r.id === 'number');
}
