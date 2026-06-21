"""
web/prepare_data.py: export committed ParkPulse artifacts to compact JSON for the
Next.js app. Run from the repo root:  python web/prepare_data.py

Reads data/hex_scored.csv and outputs/*, and reuses
scripts/patrol_optimizer.py so the website matches the repo.
Writes web/public/data/*.json.
"""
from __future__ import annotations
import json, os, sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import patrol_optimizer as P  # noqa: E402
import congestion_cost as CC  # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "data")
os.makedirs(OUT, exist_ok=True)


def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), allow_nan=False)
    print(f"  {name:18s} {os.path.getsize(os.path.join(OUT, name))/1024:6.1f} KB")


def main():
    df = pd.read_csv("data/hex_scored.csv")
    cost = pd.read_csv("data/hex_cost.csv").set_index("h3_9")["cost_inr_day"].to_dict()
    trend = (pd.read_csv("data/hex_trend.csv").set_index("h3_9")["trend"].to_dict()
             if os.path.exists("data/hex_trend.csv") else {})
    osm = {}
    if os.path.exists("data/hex_osm.csv"):  # optional, from scripts/enrich_osm.py
        o = pd.read_csv("data/hex_osm.csv").set_index("h3_9")
        if "osm_context" in o.columns:
            osm = o["osm_context"].fillna("").to_dict()

    # --- hexes for the deck.gl H3HexagonLayer (compact keys) ---
    hexes = [{
        "h": r.h3_9,
        "s": round(float(r.impact_score), 1),
        "c": round(float(r.vol_pct) * 100, 1),         # raw-count percentile (toggle)
        "n": int(r.n_violations),
        "st": str(r.dom_station),
        "vi": str(r.dom_violation),
        "mh": int(r.modal_hour),
        "vp": round(float(r.vol_pct) * 100),
        "ip": round(float(r.intensity_pct) * 100),
        "ep": round(float(r.expo_pct) * 100),
        "pp": round(float(r.persist_pct) * 100),
        "co": round(float(cost.get(r.h3_9, 0))),       # est. delay cost, rupees/day
        "tr": trend.get(r.h3_9, ""),                   # rising / stable / cooling
        "os": osm.get(r.h3_9, ""),                     # OSM road + POI context (optional)
        "wy": str(r.why),
    } for r in df.itertuples(index=False)]
    dump("hexes.json", hexes)

    # --- top enforcement zones (where + when) ---
    z = pd.read_csv("outputs/top_zones.csv").head(30)

    def short_loc(t):
        return (str(t).split(", Bengaluru")[0])[:60] if isinstance(t, str) and t else "—"
    zones = [{
        "rank": int(r.impact_rank), "station": str(r.dom_station),
        "loc": short_loc(r.dom_location), "impact": round(float(r.impact_score), 1),
        "n": int(r.n_violations), "vi": str(r.dom_violation),
        "win": str(r.recommended_window), "pred": str(r.predictability),
        "why": str(r.why), "lat": float(r.lat), "lon": float(r.lon),
    } for r in z.itertuples(index=False)]
    dump("zones.json", zones)

    # --- Pareto + patrol optimizer (reuse the committed logic) ---
    pf = P.load()
    par = P.pareto(pf)
    s = par["sorted"]
    n = par["n"]
    frac = np.linspace(0, 1, 120)
    cum = s[P.VALUE].cumsum().values / par["total"]
    idx = np.clip((frac * n).astype(int) - 1, 0, n - 1)
    lorenz = [{"x": round(float(f), 4), "y": round(float(cum[i]), 4)} for f, i in zip(frac, idx)]

    NS = list(range(1, 51))
    greedy_at, naive_at = P.coverage_curve(pf, NS)
    plan = P.greedy_plan(pf, 50)
    info = pf.set_index("h3_9")
    beats = []
    for i, r in enumerate(plan.itertuples(index=False), 1):
        row = info.loc[r.h3_9]
        beats.append({
            "n": i, "station": str(row.dom_station),
            "loc": short_loc(row.get("dom_location", "")),
            "win": str(row.get("rec_window", "—")),
            "beat": round(100 * r.beat_impact / par["total"], 1),
            "greedy": round(100 * float(greedy_at[i - 1]), 1),
            "naive": round(100 * float(naive_at[i - 1]), 1),
        })
    dump("pareto.json", {
        "lorenz": lorenz,
        "topk": {str(k): round(100 * v, 1) for k, v in par["topk"].items()},
        "need": {str(int(p * 100)): int(v) for p, v in par["need"].items()},
        "n_cells": n, "beats": beats,
    })

    # --- forecaster: bake-off + ablation ---
    fm = pd.read_csv("outputs/forecast_metrics.csv", index_col=0)
    models = [{
        "model": idx, "cov20": round(float(r["cov@20"]), 3),
        "spearman": round(float(r.Spearman), 3), "dev": round(float(r.TweedieDev), 2),
        "is_model": idx in {"LightGBM (Tweedie)", "XGBoost (Tweedie)",
                            "CatBoost (Tweedie)", "HistGBM (Poisson)"},
    } for idx, r in fm.iterrows()]
    fjson = json.load(open("outputs/forecast_model.json"))
    ablation = [{"set": k, "cov20": round(float(v), 3)} for k, v in fjson["ablation_cov20"].items()]
    dump("forecast.json", {"models": models, "ablation": ablation,
                           "best": fjson["best_model"], "n_cells": fjson["n_cells"]})

    # --- congestion cost (vehicle-hours / rupees) ---
    cr = CC.report(df)
    b = cr["band"]
    dump("cost.json", {
        "veh_hours_day": round(b["base"]["veh_hours_day"]),
        "day": {k: round(b[k]["inr_day"]) for k in ("low", "base", "high")},
        "year": {k: round(b[k]["inr_year"]) for k in ("low", "base", "high")},
        "top20_share": round(cr["top20_share"] * 100), "cells_50": int(cr["cells_50"]),
        "costliest": [{"station": str(x.dom_station), "vi": str(x.dom_violation),
                       "vh": round(float(x.veh_hours_day), 1), "inr": round(float(x.cost_inr_day))}
                      for x in cr["ranked"].head(8).itertuples(index=False)],
    })

    # --- detection-validity model ---
    det = json.load(open("outputs/detection_metrics.json"))
    dump("detection.json", det)

    # --- emerging hotspots ---
    tr = pd.read_csv("data/hex_trend.csv")
    ec = tr["trend"].value_counts()
    hi = df["impact_score"].quantile(0.75)
    warn = tr[(tr.trend == "rising") & (tr.impact_score >= hi)].sort_values("impact_score", ascending=False)
    dump("emerging.json", {
        "rising": int(ec.get("rising", 0)), "stable": int(ec.get("stable", 0)),
        "cooling": int(ec.get("cooling", 0)), "support": int(len(tr)),
        "warn": [{"station": str(x.dom_station), "vi": str(x.dom_violation),
                  "impact": round(float(x.impact_score), 1),
                  "growth": round(float(x.rel_slope) * 100), "mom": round(float(x.momentum) * 100)}
                 for x in warn.head(12).itertuples(index=False)],
    })

    # --- headline KPIs ---
    dump("kpis.json", {
        "violations": 298445, "hotspots": int(n), "days": 151, "stations": 54,
        "top1_impact": float(par["topk"][10]) and round(100 * s[P.VALUE].head(max(int(0.01*n),1)).sum()/par["total"]),
        "cells_50": int(par["need"][0.5]),
        "beats20_greedy": round(100 * float(greedy_at[19]), 0),
        "beats20_naive": round(100 * float(naive_at[19]), 0),
        "spearman_impact_count": 0.56,
        "forecast_cov20": round(float(fm.loc[fjson["best_model"], "cov@20"]), 3),
        "face_valid": "20/20",
        "cost_day_base": round(b["base"]["inr_day"]),
        "cost_year_base": round(b["base"]["inr_year"]),
        "veh_hours_day": round(b["base"]["veh_hours_day"]),
        "top20_cost_share": round(cr["top20_share"] * 100),
        "detection_auc": round(det["roc_auc"], 3),
        "rising": int(ec.get("rising", 0)),
        "early_warning": int(len(warn)),
    })
    print("done -> web/public/data/")


if __name__ == "__main__":
    main()
