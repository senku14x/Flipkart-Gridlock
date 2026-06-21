# ParkPulse: detection-validity model

A separate supervised model that predicts whether a detection will be rejected on review, from the report's own attributes (vehicle, location, time, violation type). It auto-triages probable false or contested reports so patrols are not sent to chase them. Trained on reviewed records only, with a stratified hold-out.

- Reviewed records: 165,154 (train 123,865 / test 41,289). Rejection base rate: **30.1%**.
- **ROC-AUC 0.758**, **PR-AUC 0.632** (vs 0.301 for a no-skill model). Real structure, not a base rate.

## Triage: flag the most-suspect reports

| Flag the top | Precision (are really rejected) | Recall (of all rejections) | Lift |
|---|--:|--:|--:|
| 10% most-suspect | 80% | 27% | 2.7x |
| 20% most-suspect | 64% | 43% | 2.1x |
| 30% most-suspect | 56% | 56% | 1.9x |

## Top features (gain)

- `longitude`
- `latitude`
- `police_station`
- `dow`
- `hour`
- `expo_weight`
- `month`
- `pcu`
- `obstruct_w`
- `vehicle_class`