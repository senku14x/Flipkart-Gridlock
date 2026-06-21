"use client";
import { useEffect, useState } from "react";
import { ramp, rgb } from "../lib/colors";

export default function Zones() {
  const [z, setZ] = useState(null);
  useEffect(() => { fetch("/data/zones.json").then((r) => r.json()).then(setZ).catch(() => {}); }, []);

  return (
    <div className="card overflow-hidden">
      <div className="max-h-[560px] overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10 bg-panel/95 text-left text-[11px] uppercase tracking-wider text-slate-500 backdrop-blur">
            <tr>
              <th className="px-4 py-3 font-medium">#</th>
              <th className="py-3 font-medium">Zone</th>
              <th className="py-3 font-medium">Window</th>
              <th className="py-3 pr-4 text-right font-medium">Impact</th>
              <th className="hidden py-3 pr-4 text-right font-medium sm:table-cell">Violations</th>
            </tr>
          </thead>
          <tbody>
            {(z || []).map((r) => (
              <tr key={r.rank} className="border-t border-white/5 align-top hover:bg-white/[0.04]">
                <td className="mono px-4 py-3 text-slate-500">{r.rank}</td>
                <td className="py-3 pr-3">
                  <div className="font-medium text-white">{r.station}</div>
                  <div className="text-xs text-slate-400">{r.loc}</div>
                  <div className="mt-0.5 text-[11px] text-slate-500">{r.why}</div>
                </td>
                <td className="py-3 pr-3"><span className="mono rounded bg-acc2/10 px-1.5 py-0.5 text-[12px] text-acc2">{r.win}</span></td>
                <td className="py-3 pr-4 text-right"><span className="mono font-semibold" style={{ color: rgb(ramp(r.impact / 100)) }}>{r.impact}</span></td>
                <td className="mono hidden py-3 pr-4 text-right text-slate-300 sm:table-cell">{r.n.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
