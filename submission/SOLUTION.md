# ParkPulse solution document

**Gridlock Hackathon 2.0 (Flipkart), Round 2.** Theme: *Poor Visibility on Parking-Induced Congestion*.

**Team Spectres:** Kavya Mahajan, Aarav Harshvardhan, Souhardyo Dasgupta, Vishesh Gupta.

**One line:** ParkPulse reads 298,445 real Bengaluru parking-violation records and scores every hotspot by how much it slows traffic, then tells enforcement where, when, and at what cost to act, and how many patrols it takes to fix it.

---

## 1. The problem

Bengaluru's traffic police already log thousands of parking violations a day. The gap the theme names is *visibility*: the feed shows where tickets get written, not where parking actually chokes traffic, and the two are not the same place. A quiet lane that catches a daily pre-dawn sweep can rack up more tickets than the junction that jams a main road every evening, yet the junction is the one that matters. Enforcement is patrol-based and reactive, there is no impact-weighted heatmap, and there is no way to prioritize.

We frame it as three nested problems, where most stop at the first:

1. **Detect** chronic illegal-parking hotspots (where and when).
2. **Quantify** each one's impact on traffic flow. This is the differentiator.
3. **Prioritize** so limited patrols go where they relieve the most congestion.

The success test we held ourselves to: a traffic officer reads the output and says *"tomorrow, send the team to these spots at these hours, because that is where parking chokes traffic worst."*

---

## 2. Why it is hard: the data

- **298,445 records**, 2023-11-10 to 2024-04-08 (151 days), 54 police stations, all parking-relevant.
- The defining gap: **there is no traffic-flow signal**. No speeds, volumes, or travel times. So "impact on traffic flow" must be *derived*, not looked up.
- An **enforcement-schedule confound**: a violation is only logged when a patrol is present. A daily 4-5am sweep is 15.3% of all records, and weekends are busier than weekdays. So recorded violations are roughly parking demand times patrol presence, and the recorded hour reflects patrol shifts, not congestion.

These two facts shape every modeling decision below. We treat them as the opening, not a weakness: the impact score is built to plug into a live speed feed the day one exists.

---

## 3. The approach

A pipeline that moves from *reactive patrol* to *predictive, impact-prioritized enforcement*, in three layers:

- **See:** an impact-weighted hotspot map and a ranked shortlist of zones.
- **Understand:** what the congestion costs, where effort is misallocated, and which spots are getting worse.
- **Act:** a forecaster, a false-report triage model, and a patrol optimizer that outputs a deployment plan with a rupee ROI.

Everything runs on the cleaned data with no live feed, and is designed to absorb one when available.

---

## 4. How it works

### 4.1 Data foundation
Timestamps converted UTC to IST (without this, rush-hour analysis is 5.5 hours wrong). Multi-violation records exploded; violation types mapped to obstruction weights; vehicle types mapped to PCU (passenger-car-unit) footprints. The core is built on `approved` records, with a sensitivity check on the full set. Aggregated to **H3 res-9 cells (~150 m)**, the primary enforcement unit (2,534 hotspot cells), with res-10 (~65 m) for pinpoint work.

### 4.2 Congestion Impact Score (0-100)
A geometric mean of four percentile-ranked axes, so a cell must be bad on several dimensions to rank high:

`score = 100 × (volume × intensity × exposure × persistence) ^ (1/4)`

- **Volume**: how many violations (with an empirical-Bayes shrink so single-event flukes do not top the ranking).
- **Intensity**: how obstructive the typical violation is (carriageway blocking, vehicle footprint, main-road and junction adjacency).
- **Exposure**: how busy the road normally is, from an *exogenous* hour-of-day utilization curve, not the recorded violation hour (this is how we inject "traffic flow" without a feed, and dodge the confound).
- **Persistence**: how chronic the spot is (active days).

The score is built to *disagree* with a raw violation count: their rank correlation is **0.56**, which is the point. Spatial concentration is extreme (Gini 0.84): the **top 1% of cells carry 35% of impact**, and 58 cells carry half.

### 4.3 The enforcement gap
Recorded violations double as a map of enforcement effort. Weighting each by its impact unit (obstruction × PCU × utilization) exposes the misallocation:

| Time window | Share of effort | Share of impact |
|---|--:|--:|
| Pre-dawn sweep (4-5am) | 15.3% | 4.0% |
| Night (12-5am) | 33.7% | 7.9% |
| Peak-exposure hours | 28.8% | 50.1% |

A third of logged effort lands when roads are empty. ParkPulse redirects it to the peak-hour chokepoints.

### 4.4 Ranked enforcement zones
The top 30 cells by impact, each with its dominant violation, the streets involved, and an exposure-weighted enforcement window. Where and when, not just where. Validated by **face validity** (20 of the top 20 are known commercial or market chokepoints) and **month-to-month stability** (rank correlation ~0.75 consecutive, ~0.86 against the full period).

### 4.5 Congestion cost
Turns the score into a number. Calibrating the physical delay-potential (`impact_sum`) into vehicle-hours, then rupees via a value of time, with a low/base/high band: about **574 vehicle-hours/day, ~Rs 5.2 crore/year** (base), and the worst 20 cells carry 31% of it. A first-order estimate, with the assumption-robust concentration as the headline.

### 4.6 Emerging hotspots
The score ranks where things are bad on average; this flags where they are getting worse. We trend each cell's *share* of citywide volume over the four full months, which detrends the citywide enforcement ramp. **227 cells are rising**, and 103 are both high-impact and rising: the early-warning set.

### 4.7 Forecasting (the ML with real ground truth)
Predicts next-day violation intensity per cell on a strict temporal holdout (train Nov-Feb, test Mar-Apr). A bake-off across the gradient-boosting family (LightGBM, XGBoost, CatBoost, HistGBM, Tweedie/Poisson) picks LightGBM (Tweedie). It beats the required seasonal-naive baseline by **36% on coverage@20** (0.257 to 0.348) and dominates on calibration (Tweedie deviance 3.45 vs 90), capturing 72% of the oracle ceiling. We tested 29 extra engineered features and tuning/ensembling; none beat the base 24-feature set. The honest read: base rate explains much of the "where", and the ceiling is the data, not the model.

### 4.8 False-detection triage (a second supervised model)
About a third of reviewed reports are rejected on review. A separate classifier predicts which, from the report's own attributes, with **ROC-AUC 0.758 / PR-AUC 0.632** on a stratified holdout (base rate 30%). Flag the top 20% most-suspect reports and you catch **43% of all rejections at 64% precision**, so patrols are not sent to chase contested or false reports. Location dominates the signal.

### 4.9 Patrol optimizer + ROI
A greedy max-coverage optimizer assigns N patrol beats (each beat is a cell plus its H3 ring) to maximize the impact covered. Because the worst cells cluster, **20 beats cover 53% of citywide impact vs 47% for a naive top-N pick**. The slider also reports the rupee ROI: 20 patrols relieve roughly **Rs 77k/day** of delay. A forecaster-driven next-day variant shares 14 of 20 beats with the static plan.

---

### Is the score robust?
A fair question is whether the ranking is an artefact of the equal weighting. It is not. Across 2,000 random re-weightings of the four axes (each varied up to 3x in relative importance), the ranking holds at a median Spearman of 0.97 against the shipped score, and the top-20 zones retain 18 of 20 on average. Switching from a geometric to an arithmetic mean still correlates at 0.86, and no single axis dominates (dropping any one keeps Spearman above 0.82). The ranking reflects the data's structure, not a hand-tuned weighting.

### Does it agree with the real city?
The score uses no road network and no land use, only the violation feed, so we can hold it up against real OpenStreetMap geography it never saw (`scripts/osm_validate.py`). It rediscovers the city's commercial cores. Sort all 2,534 cells into ten equal impact bands and the share sitting next to a market, shopfront, or transit stop climbs steadily from **34% in the lowest band to 62% in the highest**. The top-30 hotspots sit next to a marketplace 17% of the time versus 2% city-wide (an ~8x enrichment), and proximity to these congestion-generators tracks impact about twice as strongly as road class (Spearman 0.23 vs 0.12). The weak alignment with arterial class is itself the finding: parking does not choke the wide arterials and flyovers, it chokes the narrow commercial streets feeding them, so a score built to find parking-induced congestion *should* point away from the arterials. Built with none of this data, the score lines up with the geography that drives curbside demand, the closest thing to ground truth without a speed feed.

## 5. Results at a glance

| What | Result |
|---|---|
| Hotspot cells scored | 2,534 (H3 res-9) |
| Impact vs raw count | rank corr 0.56 (deliberately decoupled) |
| Concentration | top 1% of cells = 35% of impact; 58 cells = 50% |
| Enforcement gap | night = 34% of effort, 8% of impact |
| Estimated delay cost | ~574 veh-hr/day, ~Rs 5.2 cr/yr (band) |
| Emerging | 227 rising; 103 high-impact and rising |
| Forecaster | +36% cov@20 vs seasonal-naive; 72% of oracle |
| False-report triage | ROC-AUC 0.758; top-20% flag catches 43% |
| Patrol optimizer | 20 beats = 53% impact, ~Rs 77k/day relieved |
| Validation | face validity 20/20; stability rho 0.75-0.86 |
| OSM cross-check | commercial proximity 34% to 62% by impact band; market 8x |

---

## 6. Honesty and limitations

- **No ground truth for impact.** The score is an engineered index, not a measurement, and we never claim accuracy for it. We validate it four ways: face validity, month-to-month stability, a robustness check on the weights, and an independent OpenStreetMap cross-check (`scripts/osm_validate.py`). The cross-check is the strongest of these: the score, built without any road network or land use, independently rediscovers the city's commercial cores (proximity to markets, shops, and transit climbs from 34% to 62% across impact bands), while correctly *not* tracking arterial road class, because parking chokes commercial streets, not flyovers.
- **The enforcement confound.** We weight by exogenous exposure, never by recorded hour, and we state that the forecaster predicts *recorded detections under current enforcement*, not pure demand.
- **The data can't see the evening.** Evening violations are near-absent because enforcement rarely works evenings, so we do not build an hour-by-hour schedule from the recorded hour.
- **Fusion-ready.** The moment a live speed feed, real road network, events calendar, or patrol roster exists, those factors become inputs and measured slowdown becomes the label. The data gap is a roadmap.

---

## 7. Architecture and tech

- **Pipeline:** Python (pandas, numpy, h3 v4, scikit-learn, lightgbm). Each step reads committed artifacts and writes to `data/` or `outputs/`.
- **Web app:** Next.js (static export) + deck.gl (`H3HexagonLayer`) + Recharts + Tailwind. Fully static: it reads precomputed JSON, so it runs on a CDN with no backend and no API keys, and cannot fall over under load.
- **Optional enrichment:** `scripts/enrich_osm.py` adds the real road class and nearby congestion-generators from OpenStreetMap (run locally; geo APIs are blocked in CI). Everything downstream is graceful if it is absent.

---

## 8. Impact and roadmap

Today, ParkPulse gives enforcement the prioritization they are missing: a ranked, costed, where-and-when plan, plus the ROI of acting on it. With one more data feed it goes from a careful estimate to a measured, learning system: plug in live speeds for a true impact label, the OSM road graph for flow-criticality, and patrol rosters to de-bias the confound.

---

## 9. Links and how to run

- **Demo:** https://flipkart-gridlock-gamma.vercel.app/
- **Repository:** https://github.com/senku14x/Flipkart-Gridlock
- **Run:** see `submission/SUBMISSION.md` (web app + the Python pipeline, reproducible from the committed data).
