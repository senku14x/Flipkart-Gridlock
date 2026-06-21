"use client";
import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const TT = {
  background: "#0b1020", border: "1px solid rgba(255,255,255,.12)",
  borderRadius: 10, color: "#e7ecf5", fontSize: 12,
};
const shorten = (m) => m.replace(" (Tweedie)", "").replace(" (Poisson)", "").replace(" (lag 7d)", "");

export default function Forecaster() {
  const [f, setF] = useState(null);
  useEffect(() => { fetch("/data/forecast.json").then((r) => r.json()).then(setF).catch(() => {}); }, []);
  if (!f) return <div className="card grid h-96 place-items-center text-slate-500">Loading forecaster…</div>;

  const models = f.models.map((m) => ({ name: shorten(m.model), cov: +(m.cov20 * 100).toFixed(1), is: m.is_model }));
  const abl = f.ablation.map((a) => ({ name: a.set, cov: +(a.cov20 * 100).toFixed(1), base: a.set === "base" }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card p-5">
        <h3 className="font-semibold text-white">Model bake-off — coverage@20 on the holdout</h3>
        <p className="mt-1 text-xs text-slate-400">Four gradient-boosting models (orange) vs. three naïve baselines (grey). Train Nov–Feb, test Mar–Apr.</p>
        <div className="mt-3 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={models} layout="vertical" margin={{ left: 28, right: 16, top: 4, bottom: 0 }}>
              <CartesianGrid stroke="#ffffff12" horizontal={false} />
              <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="#ffffff20" unit="%" domain={[0, 40]} />
              <YAxis type="category" dataKey="name" width={92} tick={{ fill: "#cbd5e1", fontSize: 11 }} stroke="#ffffff20" />
              <Tooltip contentStyle={TT} cursor={{ fill: "#ffffff08" }} formatter={(v) => [`${v}%`, "coverage@20"]} />
              <Bar dataKey="cov" radius={[0, 4, 4, 0]}>
                {models.map((m, i) => <Cell key={i} fill={m.is ? "#e4572e" : "#475569"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="card p-5">
          <h3 className="font-semibold text-white">Feature engineering — base set wins</h3>
          <p className="mt-1 text-xs text-slate-400">We engineered 29 extra features in 4 groups. None beat the base 24 — granular per-cell×weekday features overfit. Honest: the ceiling is data, not features.</p>
          <div className="mt-3 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={abl} margin={{ left: -20, right: 8, top: 4, bottom: 0 }}>
                <CartesianGrid stroke="#ffffff12" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 9 }} stroke="#ffffff20" interval={0} angle={-12} dy={6} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="#ffffff20" unit="%" domain={[30, 36]} />
                <Tooltip contentStyle={TT} cursor={{ fill: "#ffffff08" }} formatter={(v) => [`${v}%`, "cov@20"]} />
                <Bar dataKey="cov" radius={[4, 4, 0, 0]}>
                  {abl.map((a, i) => <Cell key={i} fill={a.base ? "#36b3a8" : "#475569"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card grid grid-cols-2 gap-3 p-5">
          <div><div className="mono text-2xl font-bold text-acc2">+36%</div><div className="text-xs text-slate-400">cov@20 vs seasonal-naive baseline</div></div>
          <div><div className="mono text-2xl font-bold text-white">3.45</div><div className="text-xs text-slate-400">Tweedie deviance (vs 90 naive)</div></div>
          <div className="col-span-2 text-xs leading-relaxed text-slate-400">
            Genuine supervised ML with <b className="text-slate-200">real ground truth</b> and a strict temporal holdout — the one unambiguous &quot;AI&quot; model. The four libraries land within ~0.5 pt of each other: the <b className="text-slate-200">data, not the framework, is the ceiling</b>.
          </div>
        </div>
      </div>
    </div>
  );
}
