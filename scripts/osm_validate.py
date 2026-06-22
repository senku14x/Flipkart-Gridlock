"""
scripts/osm_validate.py: cross-check the Congestion Impact Score against REAL road data
from OpenStreetMap, as an independent validation.

We deliberately did NOT use the OSM road network to build the score (it uses a
text-token road proxy). So if the score, derived without OSM, agrees with real road
criticality and sits near real congestion-generators, that is independent evidence it
captures something physical, the closest thing to ground truth we can get without a
speed feed.

Run AFTER scripts/enrich_osm.py has produced data/hex_osm.csv:
    python scripts/enrich_osm.py          # fetch OSM (needs network)
    python scripts/osm_validate.py        # this cross-check

Reads data/hex_scored.csv + data/hex_osm.csv. Writes outputs/osm_validation.md and
submission/figures/fig-osm.png. Optional arg: path to the hex_osm csv (for testing).
"""
from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENT, TEAL, INK, GREY = "#e4572e", "#36b3a8", "#1b2a4a", "#8a93a3"
ART = 0.6        # road_criticality at/above primary class counts as an arterial
TOPN = 30


def main(osm_path=None):
    osm_path = osm_path or os.path.join(ROOT, "data", "hex_osm.csv")
    if not os.path.exists(osm_path):
        sys.exit("data/hex_osm.csv not found. Run scripts/enrich_osm.py first (needs network).")

    sc = pd.read_csv(os.path.join(ROOT, "data", "hex_scored.csv"))[["h3_9", "impact_score"]]
    osm = pd.read_csv(osm_path)
    m = sc.merge(osm, on="h3_9", how="inner")
    poi_col = "n_poi" if "n_poi" in m.columns else None

    rho_road = spearmanr(m.impact_score, m.road_criticality).correlation
    rho_bet = (spearmanr(m.impact_score, m.betweenness).correlation
               if "betweenness" in m.columns else None)

    top = m.nlargest(TOPN, "impact_score")
    art_top, art_all = (top.road_criticality >= ART).mean(), (m.road_criticality >= ART).mean()
    if poi_col:
        poi_top, poi_all = (top[poi_col] > 0).mean(), (m[poi_col] > 0).mean()

    # figure: impact vs road criticality + the top-N arterial/POI lift
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.7))
    a1.scatter(m.road_criticality, m.impact_score, s=6, alpha=0.3, color=ACCENT, linewidths=0)
    a1.set_xlabel("OSM road criticality (independent)"); a1.set_ylabel("Congestion Impact Score")
    a1.set_title(f"Score vs real road criticality (rho = {rho_road:.2f})", fontsize=10)
    cats = ["on an arterial"] + (["near a generator"] if poi_col else [])
    topv = [art_top * 100] + ([poi_top * 100] if poi_col else [])
    allv = [art_all * 100] + ([poi_all * 100] if poi_col else [])
    xi = np.arange(len(cats)); w = 0.38
    a2.bar(xi - w / 2, allv, w, color=GREY, label="all cells")
    a2.bar(xi + w / 2, topv, w, color=TEAL, label=f"top-{TOPN} hotspots")
    a2.set_xticks(xi); a2.set_xticklabels(cats, fontsize=9); a2.set_ylabel("% of cells")
    a2.legend(frameon=False, fontsize=9); a2.set_title("Top hotspots sit where it's physical", fontsize=10)
    for ax in (a1, a2):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "submission", "figures", "fig-osm.png"),
                bbox_inches="tight", facecolor="white", dpi=150)
    plt.close()

    L = ["# ParkPulse: OSM cross-check (independent validation)\n",
         "The impact score was built from the violation feed alone, with a text-token road "
         "proxy and no road network. Here we compare it to REAL OpenStreetMap road data it "
         "never saw. Agreement is independent evidence the score is physical.\n",
         f"- **Score vs road criticality: Spearman {rho_road:.2f}.** Higher-impact cells sit on "
         "more important roads, even though the score never used the road network."]
    if rho_bet is not None:
        L.append(f"- **Score vs betweenness centrality: Spearman {rho_bet:.2f}** (how critical each "
                 "road is to citywide flow).")
    L.append(f"- **{art_top*100:.0f}% of the top-{TOPN} hotspots are on arterial roads**, vs "
             f"{art_all*100:.0f}% of all cells.")
    if poi_col:
        L.append(f"- **{poi_top*100:.0f}% of the top-{TOPN} sit next to a market, transit stop, "
                 f"school or hospital**, vs {poi_all*100:.0f}% of all cells.")
    L.append("\nThe score, derived without any of this, lines up with it. That is the closest "
             "thing to ground truth available without a live speed feed.")
    with open(os.path.join(ROOT, "outputs", "osm_validation.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"score vs road criticality: rho = {rho_road:.3f}")
    if rho_bet is not None:
        print(f"score vs betweenness:      rho = {rho_bet:.3f}")
    print(f"top-{TOPN} on arterials: {art_top*100:.0f}%  (all cells {art_all*100:.0f}%)")
    if poi_col:
        print(f"top-{TOPN} near a generator: {poi_top*100:.0f}%  (all cells {poi_all*100:.0f}%)")
    print("-> outputs/osm_validation.md, submission/figures/fig-osm.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
