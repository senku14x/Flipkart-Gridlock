# KICKOFF (Step 2/3): Congestion Impact Score + Impact-Weighted Hotspot Map

> Paste the block below into Claude Code once it's running in the repo (it will have loaded `CLAUDE.md`). Everything it needs is already in the repo; this defines the task, the exact method, and the acceptance criteria.

---

## PASTE THIS INTO CLAUDE CODE:

You've read `CLAUDE.md`. We're building **Step 2/3**: the Congestion Impact Score and the impact-weighted hotspot map, plus a face-validity check. Work only from the existing artifacts; do **not** re-run cleaning.

**Input:** `data/hex_features_res9.csv` (2,534 hotspot cells × 28 features; schema in CLAUDE.md §5). Use `data/parkpulse_clean_records.parquet` only if you need record-level detail.

### Task 1: `scripts/compute_impact_score.py`

Compute a **Congestion Impact Score (0–100)** per hotspot cell as a **geometric mean of four percentile-normalized axes**, so a cell must be bad on several dimensions to rank high (it must NOT collapse into raw count; see CLAUDE.md §6 constraint 5).

Axes (each mapped to [0,1] via **percentile rank** across cells):
1. **Volume**: from `n_violations` (use `log_n` or the percentile rank of `n_violations`).
2. **Intensity**: a weighted blend of per-violation composition, then percentile-ranked:
   `0.30*mean_obstruct_w_norm + 0.25*main_road_share + 0.20*junction_share + 0.15*heavy_share + 0.10*crossing_signal_share`
   (these capture how obstructive the *typical* violation in the cell is).
3. **Exposure**: from `mean_expo` (already 0–1; percentile-rank it).
4. **Persistence**: from `active_days_ratio` (already 0–1; percentile-rank it).

`score = 100 * (vol_pct * intensity_pct * expo_pct * persist_pct) ** 0.25`

Requirements:
- **Minimum-support guard:** cells with very few violations must not top the ranking off a single fluke. Apply shrinkage toward the median (e.g., a Bayesian/empirical-Bayes shrink on the volume axis using a prior count k≈10) OR a soft floor; document the choice.
- Output `data/hex_scored.csv` = the feature table **plus**: `impact_score`, the four axis columns (`vol_pct`, `intensity_pct`, `expo_pct`, `persist_pct`), `impact_rank`, and a human-readable `why` string (e.g., "high volume · main-road-heavy · chronic · PM-exposed").
- Print: score distribution summary, Spearman corr of `impact_score` vs raw `n_violations` (expected < ~0.85; if it's ~0.99, the intensity axis isn't doing its job and should be investigated), and the **top 25 cells** with `dom_station`, `dom_violation`, `modal_hour`, score, and `why`.
- Keep functions importable; guard the runner with `if __name__ == "__main__":`.

### Task 2: `scripts/build_map.py`

An interactive **folium** map saved to `outputs/parkpulse_map.html`:
- H3 res-9 cell polygons (use `h3.cells_to_geo`/`cell_to_boundary` from the h3 v4 API) colored by `impact_score` (sequential colormap), popups showing the breakdown (`why`, score, top violation, modal hour, n_violations).
- **A raw-count/impact-score toggle** via two `FeatureGroup` layers + `LayerControl` (show how impact-weighting re-ranks cells vs raw density).
- Center on Bengaluru; sensible zoom; legend.

### Task 3: Ranked zones + enforcement windows

Write `outputs/top_zones.md` (and a CSV): the **top 30 enforcement zones** by `impact_score`, each with dominant station, dominant violation, **recommended enforcement window** (use `modal_hour`, and note if `hour_entropy` is low = tightly predictable), n_violations, and the `why`. This is the ops payload.

### Task 4: Face-validity check

Since there's **no ground truth** for impact (CLAUDE.md §7), validate by **face validity**: do the top-scored zones land on known Bengaluru commercial/market/arterial parking-problem areas? Use the `dom_station` and `location` text we already have (no geocoding needed; optionally reverse-geocode top cells if osmnx/geopy is available). Print the top-20 zones with their station/location and a short note on whether they match expectation (e.g., City Market / Chickpet / Commercial Street / Malleshwaram / Shivajinagar / KR Market / Majestic-Upparpet are known dense-parking commercial cores). Also report **month-to-month rank stability** of the top cells as a robustness check.

### Acceptance criteria
- `impact_score` does NOT just mirror `n_violations` (Spearman < ~0.85); high-intensity-but-moderate-volume cells visibly rise vs a pure count ranking (show a few examples).
- The map opens, the toggle works, popups show the breakdown.
- Top-zones list reads like an actionable enforcement plan (where + when + why).
- Everything reproducible from `data/hex_features_res9.csv`; no re-cleaning; honest about the no-ground-truth nature of the score.

### Watch out for (from EDA)
- Don't weight time by observed violation-hour; use `mean_expo` (enforcement-schedule confound).
- The night/4–5am mass is an enforcement sweep, not demand; don't let `night_share` masquerade as congestion.
- Percentile-rank before combining; geometric mean needs all axes in [0,1] and strictly > 0 (add a tiny epsilon).

Once this is complete, next steps are the patrol optimizer + Pareto (Step 5), the forecaster (supervised ML with temporal holdout, Step 7), and the web app (Step 8).
