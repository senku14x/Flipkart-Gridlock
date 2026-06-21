"""
patrol_optimizer.py — ParkPulse Step 5: patrol optimizer + Pareto
================================================================================
Turns the Congestion Impact Score into a deployment plan: given N patrol units,
*where* (and *when*) to send them to relieve the most parking-induced congestion
per patrol-hour.

Two parts:
  1. PARETO — parking-congestion impact is extremely concentrated, so a few
     locations carry most of it. We quantify it on `impact_sum` (the EXPOSURE-
     WEIGHTED additive impact mass: Σ obstruction×PCU×exposure — so the 4–5am
     enforcement-sweep mass barely counts; CLAUDE.md §6.6).
  2. OPTIMIZER — greedy max-coverage. Each patrol works a ~beat (its cell + the
     immediate H3 ring), and we pick beats to maximise the UNION of impact
     covered. Because the worst cells clump together, this beats a naive "top-N
     cells" pick, which would stack units in one cluster. Each beat carries an
     exposure-weighted enforcement WINDOW (from rank_zones), so the plan is
     where + when.

Optional: a forecaster-driven NEXT-DAY plan (predicted violations × impact per
violation) — the project's "reactive → predictive" thesis in one table.

Inputs : data/hex_scored.csv, outputs/zone_enrichment.csv
         (optional) outputs/forecast_model.pkl + scripts/forecast.py
Outputs: outputs/patrol_plan.md, outputs/patrol_plan.csv, outputs/pareto.png
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

import h3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style import ACC, ACC2, GRN, INK, plt  # noqa: E402

SCORED = "data/hex_scored.csv"
ENRICH = "outputs/zone_enrichment.csv"
VALUE = "impact_sum"           # exposure-weighted additive impact mass
RADIUS = 1                     # a patrol beat = cell + H3 ring-1 (~400 m)
PLAN_UNITS = 20
CANDIDATE_POOL = 300           # greedy searches over the top-N cells (others never win)
CURVE_NS = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60]


# --- data ---------------------------------------------------------------------
def load() -> pd.DataFrame:
    df = pd.read_csv(SCORED)
    if os.path.exists(ENRICH):
        enr = pd.read_csv(ENRICH)[["h3_9", "rec_window", "dom_location", "window_capture"]]
        df = df.merge(enr, on="h3_9", how="left")
    else:
        df["rec_window"], df["dom_location"] = "—", ""
    return df


# --- pareto -------------------------------------------------------------------
def pareto(df: pd.DataFrame) -> dict:
    s = df.sort_values(VALUE, ascending=False).reset_index(drop=True)
    tot = s[VALUE].sum()
    cum = s[VALUE].cumsum() / tot
    topk = {k: float(s[VALUE].head(k).sum() / tot) for k in (10, 20, 30, 50, 100)}
    need = {p: int((cum < p).sum() + 1) for p in (0.5, 0.8, 0.9)}
    return {"sorted": s, "total": tot, "cum": cum, "topk": topk, "need": need, "n": len(s)}


# --- greedy max-coverage optimizer -------------------------------------------
def _cover_sets(impact: dict, cells, radius: int) -> dict:
    return {c: [nb for nb in h3.grid_disk(c, radius) if nb in impact] for c in cells}


def greedy_plan(df: pd.DataFrame, n_units: int, radius: int = RADIUS,
                pool: int = CANDIDATE_POOL) -> pd.DataFrame:
    impact = dict(zip(df.h3_9, df[VALUE]))
    total = sum(impact.values())
    cand = df.nlargest(pool, VALUE).h3_9.tolist()
    cov = _cover_sets(impact, cand, radius)
    covered: set = set()
    chosen: set = set()
    rows, cum = [], 0.0
    for _ in range(n_units):
        best, best_gain, best_new = None, -1.0, None
        for c in cand:
            if c in chosen:
                continue
            new = [nb for nb in cov[c] if nb not in covered]
            gain = sum(impact[nb] for nb in new)
            if gain > best_gain:
                best, best_gain, best_new = c, gain, new
        if best is None or best_gain <= 0:
            break
        chosen.add(best)
        covered.update(best_new)
        cum += best_gain
        rows.append({"h3_9": best, "beat_impact": best_gain,
                     "beat_cells": len(cov[best]), "cum_cov": cum / total})
    return pd.DataFrame(rows)


def coverage_curve(df: pd.DataFrame, ns, radius: int = RADIUS):
    """Greedy vs naive top-N coverage, for the diminishing-returns chart."""
    impact = dict(zip(df.h3_9, df[VALUE]))
    total = sum(impact.values())
    ranked = df.sort_values(VALUE, ascending=False).h3_9.tolist()[:max(ns)]
    cov = _cover_sets(impact, ranked, radius)
    greedy = greedy_plan(df, max(ns), radius)["cum_cov"].tolist()
    greedy_at = [greedy[min(n, len(greedy)) - 1] for n in ns]
    naive_at = []
    for n in ns:
        u: set = set()
        for c in ranked[:n]:
            u.update(cov[c])
        naive_at.append(sum(impact[x] for x in u) / total)
    return greedy_at, naive_at


# --- optional: forecaster-driven next-day plan -------------------------------
def forecast_plan(df: pd.DataFrame, n_units: int = PLAN_UNITS, radius: int = RADIUS):
    """Greedy plan on predicted next-day impact = pred_violations × impact/violation."""
    import joblib
    import forecast as F
    panel = F.build_panel()
    _, _, te = F.temporal_split(panel)
    model = joblib.load("outputs/forecast_model.pkl")
    date = te.date.max()
    day = te[te.date == date].copy()
    day["pred"] = np.clip(model.predict(day[F.FEATURES]), 0, None)
    ipv = df.set_index("h3_9")["impact_per_violation"]
    day["dyn_value"] = day["pred"] * day.h3_9.map(ipv).fillna(ipv.median())
    dyn = day.rename(columns={"dyn_value": VALUE})[["h3_9", VALUE]]
    plan = greedy_plan(dyn, n_units, radius, pool=min(CANDIDATE_POOL, len(dyn)))
    return date, plan


# --- reporting ----------------------------------------------------------------
def make_figure(par: dict, ns, greedy_at, naive_at, path: str):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.3))
    s, n = par["sorted"], par["n"]
    x = np.arange(1, n + 1) / n
    ax1.plot(x, par["cum"].values, color=ACC, lw=2.2)
    ax1.fill_between(x, par["cum"].values, color=ACC, alpha=0.12)
    for frac in (0.01, 0.05, 0.10):
        k = max(int(frac * n), 1)
        cov = s[VALUE].head(k).sum() / par["total"]
        ax1.plot([frac], [cov], "o", color=INK)
        ax1.annotate(f"top {int(frac*100)}% → {cov*100:.0f}%", (frac, cov),
                     textcoords="offset points", xytext=(8, -4), fontsize=8)
    ax1.set_xlabel("share of hotspot cells (ranked by impact)")
    ax1.set_ylabel("cumulative share of total impact")
    ax1.set_title("Parking-congestion impact is concentrated\n(Pareto on exposure-weighted impact)")
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)

    ax2.plot(ns, np.array(greedy_at) * 100, "-o", color=GRN, lw=2.3, ms=5,
             label="greedy max-coverage (spreads beats)")
    ax2.plot(ns, np.array(naive_at) * 100, "--s", color=ACC2, lw=1.8, ms=4,
             label="naive top-N cells (clumps)")
    ax2.set_xlabel("patrol beats deployed (N)")
    ax2.set_ylabel("% of citywide impact covered")
    ax2.set_title("Patrol coverage vs. fleet size\n(each beat = cell + immediate ring)")
    ax2.legend(fontsize=8, loc="lower right")
    fig.suptitle("ParkPulse — patrol optimizer & Pareto", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _short_loc(t):
    return (str(t).split(", Bengaluru")[0])[:42] if isinstance(t, str) and t else "—"


def write_markdown(df, par, plan, ns, greedy_at, naive_at, fc, path):
    g20 = plan.cum_cov.iloc[-1]
    naive20 = naive_at[ns.index(PLAN_UNITS)] if PLAN_UNITS in ns else naive_at[-1]
    info = df.set_index("h3_9")
    L = [
        "# ParkPulse — Patrol Optimizer & Pareto", "",
        "From impact score to deployment: where (and when) to send a limited patrol fleet for the "
        "most congestion relief per patrol-hour. Coverage is measured on **`impact_sum`** — the "
        "exposure-weighted additive impact mass, so the 4–5am enforcement sweep barely counts.", "",
        "## 1. The Pareto — a few streets carry most of the problem", "",
        f"Across **{par['n']} hotspot cells**:", "",
        "| Patrol target | Cells | Share of cells | Impact covered |",
        "|---|--:|--:|--:|",
    ]
    for k in (10, 20, 30, 50, 100):
        L.append(f"| top {k} | {k} | {100*k/par['n']:.1f}% | **{100*par['topk'][k]:.0f}%** |")
    L += [
        "",
        f"It takes only **{par['need'][0.5]} cells ({100*par['need'][0.5]/par['n']:.1f}%)** to cover "
        f"half the city's parking-congestion impact, and {par['need'][0.8]} to cover 80%. *This is "
        f"the prioritisation thesis: don't patrol everywhere — patrol these.*", "",
        "## 2. The optimizer — greedy beats naive", "",
        "Each patrol works a **beat** (its cell + the immediate ring). Because the worst cells "
        "cluster in the same commercial cores, **greedy max-coverage spreads beats across distinct "
        "hotspots** and covers more than naively taking the top-N cells (which stack up in one "
        "cluster):", "",
        f"- **{PLAN_UNITS} greedy beats cover {100*g20:.0f}%** of citywide impact "
        f"vs {100*naive20:.0f}% for naive top-{PLAN_UNITS} — "
        f"**+{round(100*g20)-round(100*naive20)} pts** for the same fleet.",
        f"- Diminishing returns: 10 beats → {100*greedy_at[ns.index(10)]:.0f}%, "
        f"30 → {100*greedy_at[ns.index(30)]:.0f}%, 50 → {100*greedy_at[ns.index(50)]:.0f}%.",
        "",
        f"### Recommended deployment — {PLAN_UNITS} patrol beats", "",
        "| # | Station | Location | Window (IST) | Beat impact | Cumulative |",
        "|--:|---|---|---|--:|--:|",
    ]
    for i, r in enumerate(plan.itertuples(index=False), 1):
        row = info.loc[r.h3_9]
        L.append(f"| {i} | {row.dom_station} | {_short_loc(row.get('dom_location'))} | "
                 f"{row.get('rec_window', '—')} | {100*r.beat_impact/par['total']:.1f}% | "
                 f"{100*r.cum_cov:.0f}% |")
    L += [
        "",
        "*(Full machine-readable plan: `outputs/patrol_plan.csv`.)*", "",
    ]
    if fc is not None:
        date, fplan = fc
        static_top = set(plan.h3_9)
        dyn_top = set(fplan.h3_9)
        overlap = len(static_top & dyn_top)
        L += [
            f"## 3. Predictive deployment — plan for {date.date()} (forecaster-driven)", "",
            "Feeding the forecaster's predicted next-day violations (× impact per violation) into the "
            "same optimizer yields a **dynamic** plan that re-targets where impact will be *tomorrow*, "
            f"not just chronically. It shares **{overlap}/{PLAN_UNITS}** beats with the static plan — "
            "the stable cores — and reallocates the rest to predicted surges. This is the "
            "reactive→predictive thesis in one table.", "",
            "| # | Station | Location | Window (IST) | Pred. next-day impact |",
            "|--:|---|---|---|--:|",
        ]
        ip_tot = fplan.beat_impact.sum()
        for i, r in enumerate(fplan.itertuples(index=False), 1):
            row = info.loc[r.h3_9] if r.h3_9 in info.index else None
            st = row.dom_station if row is not None else "—"
            loc = _short_loc(row.get("dom_location")) if row is not None else "—"
            win = row.get("rec_window", "—") if row is not None else "—"
            L.append(f"| {i} | {st} | {loc} | {win} | {100*r.beat_impact/ip_tot:.1f}% |")
        L.append("")
    L += [
        "---",
        "*`scripts/patrol_optimizer.py`. Impact is a transparent engineered index — no traffic-flow "
        "ground truth (CLAUDE.md §7); the beat radius is a modelling assumption. Windows are "
        "exposure-weighted, not raw modal hour.*", "",
    ]
    open(path, "w", encoding="utf-8").write("\n".join(L))


def main() -> None:
    os.makedirs("outputs", exist_ok=True)
    df = load()
    par = pareto(df)
    plan = greedy_plan(df, PLAN_UNITS)
    greedy_at, naive_at = coverage_curve(df, CURVE_NS)

    # machine-readable plan
    out = plan.merge(df[["h3_9", "dom_station", "dom_location", "rec_window", "impact_score",
                         "n_violations", "dom_violation", "why", "lat", "lon"]], on="h3_9", how="left")
    out.insert(0, "unit", range(1, len(out) + 1))
    out.to_csv("outputs/patrol_plan.csv", index=False)

    fc = None
    try:
        if os.path.exists("outputs/forecast_model.pkl"):
            print("Building forecaster-driven next-day plan…")
            fc = forecast_plan(df)
    except Exception as e:  # never let the bonus break the core deliverable
        print(f"  (skipped forecast plan: {type(e).__name__}: {e})")

    make_figure(par, CURVE_NS, greedy_at, naive_at, "outputs/pareto.png")
    write_markdown(df, par, plan, CURVE_NS, greedy_at, naive_at, fc, "outputs/patrol_plan.md")

    print(f"\nPareto: top 20 cells cover {100*par['topk'][20]:.0f}% of impact; "
          f"{par['need'][0.8]} cells cover 80%.")
    print(f"Optimizer: {PLAN_UNITS} greedy beats cover {100*plan.cum_cov.iloc[-1]:.0f}% "
          f"(naive top-{PLAN_UNITS}: {100*naive_at[CURVE_NS.index(PLAN_UNITS)]:.0f}%).")
    print("Saved -> outputs/patrol_plan.md, outputs/patrol_plan.csv, outputs/pareto.png")


if __name__ == "__main__":
    main()
