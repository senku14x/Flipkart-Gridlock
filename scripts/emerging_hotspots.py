"""
scripts/emerging_hotspots.py: find hotspots that are escalating, not just chronically
bad. The impact score ranks where things are bad on average; this flags where they are
getting worse, so enforcement can act before a spot becomes entrenched.

Method: monthly counts on the four full months (Dec-Mar; Nov and Apr are partial). To
avoid reading the citywide enforcement ramp as per-cell growth, we track each cell's
SHARE of citywide volume each month and fit a trend to the share. A rising share means
the cell is growing faster than the city. Min support: >=40 violations over the window
and active in >=3 of the 4 months.

Honest caveat: a rising trend in recorded violations can reflect shifting enforcement
focus as well as real demand; treat it as "rising enforcement-relevant activity."

Reads the parquet + data/hex_scored.csv. Writes outputs/emerging_hotspots.md, data/hex_trend.csv.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(ROOT, "data", "parkpulse_clean_records.parquet")
SCORED = os.path.join(ROOT, "data", "hex_scored.csv")
RISE, COOL = 0.10, -0.10   # fractional change in citywide share per month


def main():
    rec = pd.read_parquet(PARQUET, columns=["h3_9", "month"])
    months = sorted(rec["month"].unique())
    full = months[1:-1]                      # drop the two partial months
    rec = rec[rec.month.isin(full)]
    cnt = rec.groupby(["h3_9", "month"]).size().unstack(fill_value=0)[full]
    city = cnt.sum(axis=0)                    # citywide total per month
    share = cnt.div(city, axis=1)            # each cell's share of the city, per month

    support = (cnt.sum(axis=1) >= 40) & ((cnt > 0).sum(axis=1) >= 3)
    x = np.arange(len(full))
    rows = []
    for h in cnt.index[support]:
        sh = share.loc[h].values
        slope = np.polyfit(x, sh, 1)[0]
        mean = sh.mean()
        rel = slope / mean if mean > 0 else 0.0          # fractional share change / month
        momentum = sh[-1] / mean - 1 if mean > 0 else 0.0
        cls = "rising" if rel > RISE else "cooling" if rel < COOL else "stable"
        rows.append((h, rel, momentum, cls, int(cnt.loc[h].sum())))
    trend = pd.DataFrame(rows, columns=["h3_9", "rel_slope", "momentum", "trend", "n_full"])

    sc = pd.read_csv(SCORED)[["h3_9", "impact_score", "impact_rank", "dom_station",
                              "dom_violation", "lat", "lon"]]
    t = trend.merge(sc, on="h3_9", how="left")
    t.to_csv(os.path.join(ROOT, "data", "hex_trend.csv"), index=False)

    counts = t["trend"].value_counts()
    rising = t[t.trend == "rising"].sort_values("impact_score", ascending=False)
    # early-warning = rising AND already high impact (top quartile of scored cells)
    hi = sc["impact_score"].quantile(0.75)
    warn = rising[rising.impact_score >= hi].head(12)

    L = ["# ParkPulse: emerging hotspots\n",
         f"Trend of each cell's share of citywide volume across the four full months "
         f"({full[0]} to {full[-1]}), so the citywide enforcement ramp is not mistaken for "
         "local growth. Min support: 40+ violations and active in 3+ months "
         f"({int(support.sum())} cells qualify).\n",
         f"- **{int(counts.get('rising',0))} rising**, {int(counts.get('stable',0))} stable, "
         f"{int(counts.get('cooling',0))} cooling.",
         f"- Of the rising cells, **{len(rising[rising.impact_score>=hi])} are already high-impact** "
         "(top quartile): these are the early-warning priorities, bad and getting worse.\n",
         "## Early-warning hotspots (high impact and rising)\n",
         "| Station | Violation | Impact | Share growth/mo | Latest vs avg |",
         "|---|---|--:|--:|--:|"]
    for r in warn.itertuples(index=False):
        L.append(f"| {r.dom_station} | {r.dom_violation} | {r.impact_score:.0f} | "
                 f"+{r.rel_slope*100:.0f}% | {r.momentum*100:+.0f}% |")
    L.append("\n## Caveat\n")
    L.append("Recorded-violation trends can reflect changing enforcement focus, not only "
             "parking demand. Read these as where enforcement-relevant activity is rising.")
    with open(os.path.join(ROOT, "outputs", "emerging_hotspots.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"support cells: {int(support.sum())} | rising {int(counts.get('rising',0))}, "
          f"stable {int(counts.get('stable',0))}, cooling {int(counts.get('cooling',0))}")
    print(f"high-impact AND rising (early-warning): {len(rising[rising.impact_score>=hi])}")
    print("top rising chokepoints:", list(warn["dom_station"].head(5)))
    print("-> outputs/emerging_hotspots.md, data/hex_trend.csv")


if __name__ == "__main__":
    main()
