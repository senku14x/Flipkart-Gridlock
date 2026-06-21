"""
scripts/congestion_cost.py: translate the Congestion Impact Score into an estimated
delay cost (vehicle-hours and rupees), so the prioritization has a business number.

This is a transparent, first-order estimate, not a measurement. We never observe
real delay (no flow feed), so we calibrate the physical delay-potential we DO have:
impact_sum = sum over a cell's violations of (obstruction x PCU footprint x road
utilization). Each unit is mapped to vehicle-hours of delay, then to rupees via a
value-of-time. We report a low/base/high band and lead with the relative result
(the share of cost in the worst cells), which is robust to the absolute calibration.

Reads data/hex_scored.csv. Writes outputs/congestion_cost.md and data/hex_cost.csv.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORED = os.path.join(ROOT, "data", "hex_scored.csv")
DAYS = 151  # observation window (2023-11-10 -> 2024-04-08)

# --- assumptions (varied for the sensitivity band) ---
# vehicle-hours of cumulative delay per unit of (obstruction x PCU x utilization)
# per violation. A median violation is ~0.32 units (-> ~0.32 veh-hr of queueing);
# a severe one ~3.5 units (-> a few veh-hr). Base 1.0, varied 2x either way.
VH_PER_UNIT = {"low": 0.5, "base": 1.0, "high": 2.0}
# value of time (rupees / vehicle-hour): fuel waste + time, blended across vehicle
# classes for an Indian metro. Base Rs 250/hr.
VOT = {"low": 150, "base": 250, "high": 400}


def compute(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # daily delay-potential per cell (calendar-day average over the window)
    out["delay_units_day"] = out["impact_sum"] / DAYS
    out["veh_hours_day"] = out["delay_units_day"] * VH_PER_UNIT["base"]
    out["cost_inr_day"] = out["veh_hours_day"] * VOT["base"]
    return out


def band(total_units_day: float):
    rows = {}
    for k in ("low", "base", "high"):
        vh = total_units_day * VH_PER_UNIT[k]
        rows[k] = {"veh_hours_day": vh, "inr_day": vh * VOT[k], "inr_year": vh * VOT[k] * 365}
    return rows


def report(df: pd.DataFrame) -> dict:
    c = compute(df)
    total_units_day = c["delay_units_day"].sum()
    b = band(total_units_day)
    ranked = c.sort_values("cost_inr_day", ascending=False).reset_index(drop=True)
    top20_share = ranked["cost_inr_day"].head(20).sum() / ranked["cost_inr_day"].sum()
    # cells covering 50% of the cost
    cum = ranked["cost_inr_day"].cumsum() / ranked["cost_inr_day"].sum()
    cells_50 = int((cum < 0.5).sum() + 1)
    return {"c": c, "ranked": ranked, "band": b, "total_units_day": total_units_day,
            "top20_share": top20_share, "cells_50": cells_50}


def inr(x):
    if x >= 1e7:
        return f"Rs {x/1e7:.2f} crore"
    if x >= 1e5:
        return f"Rs {x/1e5:.1f} lakh"
    return f"Rs {x:,.0f}"


def write_md(r: dict, path: str):
    b = r["band"]
    rk = r["ranked"]
    L = []
    L.append("# ParkPulse: estimated congestion cost\n")
    L.append("A first-order estimate, not a measurement. The data has no traffic-flow "
             "feed, so we cannot observe delay directly. Instead we calibrate the physical "
             "delay-potential the data does contain (`impact_sum` = the sum over each cell's "
             "violations of obstruction x PCU footprint x road utilization) into vehicle-hours, "
             "then into rupees via a value-of-time. We report a low/base/high band and lead "
             "with the relative concentration, which does not depend on the absolute calibration.\n")

    L.append("## Headline (base case)\n")
    L.append(f"- Recorded parking violations at these {len(rk):,} hotspots cause an estimated "
             f"**{b['base']['veh_hours_day']:,.0f} vehicle-hours of delay per day**.")
    L.append(f"- At a blended value of time, that is about **{inr(b['base']['inr_day'])}/day** "
             f"(**{inr(b['base']['inr_year'])}/year**).")
    L.append(f"- The worst **20 cells alone carry {r['top20_share']*100:.0f}%** of that cost "
             f"(~{inr(rk['cost_inr_day'].head(20).sum())}/day); just **{r['cells_50']} cells "
             f"account for half**. Enforcement that targets them recovers most of the delay "
             f"for a fraction of the effort.\n")

    L.append("## Sensitivity band\n")
    L.append("| Scenario | veh-hr/unit | Rs/veh-hr | Delay (veh-hr/day) | Cost/day | Cost/year |")
    L.append("|---|--:|--:|--:|--:|--:|")
    for k in ("low", "base", "high"):
        L.append(f"| {k} | {VH_PER_UNIT[k]} | {VOT[k]} | {b[k]['veh_hours_day']:,.0f} | "
                 f"{inr(b[k]['inr_day'])} | {inr(b[k]['inr_year'])} |")
    L.append("")

    L.append("## Assumptions\n")
    L.append("- **Delay-potential** per violation = obstruction weight (0.5-1.0) x PCU footprint "
             "(0.5-3.5) x road utilization (0.1-1.0); summed per cell as `impact_sum`, averaged "
             f"over the {DAYS}-day window for a per-day figure.")
    L.append("- **veh-hours per unit**: a median violation is ~0.32 units (about 0.32 veh-hr of "
             "queueing delay); a severe one ~3.5 units. Base 1.0, varied 0.5-2.0.")
    L.append("- **Value of time**: time plus fuel waste, blended across vehicle classes; base "
             "Rs 250/veh-hr, varied 150-400.")
    L.append("- Linear in utilization (a simplification: real queueing is convex near capacity, "
             "so this is conservative for the busiest roads). Covers only recorded violations, "
             "which are enforcement-limited, so the true figure is higher.\n")

    L.append("## Costliest 15 hotspots (base case)\n")
    L.append("| # | Station | Violation | Impact | Est. delay (veh-hr/day) | Est. cost/day |")
    L.append("|--:|---|---|--:|--:|--:|")
    for i, row in enumerate(rk.head(15).itertuples(index=False), 1):
        L.append(f"| {i} | {row.dom_station} | {row.dom_violation} | {row.impact_score:.0f} | "
                 f"{row.veh_hours_day:,.1f} | {inr(row.cost_inr_day)} |")
    L.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    df = pd.read_csv(SCORED)
    r = report(df)
    # persist per-cell cost for the web + downstream
    keep = ["h3_9", "dom_station", "dom_violation", "impact_score",
            "veh_hours_day", "cost_inr_day"]
    r["c"][keep].to_csv(os.path.join(ROOT, "data", "hex_cost.csv"), index=False)
    write_md(r, os.path.join(ROOT, "outputs", "congestion_cost.md"))

    b = r["band"]
    print(f"Citywide delay (base): {b['base']['veh_hours_day']:,.0f} veh-hr/day")
    print(f"Cost: {inr(b['base']['inr_day'])}/day  ({inr(b['low']['inr_day'])}-{inr(b['high']['inr_day'])})")
    print(f"Annual (base): {inr(b['base']['inr_year'])}")
    print(f"Top-20 cost share: {r['top20_share']*100:.1f}%  |  50% of cost in {r['cells_50']} cells")
    print("-> outputs/congestion_cost.md, data/hex_cost.csv")


if __name__ == "__main__":
    main()
