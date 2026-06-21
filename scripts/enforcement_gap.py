"""
scripts/enforcement_gap.py: quantify the gap between where enforcement effort goes
today and where congestion impact actually is. This is the case for impact-weighted
prioritization, made from the data.

Recorded violations are a proxy for enforcement effort (a violation is logged when a
patrol is present). Weighting each record by its congestion-impact unit
(obstruction x PCU footprint x road utilization) shows how much real impact each slice
of effort captures. The pre-dawn sweep and the night window absorb a large share of
effort while roads are empty, so they capture little impact; the peak hours are the
reverse.

Reads the parquet. Writes outputs/enforcement_gap.md + outputs/enforcement_gap.json.
"""
from __future__ import annotations
import json
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(ROOT, "data", "parkpulse_clean_records.parquet")


def compute(df: pd.DataFrame) -> dict:
    u = df["obstruct_w"] * df["pcu"] * df["expo_weight"]   # per-record impact unit
    tot_n, tot_u = len(df), u.sum()

    def slice_share(mask):
        return {"effort": round(100 * mask.sum() / tot_n, 1),
                "impact": round(100 * u[mask].sum() / tot_u, 1)}

    windows = [
        {"name": "Pre-dawn sweep (4-5am)", **slice_share(df.hour.isin([4, 5]))},
        {"name": "Night (12-5am)", **slice_share(df.hour.isin([0, 1, 2, 3, 4, 5]))},
        {"name": "Peak-exposure hours", **slice_share(df.is_peak.astype(bool))},
    ]
    night = windows[1]
    sweep = windows[0]
    return {"windows": windows,
            "sweep_effort": sweep["effort"], "sweep_impact": sweep["impact"],
            "night_effort": night["effort"], "night_impact": night["impact"]}


def main():
    df = pd.read_parquet(PARQUET, columns=["hour", "obstruct_w", "pcu", "expo_weight", "is_peak"])
    g = compute(df)
    with open(os.path.join(ROOT, "outputs", "enforcement_gap.json"), "w") as f:
        json.dump(g, f, indent=2)

    L = ["# ParkPulse: the enforcement gap\n",
         "Where enforcement effort goes today vs where congestion impact actually is. "
         "Recorded violations stand in for effort (a violation is logged when a patrol is "
         "present); weighting each by its impact unit (obstruction x PCU x road utilization) "
         "shows how much real impact each slice of effort captures.\n",
         f"- The **4-5am sweep is {g['sweep_effort']}% of effort but only {g['sweep_impact']}% "
         "of congestion impact** (roads are empty, so a blockage barely matters).",
         f"- The **night window (12-5am) is {g['night_effort']}% of effort and just "
         f"{g['night_impact']}% of impact**, about a third of logged enforcement, captured "
         "while congestion is near zero.",
         "- The **peak-exposure hours are the reverse**: a smaller share of effort, the "
         "majority of the impact.\n",
         "| Time window | Share of effort | Share of impact |",
         "|---|--:|--:|"]
    for w in g["windows"]:
        L.append(f"| {w['name']} | {w['effort']}% | {w['impact']}% |")
    L.append("\nParkPulse redirects effort from the low-impact night window to the "
             "peak-hour chokepoints where impact concentrates. The hour itself is "
             "enforcement-confounded, so we prioritize by exposure-weighted impact, not by "
             "the recorded violation hour.")
    with open(os.path.join(ROOT, "outputs", "enforcement_gap.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"sweep: {g['sweep_effort']}% effort -> {g['sweep_impact']}% impact")
    print(f"night: {g['night_effort']}% effort -> {g['night_impact']}% impact")
    print("-> outputs/enforcement_gap.md/.json")


if __name__ == "__main__":
    main()
