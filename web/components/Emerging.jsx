"use client";
import { useEffect, useState } from "react";
import { ramp, rgb } from "../lib/colors";

function Bar({ label, v, tot, color }) {
  const pct = tot ? Math.round((100 * v) / tot) : 0;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-16 text-slate-300">{label}</span>
      <div className="h-2 flex-1 rounded-full bg-white/10">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="mono w-8 text-right text-slate-400">{v}</span>
    </div>
  );
}

export default function Emerging() {
  const [e, setE] = useState(null);
  useEffect(() => { fetch("/data/emerging.json").then((r) => r.json()).then(setE).catch(() => {}); }, []);
  if (!e) return <div className="card grid h-72 place-items-center text-slate-500">Loading…</div>;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="card p-5">
        <h3 className="font-semibold text-white">Trend across {e.support} cells</h3>
        <div className="mt-3 space-y-2">
          <Bar label="Rising" v={e.rising} tot={e.support} color="#e4572e" />
          <Bar label="Stable" v={e.stable} tot={e.support} color="#64748b" />
          <Bar label="Cooling" v={e.cooling} tot={e.support} color="#36b3a8" />
        </div>
        <p className="mt-4 text-[12px] leading-snug text-slate-500">
          We trend each cell&apos;s share of citywide volume across the four full months, so the citywide
          enforcement ramp isn&apos;t read as local growth. A rising share means the cell is growing faster than
          the city. Recorded-violation trends can reflect shifting enforcement focus too, so read these as rising
          enforcement-relevant activity.
        </p>
      </div>

      <div className="card p-5 lg:col-span-2">
        <div className="flex items-baseline justify-between">
          <h3 className="font-semibold text-white">Early warning: high-impact and rising</h3>
          <span className="text-xs text-slate-500">bad, and getting worse</span>
        </div>
        <div className="mt-3 grid gap-1.5 sm:grid-cols-2">
          {e.warn.map((w, i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2">
              <span className="h-6 w-1 shrink-0 rounded-full bg-accent" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-white">{w.station}</div>
                <div className="truncate text-[11px] text-slate-400">{w.vi}</div>
              </div>
              <div className="text-right">
                <div className="mono text-sm font-semibold" style={{ color: rgb(ramp(w.impact / 100)) }}>{w.impact}</div>
                <div className="mono text-[11px] text-accent">+{w.growth}%/mo</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
