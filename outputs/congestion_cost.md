# ParkPulse: estimated congestion cost

A first-order estimate, not a measurement. The data has no traffic-flow feed, so we cannot observe delay directly. Instead we calibrate the physical delay-potential the data does contain (`impact_sum` = the sum over each cell's violations of obstruction x PCU footprint x road utilization) into vehicle-hours, then into rupees via a value-of-time. We report a low/base/high band and lead with the relative concentration, which does not depend on the absolute calibration.

## Headline (base case)

- Recorded parking violations at these 2,534 hotspots cause an estimated **574 vehicle-hours of delay per day**.
- At a blended value of time, that is about **Rs 1.4 lakh/day** (**Rs 5.24 crore/year**).
- The worst **20 cells alone carry 31%** of that cost (~Rs 44,776/day); just **58 cells account for half**. Enforcement that targets them recovers most of the delay for a fraction of the effort.

## Sensitivity band

| Scenario | veh-hr/unit | Rs/veh-hr | Delay (veh-hr/day) | Cost/day | Cost/year |
|---|--:|--:|--:|--:|--:|
| low | 0.5 | 150 | 287 | Rs 43,033 | Rs 1.57 crore |
| base | 1.0 | 250 | 574 | Rs 1.4 lakh | Rs 5.24 crore |
| high | 2.0 | 400 | 1,148 | Rs 4.6 lakh | Rs 16.75 crore |

## Assumptions

- **Delay-potential** per violation = obstruction weight (0.5-1.0) x PCU footprint (0.5-3.5) x road utilization (0.1-1.0); summed per cell as `impact_sum`, averaged over the 151-day window for a per-day figure.
- **veh-hours per unit**: a median violation is ~0.32 units (about 0.32 veh-hr of queueing delay); a severe one ~3.5 units. Base 1.0, varied 0.5-2.0.
- **Value of time**: time plus fuel waste, blended across vehicle classes; base Rs 250/veh-hr, varied 150-400.
- Linear in utilization (a simplification: real queueing is convex near capacity, so this is conservative for the busiest roads). Covers only recorded violations, which are enforcement-limited, so the true figure is higher.

## Costliest 15 hotspots (base case)

| # | Station | Violation | Impact | Est. delay (veh-hr/day) | Est. cost/day |
|--:|---|---|--:|--:|--:|
| 1 | Upparpet | NO PARKING | 92 | 21.0 | Rs 5,243 |
| 2 | Shivajinagar | WRONG PARKING | 97 | 15.6 | Rs 3,897 |
| 3 | Shivajinagar | WRONG PARKING | 97 | 14.9 | Rs 3,728 |
| 4 | Upparpet | NO PARKING | 68 | 11.9 | Rs 2,965 |
| 5 | City Market | WRONG PARKING | 62 | 11.8 | Rs 2,948 |
| 6 | Shivajinagar | WRONG PARKING | 77 | 11.6 | Rs 2,905 |
| 7 | Upparpet | NO PARKING | 94 | 11.2 | Rs 2,806 |
| 8 | Shivajinagar | WRONG PARKING | 94 | 8.8 | Rs 2,192 |
| 9 | HAL Old Airport | NO PARKING | 56 | 8.2 | Rs 2,052 |
| 10 | HAL Old Airport | PARKING IN A MAIN ROAD | 96 | 7.5 | Rs 1,881 |
| 11 | Rajajinagar | WRONG PARKING | 92 | 7.2 | Rs 1,798 |
| 12 | Malleshwaram | WRONG PARKING | 43 | 7.1 | Rs 1,768 |
| 13 | Upparpet | WRONG PARKING | 80 | 6.6 | Rs 1,639 |
| 14 | Mahadevapura | PARKING IN A MAIN ROAD | 90 | 5.3 | Rs 1,325 |
| 15 | K.R. Pura | WRONG PARKING | 47 | 5.2 | Rs 1,293 |
