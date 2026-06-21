# ParkPulse — Gridlock Hackathon 2.0 (Round 2)
### Theme: *Poor Visibility on Parking-Induced Congestion*

AI-driven parking intelligence that finds chronic illegal-parking hotspots, scores each by its
drag on traffic flow, and tells enforcement **where and when** to deploy for the most congestion
relief per patrol-hour.

> **Decision-support, not detection.** The input is an already-detected violation feed; ParkPulse is
> the intelligence layer on top — hotspot detection → a transparent **Congestion Impact Score** →
> ranked enforcement zones with recommended time windows.

---

## Status

- ✅ **EDA + cleaning + feature engineering complete** — see `ParkPulse_EDA_Report.md`.
- ✅ **Artifacts committed** — cleaned record table + 2,534-cell modeling table (see *The data* below).
- ▶ **Next — Step 2/3:** Congestion Impact Score + impact-weighted map + face-validity check
  (spec in `KICKOFF_STEP2.md`).

Full roadmap, design, and submission tracker: **`ParkPulse_Project_Master.md`** (source of truth).

---

## Repository layout

```
.
├── CLAUDE.md                      # project context for Claude Code (read first)
├── README.md                     # this file
├── ParkPulse_Project_Master.md   # SOURCE OF TRUTH — problem, design, roadmap, submission tracker
├── ParkPulse_EDA_Report.md       # full data profile + modeling playbook
├── KICKOFF_STEP2.md              # the next build task (impact score + map)
├── requirements.txt              # Python deps
├── .gitignore                    # ignores the ~105MB raw violations.csv (GitHub 100MB limit)
├── data/
│   ├── parkpulse_clean_records.parquet   # 298,445 cleaned records × 44 cols (IST, exploded
│   │                                     #   violations, PCU + obstruction weights, H3 indices)
│   ├── hex_features_res9.csv             # 2,534 H3 res-9 hotspot cells × 28 features (modeling table)
│   └── violations.csv                    # raw ~105MB — GITIGNORED, not in repo (provided dataset)
├── eda_plots/                    # 12 EDA figures (01–12; index in EDA report §11)
├── scripts/                      # Python pipeline
│   ├── style.py                  # shared matplotlib palette
│   ├── clean.py                  # raw CSV → cleaned records (cleaning + feature engineering)
│   ├── p_temporal.py · p_spatial.py · p_categorical.py · p_dist.py   # EDA stats + figures 01–10
│   ├── p_features.py             # builds the hex feature table + figures 11–12
│   ├── compute_impact_score.py   # Step 2/3 — TO BUILD (Congestion Impact Score)
│   └── build_map.py              # Step 2/3 — TO BUILD (folium impact map)
└── outputs/                      # generated maps, scored tables, reports
```

---

## Setup

```bash
pip install -r requirements.txt   # Python 3.10+
```

## The data (already provided — nothing to re-run)

| Artifact | Grain | Use |
|---|---|---|
| `data/hex_features_res9.csv` | one H3 res-9 (~150 m) cell | **primary modeling table** for scoring |
| `data/parkpulse_clean_records.parquet` | one violation event | record-level detail (e.g. month splits) |

The raw `violations.csv` (~105 MB) is **not** committed — it exceeds GitHub's 100 MB limit and is the
provided dataset. You only need it to re-run cleaning, which isn't required since the cleaned
artifacts above are committed.

## Run

**Next stage — Congestion Impact Score + map (Step 2/3, see `KICKOFF_STEP2.md`):**
```bash
python scripts/compute_impact_score.py   # data/hex_features_res9.csv → data/hex_scored.csv
python scripts/build_map.py              # → outputs/parkpulse_map.html (impact ↔ raw-count toggle)
```

**Regenerate the EDA artifacts (optional):** `scripts/` holds the pipeline that produced the committed
data and figures — `clean.py` → `p_temporal.py` → `p_spatial.py` → `p_categorical.py` → `p_dist.py` →
`p_features.py` (run from inside `scripts/`). Re-running requires the raw `violations.csv`.

---

## Key facts (detail in the EDA report)

- 298,445 parking-violation records · Bengaluru · 2023-11-10 → 2024-04-08 (151 days).
- **No traffic-flow data** → congestion impact is *derived*: **volume × intensity × exposure × persistence**.
- **Enforcement-schedule confound:** daily 4–5am sweep (15.3%), weekends busier than weekdays →
  recorded violations ≈ demand × patrol presence. Weight time by *exogenous* exposure, not observed hour.
- **Gini 0.84** — top 5% of ~65 m cells = 64% of violations → rank/percentile-based prioritization.
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
