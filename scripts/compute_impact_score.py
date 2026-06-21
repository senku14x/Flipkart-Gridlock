"""
compute_impact_score.py — ParkPulse Step 2/3
================================================================================
Congestion Impact Score (0-100) per H3 res-9 (~150 m) hotspot cell.

    score = 100 * (vol_pct * intensity_pct * expo_pct * persist_pct) ** 0.25

A GEOMETRIC MEAN of four percentile-ranked axes, so a cell must be bad on
SEVERAL dimensions to rank high — the score cannot collapse into raw violation
count (CLAUDE.md §6 constraint 5).

Axes (each percentile-ranked across the cells -> (0, 1]):
  volume       <- n_violations         total enforcement burden (extensive)
  intensity    <- weighted blend of per-violation composition: how obstructive
                  the TYPICAL violation in the cell is (obstruction severity,
                  main-road / junction / heavy-vehicle / crossing-signal shares)
  exposure     <- mean_expo            EXOGENOUS road-utilization weight, NOT the
                  observed violation-hour — this is how we inject "traffic flow"
                  without a feed while side-stepping the enforcement-schedule
                  confound (CLAUDE.md §6 constraint 6).
  persistence  <- active_days_ratio    chronic vs sporadic (extensive)

Minimum-support guard — empirical-Bayes shrinkage (prior count k=10):
  The per-violation MEAN features (intensity composition shares + mean_expo) are
  shrunk toward their global means before ranking:
        shrunk = (n*raw + k*prior) / (n + k)
  so a cell with 1-2 violations cannot post an extreme intensity/exposure off a
  single well-placed event (28.5% of cells have <=3 violations; 112 of them are
  100% main-road/junction flukes). Volume (count) and persistence (active-day
  ratio) are EXTENSIVE — structurally small for low-support cells — so they are
  self-guarding and ranked directly. (Shrinking the count itself would be a
  no-op: percentile rank is invariant to any monotonic transform of it.)

NO GROUND TRUTH: impact is a transparent engineered index, not a validated
measurement (CLAUDE.md §7). Validate by face validity + stability, never accuracy.

Input : data/hex_features_res9.csv   (2,534 cells x 28 features)
Output: data/hex_scored.csv          (features + axes + score + rank + why)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# --- paths --------------------------------------------------------------------
IN_PATH = "data/hex_features_res9.csv"
OUT_PATH = "data/hex_scored.csv"

# --- knobs (documented in the module docstring) ------------------------------
K_PRIOR = 10.0                          # empirical-Bayes prior strength (pseudo-count)
EPS = 1e-9                              # keep geometric-mean factors strictly > 0
OBSTRUCT_MIN, OBSTRUCT_MAX = 0.5, 1.0   # mean_obstruct_w is bounded to this range

# intensity = how obstructive the typical violation in the cell is (weights sum to 1)
INTENSITY_WEIGHTS = {
    "obstruct_norm":         0.30,   # carriageway-blocking severity (normalized)
    "main_road_share":       0.25,   # parked on a main road
    "junction_share":        0.20,   # at / near a junction (queue spillback)
    "heavy_share":           0.15,   # heavy-vehicle footprint (high PCU)
    "crossing_signal_share": 0.10,   # near a crossing / signal
}
# per-violation MEAN features that get empirical-Bayes shrinkage (the guard)
SHRINK_COLS = ["mean_obstruct_w", "main_road_share", "junction_share",
               "heavy_share", "crossing_signal_share", "mean_expo"]


# --- core ---------------------------------------------------------------------
def load_features(path: str = IN_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {"n_violations", "active_days_ratio", *SHRINK_COLS} - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing expected columns: {sorted(missing)}")
    df[SHRINK_COLS] = df[SHRINK_COLS].fillna(0.0)
    return df


def pct_rank(s: pd.Series) -> pd.Series:
    """Percentile rank in (0, 1] (ties share the average); strictly > 0."""
    return s.rank(pct=True, method="average").clip(lower=EPS)


def record_weighted_mean(df: pd.DataFrame, col: str) -> float:
    """Global prior = `col` averaged over violations (weighted by cell count)."""
    w = df["n_violations"]
    return float((df[col] * w).sum() / w.sum())


def eb_shrink(raw: pd.Series, n: pd.Series, prior: float, k: float = K_PRIOR) -> pd.Series:
    """Empirical-Bayes shrinkage of a per-violation mean toward `prior`."""
    return (n * raw + k * prior) / (n + k)


def build_axes(df: pd.DataFrame, k: float = K_PRIOR,
               weights: dict | None = None) -> pd.DataFrame:
    """Add the four percentile-ranked axes (+ intensity_raw) to a copy of df."""
    weights = weights or INTENSITY_WEIGHTS
    df = df.copy()
    n = df["n_violations"]

    # empirical-Bayes shrink the per-violation mean features (minimum-support guard)
    priors = {c: record_weighted_mean(df, c) for c in SHRINK_COLS}
    sh = {c: eb_shrink(df[c], n, priors[c], k) for c in SHRINK_COLS}

    # obstruction weight [0.5, 1.0] -> [0, 1]
    obstruct_norm = ((sh["mean_obstruct_w"] - OBSTRUCT_MIN) /
                     (OBSTRUCT_MAX - OBSTRUCT_MIN)).clip(0.0, 1.0)

    # intensity: weighted blend of (shrunk) composition
    intensity_raw = (
        weights["obstruct_norm"]         * obstruct_norm +
        weights["main_road_share"]       * sh["main_road_share"] +
        weights["junction_share"]        * sh["junction_share"] +
        weights["heavy_share"]           * sh["heavy_share"] +
        weights["crossing_signal_share"] * sh["crossing_signal_share"]
    )
    df["intensity_raw"] = intensity_raw

    # four axes in (0, 1]
    df["vol_pct"]       = pct_rank(df["n_violations"])       # extensive -> self-guarding
    df["intensity_pct"] = pct_rank(intensity_raw)            # EB-guarded
    df["expo_pct"]      = pct_rank(sh["mean_expo"])          # EB-guarded, exogenous
    df["persist_pct"]   = pct_rank(df["active_days_ratio"])  # extensive -> self-guarding
    return df


def compute_score(df: pd.DataFrame) -> pd.DataFrame:
    """Geometric mean of the four axes -> impact_score (0-100) + impact_rank."""
    df = df.copy()
    g = (df["vol_pct"] * df["intensity_pct"] * df["expo_pct"] * df["persist_pct"]).clip(lower=EPS)
    df["impact_score"] = 100.0 * g ** 0.25
    df["impact_rank"] = df["impact_score"].rank(ascending=False, method="min").astype(int)
    return df


def make_why(r: pd.Series) -> str:
    """Human-readable driver summary (raw shares for interpretability)."""
    bits: list[str] = []
    # volume
    if r.vol_pct >= 0.90:
        bits.append("very high volume")
    elif r.vol_pct >= 0.75:
        bits.append("high volume")
    elif r.vol_pct >= 0.50:
        bits.append("moderate volume")
    # composition / intensity drivers
    if r.junction_share >= 0.50:
        bits.append("junction-adjacent")
    if r.main_road_share >= 0.25:
        bits.append("main-road-heavy")
    if r.heavy_share >= 0.15:
        bits.append("heavy-vehicle")
    if r.crossing_signal_share >= 0.05:
        bits.append("near crossing/signal")
    if r.mean_obstruct_w >= 0.75 and "main-road-heavy" not in bits:
        bits.append("high-obstruction")
    # persistence
    if r.active_days_ratio >= 0.50:
        bits.append("chronic (active most days)")
    elif r.active_days_ratio >= 0.25:
        bits.append("chronic")
    elif r.active_days_ratio >= 0.12:
        bits.append("recurring")
    # exposure (exogenous road-utilization magnitude; NOT observed violation-hour)
    if r.expo_pct >= 0.80:
        bits.append("peak-exposed")
    elif r.expo_pct >= 0.60:
        bits.append("exposed")
    if not bits:
        bits.append("low across factors")
    return " · ".join(bits)


def score_hotspots(df: pd.DataFrame | None = None, k: float = K_PRIOR) -> pd.DataFrame:
    """End-to-end: feature table -> scored, impact-sorted table (importable)."""
    if df is None:
        df = load_features()
    df = build_axes(df, k=k)
    df = compute_score(df)
    df["why"] = df.apply(make_why, axis=1)
    return df.sort_values("impact_score", ascending=False).reset_index(drop=True)


# --- reporting ----------------------------------------------------------------
def print_summary(df: pd.DataFrame) -> None:
    line = "=" * 80
    print(line)
    print(f"ParkPulse — Congestion Impact Score  |  {len(df)} hotspot cells (H3 res-9)")
    print(line)

    print("\nScore distribution:")
    print(df["impact_score"].describe(percentiles=[.5, .75, .9, .95, .99]).round(2).to_string())

    rho = spearmanr(df.impact_score, df.n_violations).statistic
    flag = "OK (decoupled)" if rho < 0.85 else "** TOO HIGH — intensity axis not biting **"
    print(f"\nSpearman(impact_score, n_violations) = {rho:.3f}   [target < ~0.85]  -> {flag}")
    for ax in ["vol_pct", "intensity_pct", "expo_pct", "persist_pct"]:
        print(f"    {ax:14s} vs n_violations: rho={spearmanr(df[ax], df.n_violations).statistic:+.3f}")

    top = df.head(50)
    print("\nMinimum-support guard:")
    print(f"    smallest n_violations in top-50  = {int(top.n_violations.min())}"
          f"   (median n among top-50 = {int(top.n_violations.median())})")
    print(f"    cells with n_violations <= 2 in top-100 = {(df.head(100).n_violations <= 2).sum()}")

    cols = ["impact_rank", "h3_9", "dom_station", "dom_violation", "modal_hour",
            "n_violations", "impact_score", "why"]
    show = df.head(25)[cols].copy()
    show["impact_score"] = show["impact_score"].round(1)
    print("\nTOP 25 hotspot cells by Congestion Impact Score:")
    print(show.to_string(index=False))

    # risers: impact rank far better than raw-count rank (intensity/exposure earning it)
    d = df.copy()
    d["rank_by_count"] = d.n_violations.rank(ascending=False, method="min").astype(int)
    d["rise"] = d.rank_by_count - d.impact_rank
    ris = d[d.n_violations >= 20].sort_values("rise", ascending=False).head(10)
    ris = ris[["h3_9", "dom_station", "n_violations", "rank_by_count", "impact_rank",
               "impact_score", "why"]].copy()
    ris["impact_score"] = ris["impact_score"].round(1)
    print("\nRISERS — moderate volume but high intensity/exposure "
          "(impact rank << raw-count rank): the two-axis design at work")
    print(ris.to_string(index=False))


def main() -> None:
    df = load_features()
    scored = score_hotspots(df)
    scored.to_csv(OUT_PATH, index=False)
    print_summary(scored)
    print(f"\nSaved -> {OUT_PATH}   ({scored.shape[0]} rows x {scored.shape[1]} cols)")
    print("NOTE: impact is a transparent engineered index — there is NO ground-truth "
          "flow data.\n      Validate by face validity + stability, never 'accuracy' (CLAUDE.md §7).")


if __name__ == "__main__":
    main()
