"""
submission/make_figures.py: generate clean, branded figures for the LaTeX solution
doc from the committed data. Writes PNGs to submission/figures/.

Run:  python submission/make_figures.py
"""
from __future__ import annotations
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "submission", "figures")
os.makedirs(FIG, exist_ok=True)

ACCENT, TEAL, GOLD, INK, GREY = "#e4572e", "#36b3a8", "#c9a227", "#1b2a4a", "#8a93a3"
plt.rcParams.update({
    "font.size": 11, "font.family": "DejaVu Sans",
    "axes.edgecolor": "#cccccc", "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.dpi": 150, "axes.titleweight": "bold",
})


def save(name):
    plt.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close()


def main():
    df = pd.read_csv(os.path.join(ROOT, "data", "hex_scored.csv"))

    # 1) impact map (scatter of cells, colored + sized by impact)
    o = df.sort_values("impact_score")
    fig, ax = plt.subplots(figsize=(6, 5.3))
    sc = ax.scatter(o.lon, o.lat, c=o.impact_score, cmap="inferno",
                    s=5 + o.impact_score * 0.45, alpha=0.85, linewidths=0)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(sc, ax=ax, fraction=0.045, pad=0.02)
    cb.set_label("Congestion Impact Score")
    ax.set_title("Impact-weighted hotspots: 2,534 H3 cells (Bengaluru)", fontsize=11)
    save("fig-map.png")

    # 2) impact concentration (Lorenz)
    v = np.sort(df.impact_sum.values)[::-1]
    cum = np.cumsum(v) / v.sum() * 100
    x = np.arange(1, len(v) + 1) / len(v) * 100
    i1 = max(int(0.01 * len(v)), 1)
    fig, ax = plt.subplots(figsize=(6, 3.9))
    ax.plot(x, cum, color=ACCENT, lw=2.2)
    ax.fill_between(x, cum, color=ACCENT, alpha=0.08)
    ax.scatter([1], [cum[i1 - 1]], color=INK, zorder=5)
    ax.annotate(f"top 1% of cells = {cum[i1 - 1]:.0f}% of impact",
                (1, cum[i1 - 1]), xytext=(14, cum[i1 - 1] - 22), fontsize=9,
                arrowprops=dict(arrowstyle="-", color=GREY))
    ax.set_xlabel("share of cells (%)"); ax.set_ylabel("cumulative share of impact (%)")
    ax.set_xlim(0, 100); ax.set_ylim(0, 101)
    ax.set_title("Impact is extremely concentrated", fontsize=11)
    save("fig-concentration.png")

    # 3) enforcement gap (effort vs impact by window)
    g = json.load(open(os.path.join(ROOT, "outputs", "enforcement_gap.json")))
    W = g["windows"]
    eff = [w["effort"] for w in W]; imp = [w["impact"] for w in W]
    names = [w["name"].replace(" (", "\n(") for w in W]
    xi = np.arange(len(W)); wd = 0.38
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.bar(xi - wd / 2, eff, wd, color=GREY, label="share of effort")
    ax.bar(xi + wd / 2, imp, wd, color=[ACCENT if i < e else TEAL for e, i in zip(eff, imp)],
           label="share of impact")
    ax.set_xticks(xi); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("% of total"); ax.legend(frameon=False, fontsize=9)
    ax.set_title("Where effort goes vs where impact is", fontsize=11)
    save("fig-gap.png")

    # 4) patrol coverage curve
    p = json.load(open(os.path.join(ROOT, "web", "public", "data", "pareto.json")))
    B = p["beats"]; N = [b["n"] for b in B]
    gr = [b["greedy"] for b in B]; nv = [b["naive"] for b in B]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.plot(N, gr, color=TEAL, lw=2.2, label="greedy max-coverage")
    ax.plot(N, nv, color=GREY, ls="--", lw=1.6, label="naive top-N")
    ax.scatter([20], [gr[19]], color=ACCENT, zorder=5)
    ax.annotate(f"20 beats = {gr[19]:.0f}% of impact\n(~Rs {B[19]['roi'] / 1000:.0f}k/day relieved)",
                (20, gr[19]), xytext=(24, gr[19] - 17), fontsize=9,
                arrowprops=dict(arrowstyle="-", color=GREY))
    ax.set_xlabel("patrol beats deployed"); ax.set_ylabel("% of citywide impact covered")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Patrol coverage: clustering beats naive picking", fontsize=11)
    save("fig-coverage.png")

    # 5) forecaster bake-off
    f = json.load(open(os.path.join(ROOT, "web", "public", "data", "forecast.json")))
    M = f["models"]

    def short(m):
        return (m.replace(" (Tweedie)", "").replace(" (Poisson)", "").replace(" (lag 7d)", ""))
    nm = [short(m["model"]) for m in M]
    cov = [m["cov20"] * 100 for m in M]; ism = [m["is_model"] for m in M]
    idx = np.argsort(cov)
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.barh([nm[i] for i in idx], [cov[i] for i in idx],
            color=[ACCENT if ism[i] else GREY for i in idx])
    ax.set_xlabel("coverage@20 (%)")
    ax.set_title("Forecaster bake-off (orange = models, grey = baselines)", fontsize=10)
    save("fig-forecast.png")

    # 6) pipeline diagram
    fig, ax = plt.subplots(figsize=(7.4, 2.7)); ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 3)

    def box(x, y, w, h, text, fc, tc="white", fs=8.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    fc=fc, ec="none"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs)

    def arrow(x1, x2, y=1.5):
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=12,
                                     color=GREY, lw=1.2))
    box(0.05, 1.1, 1.7, 0.8, "298,445\nviolation records", INK)
    arrow(1.8, 2.15)
    box(2.2, 1.1, 1.7, 0.8, "Congestion\nImpact Score", ACCENT)
    arrow(3.95, 4.35)
    box(4.4, 2.0, 2.3, 0.62, "SEE:  map, zones", TEAL)
    box(4.4, 1.19, 2.3, 0.62, "UNDERSTAND:\ncost, gap, trends", TEAL, fs=8)
    box(4.4, 0.38, 2.3, 0.62, "ACT:  forecaster,\ntriage, optimizer", TEAL, fs=8)
    arrow(6.75, 7.15)
    box(7.2, 1.1, 2.7, 0.8, "Where + when + cost\n+ how many patrols", GOLD, tc=INK)
    ax.set_title("ParkPulse pipeline: from a noisy feed to a costed patrol plan",
                 fontsize=10, color=INK)
    save("fig-pipeline.png")

    print("wrote", len(os.listdir(FIG)), "figures ->", FIG)


if __name__ == "__main__":
    main()
