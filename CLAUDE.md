# CLAUDE.md: ParkPulse

> Project context for **Claude Code**. This file is auto-loaded every session. **Read it fully before writing code.** It encodes decisions from the EDA; following it prevents the common mistakes this dataset invites.

---

## 1. What this project is

**ParkPulse**: submission for **Gridlock Hackathon 2.0 (Flipkart), Round 2 (Prototype)**.
**Theme:** *Poor Visibility on Parking-Induced Congestion.*

**One-liner:** Parking intelligence that finds chronic illegal-parking hotspots, scores each by its drag on traffic flow, and tells enforcement **where and when** to deploy for the most congestion relief per patrol-hour.

**This is a PRIORITIZATION / decision-support problem.** It is **not**:
- a computer-vision violation detector (that's a *different* hackathon theme; input here is an already-detected violation feed, and our job is the intelligence layer on top);
- general traffic-congestion modeling (only the *parking-induced* slice);
- a system that *measures* traffic flow (we have none; impact is **derived**, see §4).

The success test: a traffic officer reads the output and says *"tomorrow send the team to **these** spots at **these** hours, because that's where parking chokes traffic worst."*

---

## 2. Current state & where to pick up

- **EDA complete** (DONE), data cleaned, features engineered. Full profile: `ParkPulse_EDA_Report.md` (read §3 + §9 there).
- **Artifacts ready (use these, don't regenerate unless changing logic):**
  - `data/parkpulse_clean_records.parquet`: 298,445 cleaned records (IST, exploded violations, PCU + obstruction weights, H3 indices). Record grain.
  - `data/hex_features_res9.csv`: **2,534 hotspot cells × 28 features**. The modeling table. Schema in §5.
- **Step 2–3 DONE**: Congestion Impact Score (`scripts/compute_impact_score.py` → `data/hex_scored.csv`), impact-weighted map (`scripts/build_map.py` → `outputs/parkpulse_map.html`), ranked zones + exposure-weighted windows (`scripts/rank_zones.py` → `outputs/top_zones.md`), face-validity + stability (`scripts/face_validity.py`). Spearman(impact, count)=0.56; 20/20 top zones face-valid; month-to-month ρ≈0.75.
- **Step 7 DONE (forecaster)**: `scripts/forecast.py`: multi-model GBM bake-off (LightGBM/XGBoost/CatBoost/HistGBM, Tweedie/Poisson) on a strict temporal holdout (train Nov–Feb, test Mar–Apr), 906 hotspot cells. Beats seasonal-naive (+36% coverage@20) and dominates on calibration; honest that base-rate explains most of the "where". Feature-engineering ablation: +29 features (weekly/momentum/holiday/spatial) tested, and the **base 24-feature set is optimal**; granular per-cell×weekday features overfit (~16 samples each). Hyperparameter search + 4-model ensemble also add nothing (within noise; `scripts/forecast_tune.py`). Ceiling is data (flow feed / events / patrol roster), not features. Outputs `outputs/forecast_metrics.md`, `forecast_eval.png`, `forecast_model.pkl`.
- **Step 5 DONE (patrol optimizer)**: `scripts/patrol_optimizer.py`: Pareto on exposure-weighted `impact_sum` (top 20 cells = 31% of impact; 58 cells = 50%) + greedy max-coverage optimizer (each beat = cell + H3 ring; 20 beats cover 53% vs 47% naive) + forecaster-driven next-day plan (14/20 beats shared with the static plan). Outputs `outputs/patrol_plan.md/.csv`, `pareto.png`.
- **Step 8 DONE (web app)**: `web/`: a custom **Next.js (static export) + deck.gl `H3HexagonLayer` + Recharts** site (NOT Streamlit; it can't run on Vercel). Sections: hero/KPIs, impact map (raw/impact toggle, hover breakdown), ranked zones, forecaster (bake-off + ablation), live patrol optimizer (N-beats slider), methodology. Fully static; reads `web/public/data/*.json` from `web/prepare_data.py`; deploys to Vercel (Root Directory = `web`), no backend/tokens. Verified building + rendering headless (deck.gl + React 19).
- **Analytics upgrades DONE**: congestion cost (`congestion_cost.py`, ~Rs 5.2 cr/yr est. delay), false-detection classifier (`detection_validity.py`, ROC-AUC 0.758), emerging hotspots (`emerging_hotspots.py`, share-detrended trend over the 4 full months), optional OSM road criticality (`enrich_osm.py`, run locally; geo APIs blocked in CI). All surfaced in `web/` (cost / trends / triage sections; cost + trend in the map hover). Dropped an hour-level schedule: pm_peak_share is ~0 citywide (enforcement rarely works evenings), so observed hours reflect patrol shifts, not congestion.
- **Next:** deploy (user to Vercel) + Step 9 deliverables (deck, video, source zip, screenshots).
- Roadmap, decisions, and the submission tracker: **`ParkPulse_Project_Master.md`** (the source of truth).

---

## 3. Repo layout

```
parkpulse/
├── CLAUDE.md                      # this file
├── README.md                     # orientation + reproduce steps
├── ParkPulse_Project_Master.md   # SOURCE OF TRUTH: problem, design, roadmap, submission tracker
├── ParkPulse_EDA_Report.md       # full data profile + modeling playbook
├── KICKOFF_STEP2.md              # the next build task (impact score + map)
├── requirements.txt
├── .gitignore                    # MUST ignore data/violations.csv (see §10)
├── data/
│   ├── violations.csv            # raw ~105MB, GITIGNORED (exceeds GitHub 100MB limit)
│   ├── parkpulse_clean_records.parquet
│   ├── hex_features_res9.csv
│   └── (generated: hex_scored.csv, etc.)
├── eda_plots/                    # 12 EDA figures
├── scripts/                      # all Python (EDA pipeline lives here; add new modules here)
│   ├── style.py  clean.py  p_temporal.py  p_spatial.py
│   ├── p_categorical.py  p_dist.py  p_features.py
│   ├── compute_impact_score.py   # Step 2/3: Congestion Impact Score (DONE)
│   ├── build_map.py              # Step 2/3: folium impact map, raw/impact toggle (DONE)
│   ├── rank_zones.py             # Step 2/3: ranked zones + exposure-weighted windows (DONE)
│   ├── face_validity.py          # Step 2/3: face validity + month-to-month stability (DONE)
│   ├── forecast.py               # Step 7: multi-model GBM forecaster, temporal holdout (DONE)
│   ├── forecast_tune.py          # Step 7: tuning/ensemble check (no material gain) (DONE)
│   └── patrol_optimizer.py       # Step 5: patrol optimizer + Pareto (DONE)
├── outputs/                      # generated: parkpulse_map.html, top_zones.md/.csv, face_validity.md
└── web/                          # Step 8: Next.js + deck.gl interactive site (DONE; deploy on Vercel)
    ├── app/ components/ lib/     #   UI; public/data/*.json from web/prepare_data.py
```

---

## 4. The data (essentials)

- **Bengaluru Traffic Police parking violations**, 298,445 records, **2023-11-10 → 2024-04-08** (151 days), all parking-relevant.
- **No traffic-flow signal** (no speeds/volumes/travel-times). `closed_datetime` & `action_taken_timestamp` are 100% null. Congestion impact is **derived** (§6) and the system is designed to fuse with a live speed feed when one exists (proxies → features, observed delay → label).
- Source CSV cleaning is done by `scripts/clean.py`. **Prefer the cleaned parquet**; only re-run cleaning if you change cleaning logic.

---

## 5. Feature table schema: `data/hex_features_res9.csv` (2,534 rows)

One row = one **H3 res-9 (~150m) hotspot cell**. Key insight: **raw aggregates (count, severity-sum, PCU-sum, impact-sum) are collinear (r 0.91–0.99)**, all just "more violations." So features split into **volume** vs **intensity**; the impact score MUST use both axes (§6).

**Volume / persistence:** `n_violations`, `log_n`, `n_days_active`, `active_days_ratio` (active days / 151), `vio_per_active_day`.
**Intensity / composition** (per-violation; decoupled from volume): `mean_obstruct_w` (0.5–1.0 carriageway-blocking), `mean_pcu`, `heavy_share`, `main_road_share`, `crossing_signal_share`, `footpath_share`, `junction_share`.
**Temporal:** `peak_share`, `am_peak_share`, `pm_peak_share`, `night_share`, `weekend_share`, `mean_expo` (exogenous road-utilization weight 0–1), `hour_entropy` (low = predictable window), `modal_hour` (recommended enforcement hour).
**Workflow/quality:** `approval_rate`, `scita_share`.
**Impact proxy:** `impact_sum`, `impact_per_violation`.
**Spatial/labels:** `lat`, `lon`, `dom_station`, `dom_violation`, `h3_9`.

Record-level parquet adds: parsed `vt_list`, all the `f_*` violation flags, `vehicle_class`, `obstruct_w`, `pcu`, `expo_weight`, `is_peak`/`is_weekend`/`is_approved`, `h3_8/9/10`, `created_ist`, `hour/dow/month`, etc.

---

## 6. CRITICAL CONSTRAINTS: read before any modeling

These are EDA-confirmed. Violating them produces wrong or misleading results.

1. **Time is UTC → always work in IST.** Raw `created_datetime` is UTC; Bengaluru is +5:30. The cleaned data is already IST-converted. Any new time logic must stay IST, or "rush hour" is 5.5h wrong.
2. **Counts are wildly overdispersed (var/mean = 743) and zero-inflated (88.7% of hex×day = 0).** Model counts with **Negative Binomial / Tweedie / LightGBM, NEVER Poisson.** For "will it flare" framings, binary classification is cleaner.
3. **Transform counts for linear/GLM/distance/clustering** (skew 11.1 → 0.12 via Box-Cox λ≈−0.21, ≈ log1p). **Tree ensembles need no transform** (scale-invariant).
4. **Spatial concentration is extreme (Gini 0.84; top 5% of ~65m cells = 64% of violations).** **Score by percentile/rank, not raw magnitude.** Primary unit H3 **res-9** (~150m); fine hotspots res-10 (~65m).
5. **Volume ≠ intensity (collinear raw aggregates).** The impact score MUST multiply a **volume axis** by an independent **intensity axis**, or else "impact" just re-spells "count." (§6 of EDA report.)
6. **Enforcement-schedule confound.** Recorded violations ≈ (parking demand) × (patrol presence). Evidence: a daily **4–5am sweep = 15.3% of all data** (every one of 151 days), and **weekends busier than weekdays**. Consequences:
   - For the **impact score**, weight time-of-day by the **exogenous** `mean_expo` curve, **not** by observed violation-hour.
   - For the **forecaster**, the target is *"expected detections under current enforcement,"* not pure demand. State this; don't overclaim.
7. **Build the core on `approved` records.** Among *reviewed* detections, **28.7% were rejected** (likely false/contested). 42% are unreviewed (null); treat null as "unreviewed," not invalid. Report a sensitivity check on the full set.
8. **Timestamps are minute-resolution** (seconds are an anonymization artifact). **Never** compute sub-minute / inter-event timings.
9. **Coordinates are full precision (7 decimals)** → repeated exact points are **real co-location** (a chronic spot), not GPS rounding. Recurrence is signal.

---

## 7. What is and isn't ML (ground-truth reality, be honest)

- **Hotspot detection** = unsupervised (H3 aggregation / clustering + ranking). No labels needed; validate by stability + face validity.
- **Congestion Impact Score** = a **heuristic composite index. NO ground truth.** We never observe true flow degradation in this data. Do NOT claim to "validate accuracy" of impact. It *becomes* a supervised regression the day a speed feed provides labels.
- **Forecasting violations** = supervised ML with built-in ground truth (historical recorded counts = labels). Evaluate on a **temporal holdout: train Nov–Feb, test Mar–Apr.** Operationally meaningful metric = **top-k hit rate** + Spearman rank-corr; must beat a seasonal-naive baseline (same cell, same weekday, last week).
- **Detection-validity classification** = a second supervised task (`validation_status` = label, on reviewed records). Predict approved/rejected to auto-triage false detections. Standard AUC/PR. Auxiliary but real.

**Framing for the pitch:** the forecaster is the ML component with a real ground-truth eval; the impact score is an engineered index built to become supervised. Don't fake ML where there's no label.

---

## 8. Locked modeling decisions

- **Spatial unit:** H3 res-9 primary, res-10 for pinpoint. Optionally HDBSCAN for organic named zones.
- **Impact Score:** geometric mean of percentile-normalized axes (**volume × intensity × exposure × persistence**), scaled 0–100, with a per-component breakdown. Apply a **minimum-support guard** (e.g., shrink or floor cells with very few violations) so single-event flukes don't top the ranking.
- **Forecaster:** LightGBM (Tweedie/Poisson objective) or ZINB; temporal holdout; per-hex lag/rolling features.
- **Validation of score:** face validity vs known Bengaluru commercial/parking-problem areas; month-to-month stability; approved-only vs all sensitivity.

---

## 9. Tech stack

Python 3.10+. Core: pandas, numpy, h3 (**v4 API**: `h3.latlng_to_cell(lat,lon,res)`), scipy, scikit-learn. Modeling: **lightgbm**, optionally statsmodels (NB/ZINB). Maps: **folium** (or pydeck/keplergl). Plots: matplotlib + seaborn (shared style in `scripts/style.py`). Dashboard: a static **Next.js** app (`web/`). Optional enrichment: **geopandas + osmnx** (you CAN fetch OSM/Overpass locally, which upgrades road-criticality from text-proxy to real highway class).

---

## 10. Conventions & gotchas

- **Reproducibility:** scripts read from `data/`, write generated artifacts to `data/` or `outputs/`. Don't overwrite the cleaned parquet/feature CSV. Keep functions importable; guard runners with `if __name__ == "__main__":`.
- **No magic re-cleaning:** start from `hex_features_res9.csv` for scoring; from `parkpulse_clean_records.parquet` if you need record-level detail.
- **GitHub 100MB limit:** `data/violations.csv` is ~105MB, so **gitignore it** (it exceeds the limit and it's the provided data anyway). The parquet (17MB) and feature CSV (0.8MB) are fine to commit. Suggested `.gitignore`:
  ```
  data/violations.csv
  __pycache__/
  *.pyc
  .ipynb_checkpoints/
  outputs/*.html      # optional, if large
  .env
  ```
- **Submission packaging:** "Source Code" upload is ≤50MB; keep the committed repo lean. Large data goes in the "Custom Attachment" slot, not the code zip.
- **Plotting:** reuse `scripts/style.py` palette for visual consistency across EDA + product.
- **Honesty in outputs:** wherever impact or forecasts appear, surface the derivation/limitations (no flow data; enforcement confound). Judges reward it.

---

## 11. Setup & run

```bash
pip install -r requirements.txt
# place raw data as data/violations.csv if re-running cleaning (else skip)
python scripts/clean.py            # -> data/parkpulse_clean_records.parquet (already provided)
python scripts/p_features.py       # -> data/hex_features_res9.csv (already provided)
# NEXT:
python scripts/compute_impact_score.py   # to build (see KICKOFF_STEP2.md)
python scripts/build_map.py              # to build
```

---

## 12. Submission deliverables (keep in view)

Title · Description · Theme (selected) · Snapshots · **Video URL** · **Presentation/deck** · **Demo Link** (Vercel/Netlify) · **Repository URL** · **Source Code zip (≤50MB)** · **Instructions to Run** · Custom Attachment. Full tracker in `ParkPulse_Project_Master.md` §4.

---

## 13. Do NOT
- Use Poisson for counts; use raw counts in linear/clustering steps without transform.
- Let the impact score collapse into raw violation count (use the intensity axis).
- Read recorded-violation hour as parking demand (enforcement confound).
- Include rejected/unreviewed records in the high-confidence core without flagging.
- Compute sub-minute timings; commit the raw CSV; claim to have "validated" impact against ground truth that doesn't exist.
- Build a CV detector (wrong theme).
