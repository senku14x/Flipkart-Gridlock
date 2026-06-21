# ParkPulse

**Gridlock Hackathon 2.0 (Round 2).** Theme: *Poor Visibility on Parking-Induced Congestion*.

Parking intelligence that finds chronic illegal-parking hotspots, scores each by its drag on
traffic flow, and tells enforcement **where and when** to deploy for the most congestion relief
per patrol-hour.

> **Decision-support, not detection.** The input is an already-detected violation feed; ParkPulse is
> the intelligence layer on top: hotspot detection → a **Congestion Impact Score** → ranked
> enforcement zones with recommended time windows.

---

## Status

- **EDA, cleaning, and feature engineering complete.** See `ParkPulse_EDA_Report.md`.
- **Artifacts committed.** Cleaned record table plus the 2,534-cell modeling table (see *The data* below).
- **Step 2/3 complete.** Congestion Impact Score, impact-weighted map (raw/impact toggle),
  ranked enforcement zones with exposure-weighted windows, and a face-validity and stability check.
- **Forecaster (Step 7) complete.** Multi-model GBM bake-off (LightGBM / XGBoost / CatBoost /
  HistGBM, Tweedie/Poisson) on a temporal holdout. It beats the seasonal-naive baseline, with a
  large calibration improvement. Best model, metrics, and figure saved.
- **Patrol optimizer and Pareto (Step 5) complete.** Greedy max-coverage deployment plan (20 beats
  cover 53% of citywide impact), Pareto concentration, and a forecaster-driven next-day plan.
- **Interactive web app (Step 8) complete.** A custom **Next.js + deck.gl** site (`web/`) that ties
  the impact map, ranked zones, forecaster, and live patrol optimizer into one demo. Fully static
  (precomputed JSON), deploys to Vercel with no backend.
- **Decision-support upgrades complete.** A congestion-cost estimate (vehicle-hours and rupees,
  ~Rs 5.2 cr/year; worst 20 cells = 31%), emerging-hotspot detection (cells escalating faster than
  the city), a second ML model that flags likely-false reports (ROC-AUC 0.758), and an optional OSM
  road-criticality enrichment. All surfaced in the web app.

Full roadmap, design, and submission tracker: **`ParkPulse_Project_Master.md`** (source of truth).

---

## Repository layout

```
.
├── CLAUDE.md                      # project context for Claude Code (read first)
├── README.md                     # this file
├── ParkPulse_Project_Master.md   # source of truth: problem, design, roadmap, submission tracker
├── ParkPulse_EDA_Report.md       # full data profile + modeling playbook
├── KICKOFF_STEP2.md              # the next build task (impact score + map)
├── requirements.txt              # Python deps
├── .gitignore                    # ignores the ~105MB raw violations.csv (GitHub 100MB limit)
├── data/
│   ├── parkpulse_clean_records.parquet   # 298,445 cleaned records × 44 cols (IST, exploded
│   │                                     #   violations, PCU + obstruction weights, H3 indices)
│   ├── hex_features_res9.csv             # 2,534 H3 res-9 hotspot cells × 28 features (modeling table)
│   └── violations.csv                    # raw ~105MB, GITIGNORED, not in repo (provided dataset)
├── eda_plots/                    # 12 EDA figures (01–12; index in EDA report §11)
├── scripts/                      # Python pipeline
│   ├── style.py                  # shared matplotlib palette
│   ├── clean.py                  # raw CSV → cleaned records (cleaning + feature engineering)
│   ├── p_temporal.py · p_spatial.py · p_categorical.py · p_dist.py   # EDA stats + figures 01–10
│   ├── p_features.py             # builds the hex feature table + figures 11–12
│   ├── compute_impact_score.py   # Step 2/3: Congestion Impact Score → data/hex_scored.csv
│   ├── build_map.py              # Step 2/3: folium impact map (raw/impact toggle)
│   ├── rank_zones.py             # Step 2/3: top enforcement zones + exposure-weighted windows
│   ├── face_validity.py          # Step 2/3: face validity + month-to-month stability
│   ├── forecast.py               # Step 7: multi-model GBM forecaster (temporal holdout)
│   ├── forecast_tune.py          # Step 7: tuning/ensemble check (no material gain)
│   ├── patrol_optimizer.py       # Step 5: patrol optimizer + Pareto
│   ├── congestion_cost.py        # delay cost (vehicle-hours + rupees)
│   ├── detection_validity.py     # false-detection classifier (2nd ML model)
│   ├── emerging_hotspots.py      # cells rising faster than the city
│   └── enrich_osm.py             # optional: real road class + POIs (run locally)
└── outputs/                      # generated artifacts
    ├── parkpulse_map.html        #   interactive impact map
    ├── top_zones.md / .csv       #   ranked enforcement zones (ops payload)
    ├── zone_enrichment.csv       #   per-cell location + recommended window
    ├── face_validity.md          #   corroboration report
    ├── forecast_metrics.md/.csv  #   forecaster model comparison
    ├── forecast_eval.png         #   coverage curves + feature importance
    ├── forecast_model.pkl/.json  #   best trained model + config
    ├── patrol_plan.md / .csv     #   deployment plan (where + when)
    └── pareto.png                #   impact concentration + patrol coverage
└── web/                          # Next.js + deck.gl interactive site (Step 8)
    ├── app/ · components/ · lib/ #   UI (impact map, zones, forecaster, optimizer)
    ├── public/data/*.json        #   precomputed app data (from web/prepare_data.py)
    └── prepare_data.py           #   exports committed artifacts -> JSON for the app
```

---

## Setup

```bash
pip install -r requirements.txt   # Python 3.10+
```

## The data (already provided, nothing to re-run)

| Artifact | Grain | Use |
|---|---|---|
| `data/hex_features_res9.csv` | one H3 res-9 (~150 m) cell | **primary modeling table** for scoring |
| `data/parkpulse_clean_records.parquet` | one violation event | record-level detail (e.g. month splits) |

The raw `violations.csv` (~105 MB) is **not** committed. It exceeds GitHub's 100 MB limit and is the
provided dataset. You only need it to re-run cleaning, which isn't required since the cleaned
artifacts above are committed.

## Run

**Step 2/3: Congestion Impact Score, map, zones, validation** (reproducible from the committed
feature table; run from the repo root):
```bash
python scripts/compute_impact_score.py   # data/hex_features_res9.csv → data/hex_scored.csv (+ prints)
python scripts/build_map.py              # → outputs/parkpulse_map.html (raw/impact toggle)
python scripts/rank_zones.py             # → outputs/top_zones.md / .csv, zone_enrichment.csv
python scripts/face_validity.py          # → outputs/face_validity.md (face validity + stability)
```

**Step 7: Violation forecaster** (supervised ML, temporal holdout; trains LightGBM /
XGBoost / CatBoost / HistGBM on CPU in well under a minute):
```bash
python scripts/forecast.py               # → outputs/forecast_metrics.md, forecast_eval.png, forecast_model.pkl
```

**Step 5: Patrol optimizer + Pareto** (greedy deployment plan; reads the impact score, optionally
the forecaster for a next-day plan):
```bash
python scripts/patrol_optimizer.py       # → outputs/patrol_plan.md / .csv, pareto.png
```

**Regenerate the EDA artifacts (optional):** `scripts/` holds the pipeline that produced the committed
data and figures: `clean.py` → `p_temporal.py` → `p_spatial.py` → `p_categorical.py` → `p_dist.py` →
`p_features.py` (run from inside `scripts/`). Re-running requires the raw `violations.csv`.

---

## Key facts (detail in the EDA report)

- 298,445 parking-violation records · Bengaluru · 2023-11-10 → 2024-04-08 (151 days).
- **No traffic-flow data** → congestion impact is *derived*: **volume × intensity × exposure × persistence**.
- **Enforcement-schedule confound:** daily 4–5am sweep (15.3%), weekends busier than weekdays →
  recorded violations ≈ demand × patrol presence. Weight time by *exogenous* exposure, not observed hour.
- **Gini 0.84:** top 5% of ~65 m cells = 64% of violations → rank/percentile-based prioritization.
- Counts overdispersed (var/mean = 743) + zero-inflated (88.7%) → Negative Binomial / Tweedie / LightGBM, never Poisson.
- Box-Cox λ ≈ −0.21 (skew 11.1 → 0.12) → log-transform counts for any linear/distance/clustering step; trees need none.

---

## Documentation map

| File | What's in it |
|---|---|
| `CLAUDE.md` | Project context + hard constraints (**read before writing code**) |
| `ParkPulse_Project_Master.md` | Problem framing, solution design, submission tracker, roadmap |
| `ParkPulse_EDA_Report.md` | Full data profile + modeling playbook (read §3 & §9 first) |
| `KICKOFF_STEP2.md` | The current build task: impact score + map + face validity |
