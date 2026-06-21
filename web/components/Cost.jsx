"use client";
import { useEffect, useState } from "react";
import { inr } from "../lib/format";

export default function Cost() {
  const [c, setC] = useState(null);
  useEffect(() => { fetch("/data/cost.json").then((r) => r.json()).then(setC).catch(() => {}); }, []);
  if (!c) return <div className="card grid h-72 place-items-center text-slate-500">Loading…</div>;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="card p-6 lg:col-span-2">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="mono text-3xl font-bold text-white sm:text-4xl">{c.veh_hours_day.toLocaleString()}</div>
            <div className="mt-1 text-sm text-slate-400">vehicle-hours of delay / day</div>
          </div>
          <div>
            <div className="mono text-3xl font-bold text-gold sm:text-4xl">{inr(c.year.base)}</div>
            <div className="mt-1 text-sm text-slate-400">est. delay cost / year</div>
          </div>
          <div>
            <div className="mono text-3xl font-bold text-acc2 sm:text-4xl">{c.top20_share}%</div>
            <div className="mt-1 text-sm text-slate-400">of it in the worst 20 cells</div>
          </div>
        </div>
        <p className="mt-5 text-sm text-slate-300">
          Just <b>{c.cells_50} cells carry half</b> the estimated delay cost. Targeting them recovers most of
          the loss for a fraction of the patrol effort.
        </p>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          {["low", "base", "high"].map((k) => (
            <div key={k} className="rounded-lg bg-white/5 px-2 py-2">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">{k}</div>
              <div className="mono text-sm text-slate-200">{inr(c.day[k])}/day</div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[12px] leading-snug text-slate-500">
          A first-order estimate, not a measurement. With no live speed feed, we calibrate the physical
          delay-potential (obstruction × vehicle footprint × road utilization) into vehicle-hours, then rupees,
          and show a low/base/high band. The relative concentration is robust to the assumptions.
        </p>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-white">Costliest hotspots</h3>
        <div className="mt-3 space-y-1.5">
          {c.costliest.map((x, i) => (
            <div key={i} className="flex items-center justify-between gap-2 rounded-lg bg-white/5 px-3 py-2 text-sm">
              <div className="min-w-0">
                <div className="truncate font-medium text-white">{x.station}</div>
                <div className="truncate text-[11px] text-slate-400">{x.vi}</div>
              </div>
              <div className="mono shrink-0 text-gold">{inr(x.inr)}/d</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
