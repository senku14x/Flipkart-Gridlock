# ParkPulse — Forecaster: tuning & ensembling (honest follow-up)

Methodology: hyperparameters searched and models selected on the **validation tail** (Feb); the Mar–Apr **test set is reported once**. Metric = coverage@20.

| Variant | Spearman | cov@20 | cov@50 | prec@20 | RMSE | TweedieDev |
|---|--:|--:|--:|--:|--:|--:|
| LightGBM (default) | 0.432 | 0.348 | 0.510 | 0.499 | 5.60 | 3.454 |
| LightGBM (tuned by val cov@20) | 0.428 | 0.349 | 0.512 | 0.495 | 5.62 | 3.463 |
| LightGBM (tuned by val deviance) | 0.429 | 0.346 | 0.506 | 0.492 | 5.61 | 3.464 |
| Ensemble — mean of 4 GBMs | 0.431 | 0.349 | 0.509 | 0.497 | 5.59 | 3.439 |
| Ensemble — per-day rank-mean | 0.430 | 0.350 | 0.509 | 0.499 | 7.68 | 7.329 |

Best is **Ensemble — per-day rank-mean** at cov@20=0.350 (+0.002 vs default 0.348). That is within noise — **tuning/ensembling do not materially help**; the base-rate ceiling holds. Keeping the default model.

_Note: the per-day rank-mean edges cov@20 but outputs **ranks, not counts** (hence its large RMSE/deviance) — unusable for "how many". The mean-ensemble matches it on ranking with the best calibration (deviance 3.44), but the edge over one LightGBM is within noise and not worth shipping four models._

Best hyperparameters (by val cov@20): `{'num_leaves': 31, 'min_child_samples': 80, 'learning_rate': 0.03, 'colsample_bytree': 0.6, 'subsample': 1.0, 'reg_lambda': 5.0, 'reg_alpha': 5.0, 'max_depth': 8}`.

_Consistent with the feature ablation: on this base-rate-dominated, patrol-confounded series the limit is the data, not the model. The shipped model (`forecast_model.pkl`) stays the default LightGBM._
