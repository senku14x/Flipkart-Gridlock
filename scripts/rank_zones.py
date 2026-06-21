"""
rank_zones.py - ParkPulse Step 2/3 (Task 3)
================================================================================
Turn the scored hotspot table into the ops payload: the top enforcement zones,
each with a dominant station/location, dominant violation, a recommended
enforcement window, predictability, and the `why` breakdown.

Enforcement window (the confound-safe part, CLAUDE.md §6.6):
  The raw modal violation-hour is confounded by the daily 4-5am enforcement
  sweep, so we do NOT recommend it directly. Instead we pick the 2-hour window
  that maximises EXPOSURE-WEIGHTED activity, i.e. sum of `expo_weight` (the
  exogenous diurnal road-utilisation curve, 0.1 overnight -> 1.0 at 8-10am /
  5-7pm) over the cell's violations. The pre-dawn sweep self-cancels (x0.1),
  so the window lands when this cell's parking actually coincides with busy
  roads. The raw modal hour is still shown (flagged if it falls in the sweep).

Inputs : data/hex_scored.csv, data/parkpulse_clean_records.parquet
Outputs: outputs/zone_enrichment.csv  (per-cell location + windows, all cells)
         outputs/top_zones.csv, outputs/top_zones.md   (top-N enforcement zones)
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

SCORED_PATH = "data/hex_scored.csv"
PARQUET_PATH = "data/parkpulse_clean_records.parquet"
ENRICH_PATH = "outputs/zone_enrichment.csv"
TOPZONES_CSV = "outputs/top_zones.csv"
TOPZONES_MD = "outputs/top_zones.md"
TOP_N = 30


# --- per-cell enrichment from the record-level table --------------------------
def _mode_str(s: pd.Series) -> str:
    s = s.dropna()
    m = s.mode()
    return str(m.iloc[0]) if len(m) else ""


def enrich_from_records(parquet_path: str = PARQUET_PATH) -> pd.DataFrame:
    """Per H3 cell: dominant location text + exposure-weighted enforcement window."""
    r = pd.read_parquet(parquet_path, columns=["h3_9", "hour", "expo_weight", "location"])

    # exposure-weighted hour profile: sum(expo_weight) at hour h == count(h)*expo(h)
    prof = (r.groupby(["h3_9", "hour"])["expo_weight"].sum()
              .unstack(fill_value=0.0).reindex(columns=range(24), fill_value=0.0))
    arr = prof.to_numpy()
    total = arr.sum(axis=1)
    two_hr = arr + np.roll(arr, -1, axis=1)
    two_hr[:, 23] = -1.0                      # don't let a window wrap past midnight
    win_start = two_hr.argmax(axis=1)
    peak_hour = arr.argmax(axis=1)
    # share of exposure-weighted activity captured by the recommended 2h window
    win_capture = two_hr[np.arange(len(arr)), win_start] / np.where(total > 0, total, 1.0)

    out = pd.DataFrame({
        "h3_9": prof.index,
        "rec_win_start": win_start,
        "rec_peak_hour": peak_hour,
        "window_capture": win_capture.round(3),
    })
    out["rec_window"] = [f"{h:02d}:00–{(h + 2):02d}:00" for h in out.rec_win_start]
    loc = r.groupby("h3_9")["location"].agg(_mode_str)
    out = out.merge(loc.rename("dom_location"), on="h3_9", how="left")
    return out


# --- presentation helpers -----------------------------------------------------
def predictability(entropy: float) -> str:
    if entropy < 1.5:
        return "tight / predictable"
    if entropy < 2.5:
        return "moderate"
    return "diffuse"


def short_location(text: str, n: int = 48) -> str:
    if not isinstance(text, str) or not text:
        return "—"
    text = text.split(", Bengaluru")[0].split(", Bangalore")[0]   # drop city/state tail
    parts = [p.strip() for p in text.split(",")]
    out = ", ".join(parts[:2]) if len(parts) >= 2 else text
    return out[:n].rstrip(" ,") + ("…" if len(out) > n else "")


def modal_hour_note(modal_hour: int) -> str:
    h = int(modal_hour)
    tag = "  [pre-dawn sweep]" if 0 <= h <= 5 else ""
    return f"{h:02d}:00{tag}"


# --- build the ranked table ---------------------------------------------------
def build_top_zones(n: int = TOP_N, scored_path: str = SCORED_PATH,
                    enrich: pd.DataFrame | None = None) -> pd.DataFrame:
    df = pd.read_csv(scored_path).sort_values("impact_score", ascending=False)
    if enrich is None:
        enrich = enrich_from_records()
    df = df.merge(enrich, on="h3_9", how="left")
    top = df.head(n).copy()

    top["zone"] = top["impact_rank"].astype(int)
    top["recommended_window"] = top["rec_window"]
    top["predictability"] = top["hour_entropy"].map(predictability)
    top["modal_logged_hour"] = top["modal_hour"].map(modal_hour_note)
    top["location"] = top["dom_location"].map(short_location)
    top["impact_score"] = top["impact_score"].round(1)
    return top


def write_csv(top: pd.DataFrame, path: str = TOPZONES_CSV) -> None:
    cols = ["impact_rank", "h3_9", "dom_station", "dom_location", "impact_score",
            "n_violations", "dom_violation", "recommended_window", "rec_peak_hour",
            "window_capture", "modal_hour", "hour_entropy", "predictability", "why",
            "vol_pct", "intensity_pct", "expo_pct", "persist_pct", "lat", "lon"]
    top[cols].to_csv(path, index=False)


def write_markdown(top: pd.DataFrame, path: str = TOPZONES_MD, n: int = TOP_N) -> None:
    lines = [
        f"# ParkPulse: Top {n} Enforcement Zones",
        "",
        "Ranked by **Congestion Impact Score** (0-100), a geometric mean of "
        "volume × intensity × exposure × persistence. A zone must rank poorly on "
        "several axes to score high (not just high count).",
        "",
        "**Recommended window** is exposure-weighted: the 2-hour block when this "
        "cell's violations most coincide with busy roads (exogenous diurnal curve). "
        "It ignores the daily 4-5am enforcement sweep. The raw "
        "*most-logged hour* is shown separately and flagged when it falls in that "
        "sweep. **Predictability** comes from hour-entropy (tight = schedule it).",
        "",
        f"> The highest-impact zones are **chronic all-day** problems (high hour-entropy, "
        f"\"diffuse\"), so they need sustained presence. The recommended 2-hour window "
        f"still concentrates the single best slice, capturing **{100*top['window_capture'].mean():.0f}%** "
        f"of each zone's exposure-weighted activity on average.",
        "",
        "> Note: impact is an engineered index. There is **no traffic-flow "
        "ground truth** in this data. Validate by face validity + stability, not accuracy.",
        "",
        "| # | Zone (station) | Location | Impact | Violations | Top violation | "
        "Recommended window (IST) | Most-logged hr | Predictability | Why |",
        "|--:|---|---|--:|--:|---|---|---|---|---|",
    ]
    for t in top.itertuples(index=False):
        lines.append(
            f"| {int(t.impact_rank)} | {t.dom_station} | {t.location} | "
            f"{t.impact_score:.1f} | {int(t.n_violations):,} | {t.dom_violation} | "
            f"**{t.recommended_window}** | {t.modal_logged_hour} | {t.predictability} | "
            f"{t.why} |"
        )
    lines += [
        "",
        "---",
        f"*Generated by `scripts/rank_zones.py` from `data/hex_scored.csv` "
        f"(+ record-level exposure profile). Full machine-readable table: "
        f"`outputs/top_zones.csv`.*",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    os.makedirs("outputs", exist_ok=True)
    enrich = enrich_from_records()
    enrich.to_csv(ENRICH_PATH, index=False)
    top = build_top_zones(enrich=enrich)
    write_csv(top)
    write_markdown(top)

    # console preview
    prev = top[["impact_rank", "dom_station", "location", "impact_score",
                "n_violations", "recommended_window", "modal_logged_hour",
                "predictability"]].copy()
    print(f"Top {TOP_N} enforcement zones (preview):")
    print(prev.to_string(index=False))
    # how many top zones would have been mis-scheduled to the night sweep?
    swept = (top.modal_hour.astype(int) <= 5).sum()
    print(f"\n{swept}/{TOP_N} top zones have a raw modal hour in the 0-5am sweep band; "
          f"the exposure-weighted window corrects these to daytime.")
    print(f"\nSaved -> {TOPZONES_MD}, {TOPZONES_CSV}, {ENRICH_PATH}")


if __name__ == "__main__":
    main()
