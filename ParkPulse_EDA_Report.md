# ParkPulse — Exploratory Data Analysis & Modeling Scope
### Gridlock Hackathon 2.0 · "Poor Visibility on Parking-Induced Congestion"

> Companion to **ParkPulse_Project_Master.md**. This is the deep data profile: every property of the dataset, the plots, the engineered features, and — most importantly — what each finding *means for the models*. Read §3 and §9 first if short on time. Figures are in `eda_plots/`. Cleaned data: `parkpulse_clean_records.parquet`. Modeling table: `hex_features_res9.csv`.

---

## 1. Dataset at a glance

| Property | Value |
|---|---|
| Records | **298,445** (5 null-timestamp rows dropped from 298,450) |
| Raw columns | 24 |
| Time span (IST) | **2023-11-10 → 2024-04-08**, 151 distinct days (Nov & Apr partial) |
| Geography | Bengaluru — lat 12.80–13.29, lon 77.44–77.77 |
| Grain | one row = one detected violation event (can list multiple violation types) |
| Unit economics | 54 police stations · 169 junction labels · ~178K unique GPS points · ~6.8K hotspot cells (≈65m) |

**Bottom line:** rich spatio-temporal event data, overwhelmingly parking, extremely spatially concentrated — but with **no traffic-flow signal** and a strong **enforcement-schedule confound** (see §3) that dictates how we model and what we can claim.

---

## 2. Data quality & integrity

| Column group | Finding | Action |
|---|---|---|
| `description`, `closed_datetime`, `action_taken_timestamp` | **100% null** | Drop. No enforcement-outcome or resolution signal exists. |
| `validation_status` + `updated_*` + `validation_timestamp` | **42% null** (unprocessed/in-flight) | Treat null as "unreviewed," not "invalid." |
| `data_sent_to_scita_timestamp` | 85.9% null | Use the boolean `data_sent_to_scita` instead. |
| `center_code` | 3.8% null; `location` 1% null | Minor; impute/ignore. |
| **Validation outcomes** | Among *reviewed* records, **28.7% were rejected** (overall: 38.7% approved, 16.7% rejected, 42% null) | **Build the core on `approved`**; report a sensitivity check on the full set. ~1 in 3 reviewed detections is a false/contested positive. |
| **Timestamp resolution** | `created_datetime` is **minute-resolution with a fixed seconds artifact** (94,417 unique values; seconds repeat). `modified_datetime` is unique to the microsecond. | Analyze time at **hour/minute** only. **Do not** compute inter-event times or anything sub-minute. |
| Processing lag (`modified−created`) | median 0.3h, p90 18.5h, **314 (0.1%) negative** | Clip negatives to 0; lag is a weak "review latency" proxy, not enforcement response. |
| Coordinates | **7 decimal places (full precision)**; ~89K rows share an *exact* point with another | Recurrence is **real co-location**, not GPS rounding → strong hotspot signal. |

---

## 3. ⚠️ The caveat that changes everything: enforcement-schedule confound

This is the most important thing the team must internalize before modeling.

**The data records when officers *logged* violations — which tracks patrol shifts, not organic parking demand or congestion.** Three findings prove it:

1. **A systematic 4–5am spike.** 45,705 records (**15.3% of all data**) land at 4–5am IST, spread across **all 151 days** (the top 5 dates are only 6% of it), concentrated at HAL Old Airport, Upparpet, Malleshwaram, Vijayanagara. That's a daily pre-dawn enforcement sweep, not a glitch and not commuter parking.
2. **Weekends are *busier* than weekdays** (Sun 50,160 vs Mon 34,680; weekend daily avg = 113% of weekday). Commuter congestion peaks on weekdays — so this volume is **commercial/market-driven**, and partly reflects when enforcement deploys.
3. **The recorded "peak" is mid-morning (9–11)** — see `eda_plots/02` & `03` — which mixes real market-hour parking pressure with patrol timing.

**Implications:**
- **Recorded violations ≈ (parking demand) × (enforcement presence).** A hotspot being "hot" can mean heavy violation *or* heavy patrolling. The "when to enforce" recommendation derived purely from recorded times is partly circular.
- For the **Congestion Impact Score**, weight time-of-day by an **exogenous** congestion curve (our `expo_weight`), *not* by observed violation-hour — otherwise we bake the patrol schedule into the impact.
- For the **prediction layer**, frame the target honestly as *"expected detections given current enforcement behavior."* If we want true parking-pressure, we'd need to de-bias by patrol coverage (we don't have a patrol-effort field, so flag this as a known limitation / future data ask).
- This is also a **pitch strength**: it shows ParkPulse understands the difference between *observed enforcement* and *underlying demand* — most teams won't.

---

## 4. Temporal properties  ·  `eda_plots/01–03`

- **Daily volume** (`01`): rises Nov→Jan, dips Feb, recovers Mar; clear weekly seasonality; Apr truncated at the 8th. No major gaps.
- **Hour of day** (`02`, IST): dominant 9–11am block; the anomalous 4–5am enforcement bulge; relatively quiet afternoons/evenings.
- **Day of week** (`02`): **Sunday > Saturday > weekdays**; Monday lowest.
- **Hour × DoW heatmap** (`03`): the actionable view — **weekend mornings (Sat/Sun 9–11)** are the hottest cells (Sun 10:00 ≈ 6,363), plus the daily 4–5am band.
- **Predictability:** per-cell `hour_entropy` ranges 0–4.0 (median 1.9). Many hotspots fire in a **narrow, repeatable window** (low entropy) → ideal for *scheduled* enforcement; others are diffuse.

---

## 5. Spatial properties  ·  `eda_plots/04–06`

- **Density** (`04`): violations blanket the city but spike hard in the core/commercial corridors.
- **Extreme concentration** (`05`): **Gini = 0.84** over ~65m cells. **Top 1% of cells = 34% of violations; top 5% = 64%; top 10% = 77%.** This *is* the "prioritize enforcement" thesis — a small set of locations carries most of the problem.
- **Hotspot cell counts:** 6,805 at H3-10 (~65m), 2,534 at H3-9 (~150m), 776 at H3-8 (~460m).
- **Stations** (`05`): Upparpet, Shivajinagar, Malleshwaram, HAL Old Airport, City Market lead — dense commercial/market zones, matching the brief.
- **Top recurring addresses** (`06`): a handful of specific stretches dominate (the chronic chokepoints).
- **Junctions:** 50.4% of records are tagged to a named junction → strong, ready-made link to intersections where parking spillover hurts flow most.

---

## 6. Categorical properties & relationships  ·  `eda_plots/07–08`

- **Violation mix** (`07`): WRONG PARKING (165K) + NO PARKING (139K) dominate; the high-impact tags are rarer but matter — MAIN ROAD (24K), FOOTPATH (3.8K), BUSSTOP/SCHOOL/HOSPITAL (2.4K), DOUBLE (2K), ROAD CROSSING (1.7K), TRAFFIC-LIGHT/ZEBRA (525). **13.4%** of records carry >1 type (avg 1.17).
- **Vehicle mix** (`07`): by class — **2W 46.2%, 4W-light 38.0%, 3W 13.7%, HEAVY 2.1%.** Two-wheelers dominate by count but are low-footprint; HEAVY is rare but high-impact (PCU up to 3.5–4.0).
- **Co-occurrence** (`08`, left): which violations appear together (e.g., main-road/crossing/double tend to co-tag) — useful for a composite "obstruction" feature.
- **Vehicle × violation** (`08`, right): composition differs by vehicle class (e.g., heavy vehicles skew toward main-road/footpath) — supports class-aware severity.

---

## 7. Distributional properties & transforms (modeling-critical)  ·  `eda_plots/09–10`

Aggregating to hotspot cells (H3-10), violation count per cell:

| Property | Value | Modeling consequence |
|---|---|---|
| mean / var | 43.9 / 32,601 | — |
| **Dispersion (var/mean)** | **743** | **Poisson is invalid → Negative Binomial** for counts. |
| Skewness, raw | **11.14** | Raw counts unusable in linear/distance methods. |
| Skewness, log1p | 1.05 | Big improvement. |
| **Skewness, Box-Cox (λ=−0.21)** | **0.12** (near-normal) | λ≈0 ⇒ a (near-)log transform is right; Box-Cox marginally best. |
| Shape | heavy-tailed, **power-law-like** rank-frequency (`10`) | Use **rank/percentile-based scoring**, not raw magnitudes. |
| Prediction target sparsity | **88.7% of hex×day cells are zero** | Target is **zero-inflated** → ZINB / hurdle / Tweedie, or tree model with appropriate objective. |

**Transform rule of thumb:** apply `log1p` or Box-Cox to counts for any **linear model, GLM, PCA, or distance/clustering** step; **tree ensembles (LightGBM/XGBoost) are scale-invariant** and need no transform.

---

## 8. Engineered features — data dictionary

Two tables produced: record-level (`parkpulse_clean_records.parquet`, 298K rows) and the **modeling table `hex_features_res9.csv`** (2,534 hotspot cells × 28 features). Key insight from `eda_plots/11`: the **raw aggregates (count, severity-sum, PCU-sum, impact-sum) are collinear (r 0.91–0.99)** — they're all "more violations." So features are split into **volume** vs **intensity** so both axes carry independent signal (see the quadrant plot `eda_plots/12`).

**Volume / persistence**
- `n_violations`, `log_n` — size of hotspot (median 11, max 12,123; use `log_n`).
- `n_days_active`, `active_days_ratio` — chronicity (max 151 = active *every* day).
- `vio_per_active_day` — recurrence intensity when active (median 2, max 80).

**Intensity / composition** *(decoupled from volume — the "quality" of a hotspot)*
- `mean_obstruct_w` — avg carriageway-blocking severity (0.5–1.0).
- `mean_pcu`, `heavy_share` — vehicle footprint / heavy-vehicle fraction.
- `main_road_share`, `crossing_signal_share`, `footpath_share` — violation-type composition.
- `junction_share` — fraction at a named junction (intersection exposure).

**Temporal**
- `peak_share`, `am_peak_share`, `pm_peak_share`, `night_share`, `weekend_share` — when it fires.
- `mean_expo` — exogenous road-utilization weight (for impact).
- `hour_entropy` — temporal concentration (low = predictable window).
- `modal_hour` — the recommended enforcement hour.

**Workflow / quality**
- `approval_rate` — share of reviewed detections approved (data-trust signal).
- `scita_share` — share forwarded to SCITA.

**Impact (proxy)**
- `impact_sum` = Σ(obstruct × pcu × expo); `impact_per_violation` = intensity form (median 0.28, max 3.5).

**Spatial / labels**
- `lat`, `lon`, `dom_station`, `dom_violation`.

> **For the Congestion Impact Score:** combine a **volume axis** (`log_n` or Box-Cox count, × `active_days_ratio`) with an **intensity axis** (geometric blend of `mean_obstruct_w`, `heavy_share`, `main_road_share`, `junction_share`, `crossing_signal_share`) and an **exposure axis** (`mean_expo`). A geometric mean of percentile-normalized axes forces a hotspot to be bad on several dimensions to score high — and stays interpretable.

---

## 9. Modeling playbook (recommendations)

**Spatial unit.** Use **H3 res-9 (~150m)** as the primary enforcement "zone" (2,534 cells — interpretable as a street stretch) and **res-10 (~65m)** for pinpoint hotspots. Optionally run **HDBSCAN** on coordinates to name organic zones (market frontage, station approach). Given Gini 0.84, **score by percentile/rank**, and you can cover most of the problem with the top few %.

**Congestion Impact Score (unsupervised, today).** Volume × Intensity × Exposure × Persistence, geometric mean of normalized factors (see §8). Transparent breakdown per zone. Frame as a *model awaiting labels*: when a speed feed exists, observed delay = label, these become features, weights learned by regression.

**Prediction layer (where/when violations spike).**
- Target: violation count per **hex × (day or hour-bin)**. It's **overdispersed + zero-inflated** → first choice **LightGBM with Tweedie/Poisson objective** (handles sparsity, nonlinearity, no transform needed); statistical alternative **ZINB**.
- Features: temporal (hour, dow, month, is_holiday/event, **lagged & rolling per-hex counts**), spatial (hex id/embedding, `dom_station`, road proxy), composition shares.
- **Validation: temporal holdout** (train Nov–Feb, test Mar–Apr) **and** spatial block CV (don't let neighbouring hexes leak). Metric: rank-correlation of predicted vs actual hotspot intensity + top-k hit rate.
- **Honesty:** predicts *recorded detections under current enforcement* (§3), not pure demand.

**Validation of the impact score (no ground truth).** **Face validity** — check whether top-scored zones match Bengaluru's notorious chokepoints; **stability** — scores consistent across months; **sensitivity** — robust to approved-only vs all.

**Pitfalls to avoid** (all evidenced above): don't read recorded-hour as demand (enforcement confound); filter/handle rejected detections; never use sub-minute time; don't let impact score collapse into raw count (use intensity axis); don't model counts with Poisson (use NB/Tweedie); remember weekend>weekday is commercial, and the night spike is a patrol shift.

---

## 10. Open data questions / asks
- **Traffic-flow feed** (segment speeds / travel times) — the missing label; even a small/current sample enables calibration.
- **OSM road network** for Bengaluru (highway class + betweenness) — upgrades road-importance from text-proxy to physical. *(Can't fetch from this sandbox — supply an extract if available.)*
- **Patrol-effort / roster data** — would let us de-bias the enforcement confound.
- **Repeat-offender signal** — `vehicle_number` (231,890 unique of 298,445) is in the raw file; per-vehicle recurrence could be a feature (dropped from the clean table for now; easy to add).
- **Event/holiday calendar** — to explain weekend and seasonal spikes for the predictor.

---

## 11. Figure index (`eda_plots/`)
1. `01_temporal_daily.png` — daily volume, 7-day avg, weekends shaded
2. `02_temporal_profiles.png` — hour / day-of-week / month
3. `03_temporal_heatmap.png` — hour × day-of-week (the "when" view)
4. `04_spatial_density.png` — citywide hexbin density
5. `05_spatial_concentration.png` — Lorenz/Gini + top stations
6. `06_top_locations.png` — top recurring addresses
7. `07_categorical.png` — violation types / vehicle types / validation status
8. `08_cooccurrence.png` — violation co-occurrence + vehicle×violation
9. `09_distribution_boxcox.png` — raw vs log vs Box-Cox + Q-Q
10. `10_rank_frequency.png` — power-law rank-frequency
11. `11_feature_correlation.png` — hotspot-feature correlation map
12. `12_volume_vs_intensity.png` — volume vs intensity quadrants

## 12. Artifact manifest
- `parkpulse_clean_records.parquet` — cleaned, IST-converted, feature-engineered record table (298K × ~44).
- `hex_features_res9.csv` — hotspot-cell modeling table (2,534 × 28).
- `eda_plots/` — the 12 figures above.
- `ParkPulse_Project_Master.md` — project source of truth (problem, solution, submission tracker, roadmap).
