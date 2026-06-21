"use client";
import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot,
} from "recharts";

const TT = {
  background: "#0b1020", border: "1px solid rgba(255,255,255,.12)",
  borderRadius: 10, color: "#e7ecf5", fontSize: 12,
};

export default function Optimizer() {
  const [data, setData] = useState(null);
  const [n, setN] = useState(20);
  useEffect(() => { fetch("/data/pareto.json").then((r) => r.json()).then(setData).catch(() => {}); }, []);

  if (!data) return <div className="card grid h-96 place-items-center text-slate-500">Loading optimizer…</div>;
  const cur = data.beats[n - 1];
  const chart = data.beats.map((b) => ({ n: b.n, greedy: b.greedy, naive: b.naive }));
  const plan = data.beats.slice(0, n);

  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <div className="card p-6 lg:col-span-3">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-sm text-slate-400">Deploy</div>
            <div className="mono text-5xl font-bold text-white">
              {n} <span className="text-2xl font-medium text-slate-400">patrol beats</span>
            </div>
          </div>
          <div className="text-right">
            <div className="mono text-5xl font-bold text-acc2">{cur.greedy}%</div>
            <div className="text-sm text-slate-400">of citywide impact covered</div>
          </div>
        </div>

        <input
          type="range" min={1} max={50} value={n} onChange={(e) => setN(+e.target.value)}
          className="mt-5 w-full accent-[#e4572e]"
        />
        <div className="mono flex justify-between text-[11px] text-slate-500"><span>1</span><span>25</span><span>50</span></div>

        <div className="mt-4 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#ffffff12" />
              <XAxis dataKey="n" tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="#ffffff20" />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="#ffffff20" unit="%" domain={[0, 80]} />
              <Tooltip contentStyle={TT} formatter={(v, k) => [`${v}%`, k === "greedy" ? "Greedy" : "Naive top-N"]} labelFormatter={(l) => `${l} beats`} />
              <Line type="monotone" dataKey="naive" stroke="#64748b" strokeDasharray="5 4" dot={false} strokeWidth={1.6} />
              <Line type="monotone" dataKey="greedy" stroke="#36b3a8" dot={false} strokeWidth={2.6} />
              <ReferenceDot x={n} y={cur.greedy} r={5} fill="#e4572e" stroke="#fff" strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex items-center gap-4 text-[12px] text-slate-400">
          <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-4 bg-acc2" />greedy max-coverage</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-4 bg-slate-500" />naive top-N (clumps)</span>
        </div>
      </div>

      <div className="card flex flex-col p-5 lg:col-span-2">
        <div className="flex items-baseline justify-between">
          <h3 className="font-semibold text-white">Deployment plan</h3>
          <span className="text-xs text-slate-500">where + when</span>
        </div>
        <div className="mt-3 -mr-2 max-h-80 space-y-1.5 overflow-y-auto pr-2">
          {plan.map((b) => (
            <div key={b.n} className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2">
              <span className="mono grid h-6 w-6 shrink-0 place-items-center rounded-md bg-accent/20 text-xs text-accent">{b.n}</span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-white">{b.station}</div>
                <div className="truncate text-[11px] text-slate-400">{b.loc}</div>
              </div>
              <span className="mono shrink-0 rounded bg-acc2/15 px-1.5 py-0.5 text-[11px] text-acc2">{b.win}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
