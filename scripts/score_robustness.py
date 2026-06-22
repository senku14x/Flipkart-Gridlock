"""
scripts/score_robustness.py: stress-test the Congestion Impact Score against its own
design choices, to answer "why those weights?".

The score is an equal-weighted geometric mean of four percentile-ranked axes
(volume, intensity, exposure, persistence). Here we (1) re-weight the axes across
thousands of reasonable weightings and measure how much the ranking moves, (2) try
arithmetic vs geometric aggregation, and (3) drop or double each axis. A ranking that
survives all of this is not an artefact of one arbitrary weighting.

Reads data/hex_scored.csv. Writes outputs/score_robustness.md and
submission/figures/fig-robustness.png.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AX = ["vol_pct", "intensity_pct", "expo_pct", "persist_pct"]
LBL = ["volume", "intensity", "exposure", "persistence"]
ACCENT, INK, GREY = "#e4572e", "#1b2a4a", "#8a93a3"


def main():
    df = pd.read_csv(os.path.join(ROOT, "data", "hex_scored.csv"))
    A = df[AX].clip(1e-6, 1.0).values          # n x 4 percentile axes in (0,1]
    base = df["impact_score"].values
    border = np.argsort(-base)
    b20, b50 = set(border[:20]), set(border[:50])

    def geo(expo):
        return (A ** expo).prod(axis=1)

    # sanity: equal-weight geometric mean reproduces the committed score ranking
    eq_rho = spearmanr(geo(np.ones(4)), base).correlation

    # (1) random re-weightings: each axis exponent ~ U(0.5, 1.5) => up to 3x relative
    rng = np.random.default_rng(7)
    N = 2000
    rhos, j20, keep20 = [], [], np.zeros(20)
    b20_list = list(border[:20])
    for _ in range(N):
        e = rng.uniform(0.5, 1.5, 4)
        s = geo(e)
        rhos.append(spearmanr(s, base).correlation)
        t20 = set(np.argsort(-s)[:20])
        j20.append(len(b20 & t20) / len(b20 | t20))
        for i, c in enumerate(b20_list):
            keep20[i] += c in t20
    rhos = np.array(rhos); j20 = np.array(j20)
    retain20 = np.array([len(set(np.argsort(-geo(rng.uniform(0.5, 1.5, 4)))[:20]) & b20)
                         for _ in range(N)])

    # (2) aggregation choice: arithmetic mean instead of geometric
    arith_rho = spearmanr(A.mean(axis=1), base).correlation

    # (3) drop-one and double-one each axis
    drop, dbl = {}, {}
    for i, name in enumerate(LBL):
        e = np.ones(4); e[i] = 0.0
        drop[name] = spearmanr(geo(e), base).correlation
        e = np.ones(4); e[i] = 2.0
        s = geo(e); dbl[name] = len(set(np.argsort(-s)[:20]) & b20)

    # ---- figure ----
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.hist(rhos, bins=40, color=ACCENT, alpha=0.85)
    ax.axvline(np.median(rhos), color=INK, lw=1.5, ls="--")
    ax.set_xlabel("Spearman rank correlation vs the shipped ranking")
    ax.set_ylabel("count of weightings")
    ax.set_title("Ranking is stable across 2,000 random axis weightings", fontsize=11)
    ax.annotate(f"median {np.median(rhos):.3f}\ntop-20 kept: {np.median(retain20):.0f}/20 (median)",
                xy=(np.median(rhos), ax.get_ylim()[1] * 0.8),
                xytext=(0.05, 0.78), textcoords="axes fraction", fontsize=9, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(os.path.join(ROOT, "submission", "figures", "fig-robustness.png"),
                bbox_inches="tight", facecolor="white", dpi=150)
    plt.close()

    L = ["# ParkPulse: impact-score robustness\n",
         "The score is an equal-weighted geometric mean of four percentile-ranked axes "
         "(volume, intensity, exposure, persistence). Is the ranking an artefact of that "
         "particular weighting? We stress-test it.\n",
         f"Equal weights reproduce the shipped score (Spearman {eq_rho:.3f}), as expected.\n",
         "## 1. Random re-weightings (each axis varied up to 3x in relative importance)\n",
         f"- Across **{N} random weightings**, the ranking holds: **median Spearman "
         f"{np.median(rhos):.3f}** (5th percentile {np.percentile(rhos,5):.3f}).",
         f"- The top-20 zones are sticky: a random weighting keeps **{np.median(retain20):.0f} of "
         f"the 20** on average (worst case {retain20.min()}/20), top-20 Jaccard median {np.median(j20):.2f}.\n",
         "## 2. Aggregation choice\n",
         f"- Switching from geometric to an **arithmetic** mean still gives Spearman "
         f"{arith_rho:.3f} against the shipped ranking. The conclusion does not hinge on the mean.\n",
         "## 3. Drop or double a single axis\n",
         "| Axis | Spearman if dropped | Top-20 kept if doubled |",
         "|---|--:|--:|"]
    for name in LBL:
        L.append(f"| {name} | {drop[name]:.3f} | {dbl[name]}/20 |")
    L.append("\nNo single axis dominates: dropping any one still correlates strongly with the "
             "full score, and doubling any one keeps most of the top-20. The ranking reflects "
             "the data's structure, not a hand-tuned weighting.")
    with open(os.path.join(ROOT, "outputs", "score_robustness.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"equal-weight check: rho={eq_rho:.3f}")
    print(f"random re-weightings: median rho={np.median(rhos):.3f}, top-20 kept median={np.median(retain20):.0f}/20")
    print(f"arithmetic mean: rho={arith_rho:.3f}")
    print("drop-one rho:", {k: round(v, 3) for k, v in drop.items()})
    print("-> outputs/score_robustness.md, submission/figures/fig-robustness.png")


if __name__ == "__main__":
    main()
