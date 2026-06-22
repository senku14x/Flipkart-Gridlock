# ParkPulse: Project Master Doc
### Gridlock Hackathon 2.0 (Flipkart) · Round 2 (Prototype Phase)

> **How to use this doc.** This is the single source of truth for the project. If you start a fresh chat, paste this whole file in and say *"continue from [step X]"*. It contains the problem framing, the dataset facts, the full solution design, every submission requirement with its status, the build roadmap, and the key technical decisions. Update the **Status** markers as we go.
>
> **Deep data profile:** see the companion **ParkPulse_EDA_Report.md** (+ `eda_plots/`, `hex_features_res9.csv`, `parkpulse_clean_records.parquet`).
>
> **Note:** Data does not persist across chats or sandbox resets. When resuming, re-upload the dataset zip (`jan_to_may_police_violation_anonymized791b166_csv.zip`).

**Status legend:** [x] Done · in progress · [ ] Not started · Needs your action (outside the sandbox)

---

## 0. Snapshot

| | |
|---|---|
| **Working name** | ParkPulse *(change anytime)* |
| **Theme (selected)** | Poor Visibility on Parking-Induced Congestion |
| **One-line pitch** | AI-driven parking intelligence that finds chronic illegal-parking hotspots, scores each by its drag on traffic flow, and tells enforcement *where and when* to deploy for the most congestion relief per patrol-hour. |
| **Round window** | Jun 15 – Jun 21, 2026 |
| **Team size** | 1 |

---

## 1. Problem Statement (framed)

**Official statement: "Poor Visibility on Parking-Induced Congestion"**
On-street illegal parking and spillover near commercial areas, metro stations, and events choke carriageways and intersections. It's hard today because enforcement is patrol-based and reactive, there's no heatmap of parking violations vs. congestion impact, and it's difficult to prioritize enforcement zones.

> *Direction:* How can AI-driven parking intelligence detect illegal parking hotspots **and quantify their impact on traffic flow** to enable targeted enforcement?

**Our framing (three nested problems, most teams stop at #1):**
1. **Detect** illegal/spillover parking hotspots: *where & when.*
2. **Quantify impact** on traffic flow: turn "a violation" into "a violation that costs X." **This is the differentiator.**
3. **Prioritize:** rank enforcement zones so limited patrols go where they relieve the most congestion.

**Pain point → our answer (the pitch maps 1:1):**
- *Reactive patrols:* predictive forecasting of where/when violations will spike.
- *No impact heatmap:* impact-weighted hotspot map (not raw counts).
- *Can't prioritize:* ranked zones + recommended enforcement windows + patrol optimizer.

---

## 2. The Dataset

**Source:** Bengaluru Traffic Police parking violations (anonymized). ~**298,450** records, **Nov 9 2023 → Apr 8 2024** (note: filename says "jan to may"; actual span is Nov–Apr, April partial). All coordinates within Bengaluru (lat 12.80–13.29, lon 77.44–77.77).

**Schema (24 cols):**
- **Spatial:** `latitude`, `longitude`, `location` (free text), `junction_name` (named junction for ~50%; else "No Junction"), `police_station` (54 stations).
- **Temporal:** `created_datetime` (the event time, **in UTC**), plus `modified_datetime`. *(`closed_datetime` and `action_taken_timestamp` are 100% null, no enforcement-response signal.)*
- **Violation:** `violation_type` (JSON array, ~1.17 types/record), `offence_code` (parallel codes).
- **Vehicle:** `vehicle_type`.
- **Workflow/admin:** `validation_status` (approved / rejected / created1 / processing / duplicate; 42% null), `data_sent_to_scita` (T/F), `device_id`, `created_by_id`, `center_code`.

**Key signal found:**
- **Overwhelmingly parking:** WRONG PARKING (165K), NO PARKING (139K), PARKING IN A MAIN ROAD (24K), ON FOOTPATH (3.8K), NEAR BUSTOP/SCHOOL/HOSPITAL (2.4K), DOUBLE PARKING (2K), NEAR ROAD CROSSING (1.7K), NEAR TRAFFIC LIGHT/ZEBRA (525)…
- **Strong spatial recurrence:** ~89K records share an *exact* coordinate with another → violations stack at the same spots (hotspot signal).
- **Commercial/junction coverage:** 168 named junctions; busiest stations (Upparpet, Shivajinagar, Malleshwaram, HAL Old Airport, City Market) = the dense commercial/market zones the brief calls out.
- **Vehicle mix:** Scooter (95K), Car (89K), Motorcycle (41K), Passenger Auto (38K), then Maxi-cab/LGV/bus/tanker.

**The defining gap:** there is **no traffic-flow data** (no speeds, volumes, or travel times). So "impact on traffic flow" must be **derived**, not looked up. (See §3: this is the design opening, not a weakness.)

---

## 3. Solution Design

### Thesis
*From reactive patrol to predictive, impact-prioritized enforcement.*

### The three differentiators (what wins judging)
1. **Congestion Impact Score:** physically grounded, survives questioning.
2. **Fusion-ready architecture:** designed to plug into a live speed feed the day one exists; the data gap becomes a roadmap.
3. **Face-validity proof:** if our top-scored hotspots match Bengaluru's known chokepoints, that is evidence the score captures real impact without flow data.

### Pipeline (end to end)

**a) Data foundation.** Parse timestamps + **convert UTC→IST** (Bengaluru = +5:30; without this, rush-hour analysis is 5.5 hrs wrong). Explode multi-violation records; map violation types to obstruction classes; map vehicle types to **PCU (Passenger Car Unit)** footprint weights (a double-parked bus >> a scooter). Build the core on **approved/high-confidence** records; show a sensitivity check (a rejected detection may be a false positive).

**b) Hotspot detection (the "where").** **H3 hexagons (~150m)** for stable heatmap units + **HDBSCAN** clustering for organically-shaped named zones. Compute **persistence** per hotspot (how many distinct days, which consistent hours) to separate structural chokepoints from sporadic noise.

**c) Congestion Impact Score (0–100, the heart).** Geometric mean of physically-motivated factors (so a hotspot must be bad on several axes to top the list):
- **Obstruction severity:** from violation type (main road / double / near-crossing / near-signal rank high; footpath low for *vehicle* flow).
- **Vehicle footprint:** PCU-weighted.
- **Road importance:** proxy from location-text tokens (Main/Ring/Cross/Flyover), the "main road" tag, junction adjacency, local density. *(Upgrade path: true OSM highway-class + betweenness centrality, needs an OSM extract, see §6.)*
- **Junction proximity:** near junctions, impact is super-linear (queue spillback, blocked turns).
- **Temporal exposure:** weight each violation by how full the road typically is at that hour (Bengaluru diurnal curve: AM ~8–11, PM ~5–9). *This is how we inject "traffic flow" without a feed: weight by when roads are at capacity.*
- **Persistence & simultaneity:** chronic recurrence + multiple vehicles blocking the same stretch (effective lane loss).

  *Framing:* the score is a **model awaiting labels**: today these are features; in production, observed speed-drop is the label and weights are learned by regression. Not arbitrary.

**d) Prioritization & action (the ops payload).**
- **Ranked enforcement zones:** each with score + breakdown, dominant violation/vehicle type, and a **recommended enforcement window** (peak hours, IST).
- **Patrol optimizer:** greedy coverage ("deploy N patrols to these zones at these hours, cover X% of total estimated impact").
- **Pareto story:** top ~20 hotspots = small share of locations, large share of impact.

**e) Prediction (stretch, included).** Forecast hex×hour violation intensity (gradient-boosted / Poisson; seasonal-naive baseline), evaluated on a **temporal holdout** (train Nov–Feb, test Mar–Apr). Output: "next Fri 6–8pm these cells spike, pre-position now." Direct antidote to "reactive."

**f) Product.** Interactive map centerpiece: impact-weighted hex heatmap with a **raw-count to impact-weighted toggle** (the contrast sells it), time-of-day slider, junction/zone layers, plus dashboard (ranked-zone table, hour×day heatmap, breakdowns, patrol view, KPI cards).

### Proposed tech stack
Python (pandas, `h3`, `hdbscan`/scikit-learn, plotly/folium or kepler.gl for maps) for the reproducible pipeline; a polished self-contained web artifact (or Streamlit app) for the demo.

---

## 4. Submission Requirements Tracker

| # | Field | Req'd | What it needs | Plan / who | Status |
|---|-------|:---:|---|---|:---:|
| 1 | **Title** | - | Clear descriptive title | Recommended below | in progress |
| 2 | **Description** | - | Project write-up (formatting/links ok) | Draft v0 below; refine after build | in progress |
| 3 | **Theme** | - | Pick one | "Poor Visibility on Parking-Induced Congestion" | done |
| 4 | Snapshots | — | Images of project (JPG/PNG ≤3MB) | Dashboard screenshots after build | [ ] |
| 5 | **Video URL** | - | Demo/pitch video link | Record 2–3 min; host YouTube/Loom/Drive | you |
| 6 | **Presentation** | - | Pitch deck (.pdf/.pptx… ≤50MB) | I'll build the deck | [ ] |
| 7 | **Demo Link** | - | Working demo/prototype link | Needs hosting (options in §5) | you + me |
| 8 | **Repository URL** | - | GitHub/Bitbucket repo | You create repo; I prep contents | you |
| 9 | **Source Code** | - | Zip/apk (≤50MB) | I'll package pipeline + app | [ ] |
| 10 | **Instructions to Run** | - | Steps for reviewers | I'll write the README | [ ] |
| 11 | Custom Attachment | — | Any extra file | Optional (e.g. methodology PDF) | [ ] |

**What I can produce directly in here:** title, description, pitch deck, source-code zip, run instructions, dashboard screenshots, methodology doc.
**What needs you (outside sandbox):** create the GitHub repo, host the demo somewhere reachable, record + upload the video.

### Recommended Title (field #1)
**Primary:** *ParkPulse: AI Parking Intelligence for Impact-Prioritized Enforcement*
Alternates: *"ParkPulse: From Parking Violations to a Congestion-Impact Map"* · *"Beyond the Heatmap: Scoring Parking Hotspots by Their Traffic-Flow Impact"*

### Draft Description v0 (field #2, refine after build)
> Illegal and spillover parking chokes Bengaluru's carriageways and junctions, but enforcement is reactive and blind to *which* violations actually hurt traffic. **ParkPulse** turns 298K+ real parking-violation records into a decision tool. It detects chronic hotspots (H3 + density clustering), then computes a **Congestion Impact Score** for each, fusing obstruction severity, vehicle footprint (PCU), road importance, junction proximity, peak-hour exposure, and persistence, so enforcement sees an *impact-weighted* map rather than raw counts. It outputs ranked enforcement zones, recommended deployment windows, a patrol optimizer, and a forecast of where violations will spike next. The scoring is designed to fuse with a live speed feed the moment one is available, so it works standalone today and improves with richer data in deployment.

---

## 5. Demo Hosting Options (for field #7)
- **Static interactive HTML** (map + dashboard in one file): host on **GitHub Pages / Netlify / Vercel** (free, instant).
- **Streamlit app:** **Streamlit Community Cloud** (free, links straight from the GitHub repo).
- Fallback: a recorded walkthrough as the "demo," with the static HTML attached as Custom Attachment.
> Decision pending; see §7.

---

## 6. Key Technical Decisions & Constraints
- **UTC→IST** conversion is mandatory before any time analysis.
- **`validation_status`:** core analysis on approved/high-confidence; sensitivity check on the full set.
- **Vehicle weighting** via PCU equivalents (traffic-engineering standard).
- **Hotspots:** H3 (heatmap/scoring) + HDBSCAN (named zones).
- **Impact Score:** geometric mean of 6 factors; transparent breakdown; framed as a model awaiting flow-feed labels.
- **No OSM in this sandbox** (network is allow-listed; Overpass/OSM unreachable). Road importance uses in-data proxies. **Upgrade if you can supply a Bengaluru road-network extract** (e.g., an OSM `.pbf`/GeoJSON of roads + junctions): enables true highway-class + betweenness centrality.
- **Prediction** evaluated on a temporal holdout (train Nov–Feb / test Mar–Apr).

**EDA-confirmed decisions (2026-06-18):**
- **Enforcement-schedule confound** is real (daily 4–5am sweep = 15.3% of data; weekends busier than weekdays). Recorded violations ≈ demand × patrol presence. Weight impact by an *exogenous* congestion curve, and frame predictions as "expected detections under current enforcement," not pure demand.
- **Counts are wildly overdispersed (var/mean = 743) and zero-inflated (88.7% of hex×day = 0).** Model counts with **Negative Binomial / Tweedie / LightGBM**, never Poisson.
- **Box-Cox λ ≈ −0.21** (skew 11.1 → 0.12): log/Box-Cox transform counts for any linear/GLM/distance/clustering step; trees need none.
- **Extreme spatial concentration (Gini 0.84; top 5% of cells = 64% of violations):** score by **percentile/rank**; primary spatial unit **H3 res-9 (~150m)**, fine hotspots **res-10 (~65m)**.
- **Raw aggregates are collinear (r 0.91–0.99):** impact score must separate **volume × intensity** (intensity = per-violation composition), else it collapses to raw count.
- **Build on `approved` records** (28.7% of *reviewed* detections were rejected); sensitivity-check on full set.

---

## 7. Open Decisions (need your input)
1. **Final project name:** keep "ParkPulse" or pick another?
2. **OSM/road extract:** can you provide one (sharpens the impact score), or proceed with in-data proxies?
3. **Demo hosting:** GitHub Pages / Netlify / Vercel / Streamlit Cloud?
4. **Video:** your plan for recording (screen-capture walkthrough vs. narrated deck)?
5. **Repo:** your GitHub username/org so run instructions match.

---

## 8. Build Roadmap

Each step produces something showable, so we're never far from a demo.

- [x] **0. Data profiling + full EDA:** quality, temporal/spatial/categorical/distributional analysis, 12 plots, feature table, modeling playbook. Output: `ParkPulse_EDA_Report.md`.
- [x] **1. Foundation & cleaning:** done inside EDA (`parkpulse_clean_records.parquet`: UTC→IST, exploded violations, PCU + obstruction weights, hex features). Ready to reuse.
- [x] **2. Hotspot detection + impact-weighted heatmap:** `scripts/build_map.py` → `outputs/parkpulse_map.html` (raw/impact toggle).
- [x] **3. Congestion Impact Score:** `scripts/compute_impact_score.py` → `data/hex_scored.csv`. Geometric mean of volume × intensity × exposure × persistence; EB minimum-support guard; Spearman(impact, count)=0.56 (decoupled).
- [x] **4. Ranked zones + enforcement windows:** `scripts/rank_zones.py` → `outputs/top_zones.md/.csv`. Exposure-weighted windows (confound-safe).
- [x] **5. Patrol optimizer + Pareto analysis:** `scripts/patrol_optimizer.py` → `outputs/patrol_plan.md/.csv`, `pareto.png`. Greedy max-coverage (beat = cell + H3 ring): 20 beats cover 53% of exposure-weighted impact vs 47% naive; Pareto (top 1% of cells = 35%, 58 cells = 50%); forecaster-driven next-day plan (14/20 beats shared with static).
- [x] **6. Face-validity check vs known Bengaluru chokepoints:** `scripts/face_validity.py`. 20/20 top zones face-valid; month-to-month rank ρ≈0.75, each-month-vs-full ρ≈0.86.
- [x] **7. Prediction layer** (temporal holdout): `scripts/forecast.py`. Multi-model GBM bake-off (LightGBM/XGBoost/CatBoost/HistGBM, Tweedie/Poisson) on 906 hotspot cells; beats seasonal-naive (+36% coverage@20) and dominates on calibration. Best model saved to `outputs/forecast_model.pkl`.
- [x] **8. Packaged dashboard / demo artifact:** `web/`, custom **Next.js (static export) + deck.gl + Recharts** site (not Streamlit: can't run on Vercel). Impact map (raw/impact toggle, hover breakdown), ranked zones, forecaster (bake-off + ablation), live patrol optimizer (N-beats slider), methodology. Fully static (precomputed JSON), deploys to Vercel with no backend/tokens.
- [ ] **9. Deliverables:** deck, README, source zip, screenshots, description final.

---

## 9. Change Log
- *2026-06-18:* Doc created. Problem framed, data profiled (§2), solution designed (§3), submission fields mapped (§4). Next: Step 1 (foundation & cleaning).
- *2026-06-18:* **Extensive EDA complete.** Cleaning + feature engineering done (Steps 0–1). Produced `ParkPulse_EDA_Report.md`, 12 figures, `hex_features_res9.csv`, `parkpulse_clean_records.parquet`. Key learnings folded into §6 (enforcement confound, NB/zero-inflation, Box-Cox, Gini concentration, volume×intensity, approved-only). Next: Step 2/3, hotspot map + Congestion Impact Score on the existing feature table.
- *2026-06-21:* **Step 2/3 built (Steps 2, 3, 4, 6).** Repo scaffolded into the canonical layout. `compute_impact_score.py` → `data/hex_scored.csv` (geometric-mean impact score, EB minimum-support guard, Spearman vs count = 0.56). `build_map.py` → `outputs/parkpulse_map.html` (folium, raw/impact toggle). `rank_zones.py` → `outputs/top_zones.md/.csv` (top-30 zones, exposure-weighted enforcement windows that neutralise the 4–5am sweep confound). `face_validity.py` → `outputs/face_validity.md` (20/20 top zones on known cores; month-to-month rank stability ρ≈0.75). Next: Step 5 (patrol optimizer + Pareto), Step 7 (forecaster), Step 8 (dashboard).
- *2026-06-21:* **Step 7 built (forecaster).** `scripts/forecast.py`: leakage-safe hex×day panel (causal lags/rolling + train-only static features), four GBM models (LightGBM/XGBoost/CatBoost/HistGBM, Tweedie/Poisson) on a strict temporal holdout (train Nov–Feb, test Mar–Apr, 906 cells). All four beat the three baselines; LightGBM best (coverage@20 0.348, +36% vs seasonal-naive, 72% of oracle) and Tweedie deviance 3.45 vs 90. Base-rate (`tr_mean`) dominates importance, so location is stable and the four libraries tie within ~0.5pt. Outputs `forecast_metrics.md/.csv`, `forecast_eval.png`, `forecast_model.pkl/.json`, `forecast_importance.csv`. Next: Step 5 (patrol optimizer), Step 8 (dashboard).
- *2026-06-21:* **Forecaster feature-engineering exploration.** Engineered 29 extra features in four leakage-safe groups (per-cell×weekday profile, momentum/EWMA, cyclical + holiday/Ramadan flags, spatial spillover) and ran a marginal ablation. Result: none beat the base 24-feature set. The per-cell×weekday profile actively hurts (cov@20 0.348→0.332: ~16 samples per cell×weekday, high-variance, overfits); momentum/spatial neutral; holidays slightly negative. Shipped the leaner base model; documented that the ceiling-lifters are data (live speed feed, events calendar, patrol roster), not more features. Ablation table + chart in `forecast_metrics.md` / `forecast_eval.png`.
- *2026-06-21:* **Forecaster tuning + ensemble check** (`scripts/forecast_tune.py` → `outputs/forecast_tuning.md`). 28-config LightGBM random search (selected on the Feb val tail) and two 4-model ensembles (prediction-mean, per-day rank-mean) evaluated once on the Mar–Apr test. Best is +0.002 cov@20 over the default, within noise. Confirms the data ceiling; keeping the single default LightGBM as the shipped model. (Mean-ensemble offers a negligible calibration edge, not worth shipping four models.)
- *2026-06-21:* **Step 8 built (interactive web app).** `web/`: a custom **Next.js 16 (static export) + deck.gl 9 (`H3HexagonLayer`) + Recharts** site, Tailwind v4, dark theme. Decision: not Streamlit (needs a persistent server and can't run on Vercel; a static frontend is trivially CDN-scalable with all compute precomputed). Sections: hero/KPIs, GPU impact map (raw/impact toggle + hover breakdown), ranked zones, forecaster (bake-off bars + ablation), live patrol optimizer (N-beats slider driving the greedy-vs-naive coverage chart + deployment plan), methodology. Data via `web/prepare_data.py` → `web/public/data/*.json` (reuses `patrol_optimizer.py` so the site matches the repo). Verified: builds static + renders headless with zero runtime errors (deck.gl on React 19). Deploy: Vercel, Root Directory = `web`, no env/tokens. Next: deploy + Step 9 deliverables (deck, video, screenshots, source zip).
- *2026-06-21:* **Decision-support upgrades built.** Four additions that deepen the prioritization beyond average impact. (1) `congestion_cost.py` calibrates impact_sum into vehicle-hours and rupees of delay (~Rs 5.2 cr/yr base, low/base/high band; worst 20 cells = 31%, 58 cells = half), leading with the assumption-robust concentration. (2) `detection_validity.py`, a second supervised model (separate from the forecaster) predicting rejection on review: ROC-AUC 0.758 / PR-AUC 0.632 on a stratified holdout, top-20% flag catches 43% of rejections at 64% precision; excludes data_sent_to_scita to avoid leakage. (3) `emerging_hotspots.py` trends each cell's SHARE of citywide volume over the four full months (detrends the enforcement ramp): 227 rising, 103 high-impact-and-rising. (4) `enrich_osm.py`, optional run-locally OSM enrichment (nearest road class + nearby POIs); downstream is graceful if absent. Dropped an hour-by-hour schedule: pm_peak_share is ~0 citywide (enforcement rarely works evenings), so observed hours reflect patrol shifts, not congestion. All surfaced in `web/` (cost, trends, triage sections; cost + trend in the map hover).
- *2026-06-21:* **Enforcement-gap analysis + patrol ROI built.** `enforcement_gap.py`: weighting recorded violations (a proxy for enforcement effort) by their impact unit shows the 4-5am sweep is 15.3% of effort but 4.0% of impact, the night window 33.7% effort / 7.9% impact, and peak hours 28.8% effort / 50.1% impact, which is the case for impact-weighted prioritization. New web "visibility gap" section (effort-vs-impact bars per window). The optimizer slider now also reports rupees/day of delay relieved (coverage x total daily cost; 20 patrols ~Rs 77k/day), turning it into an enforcement-ROI tool.
- *2026-06-21:* **Impact-score robustness built.** `score_robustness.py`: re-weights the four axes across 2,000 random weightings (each varied up to 3x in relative importance) and measures ranking drift. Median Spearman 0.97 vs the shipped score, top-20 retains 18/20; arithmetic vs geometric mean still 0.86; no single axis dominates (drop-one Spearman > 0.82). Answers "why those weights?". Figure `fig-robustness.png`; surfaced in the LaTeX/solution doc, the deck, and the web methodology card.
- *2026-06-21:* **OSM cross-check made turnkey.** `enrich_osm.py` now also computes k-sampled node betweenness centrality (how critical each road is to flow) alongside the highway class + POIs. New `osm_validate.py` correlates the impact score (built WITHOUT the road network) against real OSM road criticality, betweenness, and nearby congestion-generators, the independent validation that retires the no-ground-truth critique. Framed as a cross-check, not blended into the score, so an independent agreement is the evidence and the committed numbers are undisturbed. Validator logic verified on a synthetic hex_osm.csv; the user runs the two commands locally (network) to get the real numbers + `fig-osm.png`.
- *2026-06-21:* **Step 5 built (patrol optimizer + Pareto).** `scripts/patrol_optimizer.py` → `outputs/patrol_plan.md/.csv`, `pareto.png`. Pareto on the exposure-weighted additive impact mass (`impact_sum`): top 1% of cells = 35% of impact, 58 cells (2.3%) = 50%, 269 = 80%. Greedy max-coverage optimizer where each patrol works a beat (cell + H3 ring-1): because the worst cells clump in commercial cores, greedy spreads beats and **20 beats cover 53% vs 47% for naive top-N** (+6 pts, same fleet). Each beat carries its exposure-weighted enforcement window. Bonus: a forecaster-driven next-day plan (predicted violations × impact/violation) that shares 14/20 beats with the static plan and reallocates the rest to predicted surges, demonstrating the reactive-to-predictive shift operationally. Next: Step 8 (dashboard).
