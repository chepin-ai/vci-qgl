import { useEffect, useState } from 'react';

type DashBeat = {
  beat: string;
  chain_seq: number;
  chain_tip: string;
  pc: number;
  ts: string;
  highlights: string[];
  pending: string[];
};

export function BeatView() {
  const [d, setD] = useState<DashBeat | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    const load = () =>
      fetch(`${import.meta.env.BASE_URL}dash-beat.json`, { cache: 'no-store' })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((v) => { setD(v as DashBeat); setErr(false); })
        .catch(() => setErr(true));
    load();
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, []);

  if (err) return <div className="rounded-lg border border-neutral-800 p-6 text-sm text-neutral-500">dash-beat.json 未就绪</div>;
  if (!d) return <div className="p-6 text-sm text-neutral-500">载入拍面…</div>;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5">
        <div className="text-[11px] tracking-widest text-neutral-500">QGL 主线 · 当前拍</div>
        <div className="mt-2 flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <span className="font-mono text-4xl font-bold text-emerald-300">beat {d.beat}</span>
          <span className="font-mono text-sm text-neutral-400">链 #{d.chain_seq}</span>
          <span className="font-mono text-sm text-emerald-400">{d.chain_tip}</span>
          <span className="font-mono text-xs text-neutral-500">pc={d.pc} · {d.ts}</span>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-neutral-800 p-4">
          <div className="mb-2 text-[11px] tracking-widest text-neutral-500">本拍产出（实测铸囊）</div>
          <ul className="space-y-1.5 text-sm text-neutral-300">
            {d.highlights.map((h, i) => <li key={i} className="flex gap-2"><span className="text-emerald-400">◆</span><span>{h}</span></li>)}
          </ul>
        </div>
        <div className="rounded-xl border border-neutral-800 p-4">
          <div className="mb-2 text-[11px] tracking-widest text-neutral-500">候件（主动驱动中）</div>
          <ul className="space-y-1.5 text-sm text-neutral-400">
            {d.pending.map((p, i) => <li key={i} className="flex gap-2"><span className="text-amber-400">◇</span><span>{p}</span></li>)}
          </ul>
        </div>
      </div>
      <div className="text-[11px] text-neutral-600">数据源：同域 dash-beat.json（每拍重写，随版本发布）· 60s 轮询</div>
    </div>
  );
}
