"use client";
import { useEffect, useState } from "react";

export default function Detection() {
  const [d, setD] = useState(null);
  useEffect(() => { fetch("/data/detection.json").then((r) => r.json()).then(setD).catch(() => {}); }, []);
  if (!d) return <div className="card grid h-72 place-items-center text-slate-500">Loading…</div>;
  const t20 = d.triage.find((t) => t.flag_pct === 20) || d.triage[1];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card p-5">
        <h3 className="font-semibold text-white">Predicting which reports are false</h3>
        <p className="mt-1 text-xs text-slate-400">
          A second supervised model, separate from the forecaster, trained on {d.n_train.toLocaleString()} reviewed
          reports with a stratified hold-out. Real labels, real structure (not a base rate).
        </p>
        <div className="mt-4 grid grid-cols-3 gap-3 text-center">
          <div className="rounded-lg bg-white/5 py-3"><div className="mono text-2xl font-bold text-accent">{d.roc_auc.toFixed(3)}</div><div className="text-[11px] text-slate-400">ROC-AUC</div></div>
          <div className="rounded-lg bg-white/5 py-3"><div className="mono text-2xl font-bold text-white">{d.pr_auc.toFixed(3)}</div><div className="text-[11px] text-slate-400">PR-AUC</div></div>
          <div className="rounded-lg bg-white/5 py-3"><div className="mono text-2xl font-bold text-slate-300">{(d.base_rate * 100).toFixed(0)}%</div><div className="text-[11px] text-slate-400">base rate</div></div>
        </div>
        <div className="mt-4 rounded-lg border border-accent/30 bg-accent/10 p-3 text-sm text-slate-200">
          Flag the <b>top {t20.flag_pct}%</b> most-suspect reports and you catch <b>{(t20.recall * 100).toFixed(0)}%</b> of
          all rejections at <b>{(t20.precision * 100).toFixed(0)}%</b> precision. Patrols stop chasing ghosts.
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-white">Triage lift</h3>
        <table className="mt-3 w-full text-sm">
          <thead className="text-left text-[11px] uppercase tracking-wide text-slate-500">
            <tr><th className="py-2 font-medium">Flag top</th><th className="py-2 text-right font-medium">Precision</th><th className="py-2 text-right font-medium">Recall</th><th className="py-2 text-right font-medium">Lift</th></tr>
          </thead>
          <tbody>
            {d.triage.map((t, i) => (
              <tr key={i} className="border-t border-white/5">
                <td className="py-2 text-slate-300">{t.flag_pct}% most-suspect</td>
                <td className="mono py-2 text-right text-white">{(t.precision * 100).toFixed(0)}%</td>
                <td className="mono py-2 text-right text-acc2">{(t.recall * 100).toFixed(0)}%</td>
                <td className="mono py-2 text-right text-slate-400">{t.lift.toFixed(1)}×</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-3 text-[12px] leading-snug text-slate-500">
          Top signals: {d.top_features.slice(0, 5).map((f) => f.f).join(", ")}. Location dominates — some areas
          generate far more contested reports than others.
        </div>
      </div>
    </div>
  );
}
