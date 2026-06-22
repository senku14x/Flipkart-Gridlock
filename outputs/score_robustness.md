# ParkPulse: impact-score robustness

The score is an equal-weighted geometric mean of four percentile-ranked axes (volume, intensity, exposure, persistence). Is the ranking an artefact of that particular weighting? We stress-test it.

Equal weights reproduce the shipped score (Spearman 1.000), as expected.

## 1. Random re-weightings (each axis varied up to 3x in relative importance)

- Across **2000 random weightings**, the ranking holds: **median Spearman 0.974** (5th percentile 0.919).
- The top-20 zones are sticky: a random weighting keeps **18 of the 20** on average (worst case 15/20), top-20 Jaccard median 0.82.

## 2. Aggregation choice

- Switching from geometric to an **arithmetic** mean still gives Spearman 0.863 against the shipped ranking. The conclusion does not hinge on the mean.

## 3. Drop or double a single axis

| Axis | Spearman if dropped | Top-20 kept if doubled |
|---|--:|--:|
| volume | 0.878 | 18/20 |
| intensity | 0.833 | 16/20 |
| exposure | 0.828 | 17/20 |
| persistence | 0.903 | 18/20 |

No single axis dominates: dropping any one still correlates strongly with the full score, and doubling any one keeps most of the top-20. The ranking reflects the data's structure, not a hand-tuned weighting.