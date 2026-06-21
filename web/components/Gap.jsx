"use client";
import { useEffect, useState } from "react";

function TwoBar({ label, v, color }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-12 text-[11px] text-slate-500">{label}</span>
      <div className="h-3 flex-1 rounded bg-white/5">
        <div className="h-full rounded" style={{ width: `${Math.min(v, 100)}%`, background: color }} />
      </div>
      <span className="mono w-10 text-right text-[11px] text-slate-300">{v}%</span>
    </div>
  );
}

export default function Gap() {
  const [g, setG] = useState(null);
  useEffect(() => { fetch("/data/gap.json").then((r) => r.json()).then(setG).catch(() => {}); }, []);
  if (!g) return <div className="card grid h-64 place-items-center text-slate-500">Loading…</div>;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="card p-6">
        <div className="mono text-4xl font-bold text-white">{g.night_effort}%</div>
        <div className="text-sm text-slate-400">of enforcement effort is the night window…</div>
        <div className="mono mt-3 text-4xl font-bold text-accent">{g.night_impact}%</div>
        <div className="text-sm text-slate-400">…but that is all the congestion impact it catches.</div>
        <p className="mt-4 text-[12px] leading-snug text-slate-500">
          The 4–5am sweep alone is {g.sweep_effort}% of effort and {g.sweep_impact}% of impact. ParkPulse moves
          effort to the peak-hour chokepoints where impact concentrates. We prioritize by exposure-weighted
          impact, never by the recorded violation hour (which tracks patrol shifts).
        </p>
      </div>

      <div className="card p-6 lg:col-span-2">
        <h3 className="font-semibold text-white">Effort vs impact, by time window</h3>
        <div className="mt-4 space-y-4">
          {g.windows.map((w, i) => (
            <div key={i}>
              <div className="text-sm text-slate-300">{w.name}</div>
              <div className="mt-1 space-y-1">
                <TwoBar label="effort" v={w.effort} color="#64748b" />
                <TwoBar label="impact" v={w.impact} color={w.impact >= w.effort ? "#36b3a8" : "#e4572e"} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex gap-4 text-[12px] text-slate-400">
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-3 rounded bg-slate-500" />share of effort</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-3 rounded bg-acc2" />share of impact</span>
        </div>
      </div>
    </div>
  );
}
