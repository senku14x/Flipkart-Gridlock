# ParkPulse: Violation Forecaster (models + feature engineering)

Genuine supervised ML, **real ground truth**, strict **temporal holdout** (train 2023-11-10 → 2024-02-29, test 2024-03-01 → 2024-04-08) over **906 recurring hotspot cells** (≥20 train violations).

> Note: Target = *expected recorded detections under current enforcement*, not pure demand (patrol-confounded, CLAUDE.md §6.6).

## Feature engineering: the base set wins

We engineered **29 extra features** in four leakage-safe groups (per-cell × weekday profile, momentum/EWMA, cyclical + holiday/Ramadan flags, and spatial spillover) and tested each on the holdout (LightGBM). Result: **none beat the 24-feature base set, and the granular weekly group hurts.** `cov@20` = share of a held-out day's violations in the model's top-20 cells.

| Feature set | # feats | cov@20 | Spearman | TweedieDev |
|---|--:|--:|--:|--:|
| base (shipped) | 24 | 0.348 | 0.432 | 3.454 |
| base+weekly | 28 | 0.332 | 0.401 | 4.489 |
| base+momentum | 36 | 0.349 | 0.430 | 3.445 |
| base+calendar | 32 | 0.343 | 0.428 | 3.482 |
| base+spatial | 29 | 0.347 | 0.431 | 3.445 |
| base+all | 53 | 0.335 | 0.402 | 4.412 |

`base` is best (coverage@20 0.348). Adding the **per-cell × day-of-week profile** drops it to 0.332 (deviance 3.45 → 4.49): each cell×weekday has only ~16 training samples, so it is a high-variance estimate the model overfits. Momentum and spatial are neutral (±0.001); holiday flags are slightly negative. **More features add variance, not signal**: a textbook bias-variance outcome on a base-rate-dominated, patrol-confounded series, so we ship the leaner 24-feature model.

_To push past this ceiling the levers are **data, not features**: a live speed feed (the missing label that turns this into true congestion forecasting), an events/attendance calendar, and patrol-roster data to de-confound enforcement. All are flagged as data asks in the EDA report._

## Model bake-off (base feature set)

_Oracle (perfect-foresight) coverage@20 = 0.481; random ≈ 0.022._

| Model | Spearman | cov@10 | **cov@20** | cov@50 | prec@20 | RMSE | TweedieDev |
|---|--:|--:|--:|--:|--:|--:|--:|
| LightGBM (Tweedie) [best] | 0.432 | 0.244 | **0.348** | 0.510 | 0.499 | 5.60 | 3.454 |
| HistGBM (Poisson) | 0.429 | 0.242 | 0.347 | 0.504 | 0.490 | 5.95 | 3.502 |
| CatBoost (Tweedie) | 0.431 | 0.247 | 0.346 | 0.509 | 0.491 | 5.60 | 3.435 |
| XGBoost (Tweedie) | 0.428 | 0.243 | 0.346 | 0.507 | 0.490 | 5.60 | 3.463 |
| Cell train-mean | 0.405 | 0.234 | 0.338 | 0.491 | 0.478 | 5.80 | 3.677 |
| Rolling-7d mean | 0.427 | 0.235 | 0.329 | 0.494 | 0.465 | 5.89 | 16.846 |
| Seasonal-naive (lag 7d) | 0.340 | 0.188 | 0.257 | 0.402 | 0.342 | 7.68 | 90.286 |

**Best: LightGBM (Tweedie).** Beats every baseline on every metric. vs the *required* seasonal-naive: **+36%** coverage@20 (0.257 → 0.348); vs the strong cell base-rate: +3% (Spearman 0.405 → 0.432). Captures 72% of the oracle ceiling. Calibration is the clearest win: Tweedie deviance 3.45 vs 90 (seasonal-naive).

The four GBM libraries land within ~0.5 pt of each other. With this signal the **data, not the framework, is the ceiling**. LightGBM is chosen on a thin margin.

### Top features (permutation importance)

| Feature | Importance |
|---|--:|
| `tr_mean` | 3.446 |
| `roll7_mean` | 0.146 |
| `y_lag1` | 0.092 |
| `tr_std` | 0.067 |
| `dow` | 0.058 |
| `expw_mean` | 0.057 |
| `roll14_mean` | 0.030 |
| `dow_mean4` | 0.025 |
| `tr_expo` | 0.014 |
| `y_lag14` | 0.010 |

All features are causal (backward-looking) or train-only (no leakage).

---
*`scripts/forecast.py`. Best model saved to `outputs/forecast_model.pkl` (+ `.json`). The impact score remains an engineered index awaiting a flow label.*
