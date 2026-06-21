# ParkPulse: Patrol Optimizer & Pareto

From impact score to deployment: where (and when) to send a limited patrol fleet for the most congestion relief per patrol-hour. Coverage is measured on **`impact_sum`** (the exposure-weighted additive impact mass), so the 4–5am enforcement sweep barely counts.

## 1. The Pareto: a few streets carry most of the problem

Across **2534 hotspot cells**:

| Patrol target | Cells | Share of cells | Impact covered |
|---|--:|--:|--:|
| top 10 | 10 | 0.4% | **21%** |
| top 20 | 20 | 0.8% | **31%** |
| top 30 | 30 | 1.2% | **38%** |
| top 50 | 50 | 2.0% | **48%** |
| top 100 | 100 | 3.9% | **61%** |

It takes only **58 cells (2.3%)** to cover half the city's parking-congestion impact, and 269 to cover 80%. *This is the prioritisation thesis: focus patrol on these cells rather than spreading evenly.*

## 2. The optimizer: greedy beats naive

Each patrol works a **beat** (its cell + the immediate ring). Because the worst cells cluster in the same commercial cores, **greedy max-coverage spreads beats across distinct hotspots** and covers more than naively taking the top-N cells (which stack up in one cluster):

- **20 greedy beats cover 53%** of citywide impact vs 47% for naive top-20 (**+6 pts** for the same fleet).
- Diminishing returns: 10 beats: 40%, 30: 61%, 50: 71%.

### Recommended deployment: 20 patrol beats

| # | Station | Location | Window (IST) | Beat impact | Cumulative |
|--:|---|---|---|--:|--:|
| 1 | Upparpet | 5th Main Road, Kempe Gowda Circle, Gandhi  | 08:00–10:00 | 9.8% | 10% |
| 2 | Shivajinagar | Dispensary Road, Tasker Town, Shivaji Naga | 10:00–12:00 | 8.6% | 18% |
| 3 | City Market | Avenue Road, Medarpet, Nagartapete | 09:00–11:00 | 4.6% | 23% |
| 4 | Malleshwaram | 80 Feet Ring Road, Orion, Brigade Gateway, | 09:00–11:00 | 3.5% | 26% |
| 5 | Rajajinagar | 10th Cross Road, Block 1, Rajaji Nagar | 08:00–10:00 | 2.7% | 29% |
| 6 | HAL Old Airport | Outer Ring Road, Vajram Onyx, Devara Beesa | 07:00–09:00 | 2.7% | 32% |
| 7 | Shivajinagar | Meenakshi Koil Street, Shivaji Nagar | 09:00–11:00 | 2.5% | 34% |
| 8 | Halasuru Gate | Sri Narasimha Raj Wadiyar Road, Potters Co | 09:00–11:00 | 1.9% | 36% |
| 9 | Malleshwaram | Sri Venkataranga Ayangar Road, RR Palace,  | 10:00–12:00 | 1.8% | 38% |
| 10 | HAL Old Airport | Outer Ring Road, SLS Serenity Apartment, R | 10:00–12:00 | 1.8% | 40% |
| 11 | Kodigehalli | Sahakar Nagar Road, Olivia, Raintree Boule | 10:00–12:00 | 1.8% | 42% |
| 12 | Vijayanagara | Chord Road, Sindhya Sunshine Apartment, Vi | 10:00–12:00 | 1.7% | 43% |
| 13 | Mahadevapura | MBT Road, Royal Heritage, Pai Layout, Maha | 09:00–11:00 | 1.6% | 45% |
| 14 | Chikkajala | Unnamed Road, Begur Chikkanahalli | 11:00–13:00 | 1.6% | 47% |
| 15 | Malleshwaram | 15th Cross Road, Malleshwara Extension, Ma | 10:00–12:00 | 1.4% | 48% |
| 16 | K.R. Pura | MBT Road, Devasandra Junction, KR Puram | 10:00–12:00 | 1.3% | 49% |
| 17 | City Market | Kalasipalyam Main Road, Basappa Circle, VV | 09:00–11:00 | 1.2% | 50% |
| 18 | Upparpet | Y Ramachandra Road, Maharani College Junct | 08:00–10:00 | 1.1% | 52% |
| 19 | Mahadevapura | Whitefield Road, VR Mall, Dyavasandra Indu | 08:00–10:00 | 1.0% | 53% |
| 20 | Vijayanagara | Sri Sankasta Hara Ganapati Temple Road, RP | 10:00–12:00 | 0.9% | 53% |

*(Full machine-readable plan: `outputs/patrol_plan.csv`.)*

## 3. Predictive deployment: plan for 2024-04-08 (forecaster-driven)

Feeding the forecaster's predicted next-day violations (× impact per violation) into the same optimizer yields a **dynamic** plan that re-targets where impact will be *tomorrow*, not just chronically. It shares **14/20** beats with the static plan (the stable cores) and reallocates the rest to predicted surges. This is the reactive-to-predictive shift in one table.

| # | Station | Location | Window (IST) | Pred. next-day impact |
|--:|---|---|---|--:|
| 1 | Upparpet | 5th Main Road, Kempe Gowda Circle, Gandhi  | 08:00–10:00 | 21.2% |
| 2 | Shivajinagar | Dickenson Road, Sri Nagamma Devi Circle, S | 09:00–11:00 | 16.8% |
| 3 | Malleshwaram | 80 Feet Ring Road, Orion, Brigade Gateway, | 09:00–11:00 | 8.7% |
| 4 | City Market | Avenue Road, Medarpet, Nagartapete | 09:00–11:00 | 8.6% |
| 5 | Rajajinagar | 10th Cross Road, Block 1, Rajaji Nagar | 08:00–10:00 | 4.7% |
| 6 | Malleshwaram | Sri Venkataranga Ayangar Road, RR Palace,  | 10:00–12:00 | 4.3% |
| 7 | Shivajinagar | Meenakshi Koil Street, Shivaji Nagar | 09:00–11:00 | 4.2% |
| 8 | Kodigehalli | Sahakar Nagar Road, Olivia, Raintree Boule | 10:00–12:00 | 4.1% |
| 9 | Mahadevapura | MBT Road, Royal Heritage, Pai Layout, Maha | 09:00–11:00 | 3.2% |
| 10 | Mahadevapura | Whitefield Road, VR Mall, Dyavasandra Indu | 08:00–10:00 | 3.1% |
| 11 | Chikkajala | Unnamed Road, Begur Chikkanahalli | 11:00–13:00 | 3.0% |
| 12 | Halasuru Gate | Sri Narasimha Raj Wadiyar Road, Potters Co | 09:00–11:00 | 3.0% |
| 13 | K.R. Pura | MBT Road, Devasandra Junction, KR Puram | 10:00–12:00 | 2.7% |
| 14 | Malleshwaram | Sri Venkataranga Ayangar Road, Ranganathap | 09:00–11:00 | 2.2% |
| 15 | Vijayanagara | Chord Road, Sindhya Sunshine Apartment, Vi | 10:00–12:00 | 2.2% |
| 16 | Upparpet | Y Ramachandra Road, Maharani College Junct | 08:00–10:00 | 1.9% |
| 17 | HAL Old Airport | Panathur Main Road, Darshan Layout, Kadubi | 08:00–10:00 | 1.8% |
| 18 | Basavanagudi | Sri DV Gundappa Road, Gandhi Bazar Circle, | 10:00–12:00 | 1.5% |
| 19 | Upparpet | Major T Ramachandrappa Road, AT Extension, | 09:00–11:00 | 1.4% |
| 20 | Rajajinagar | 1st Main Road, Block 1R, Rajaji Nagar | 09:00–11:00 | 1.4% |

---
*`scripts/patrol_optimizer.py`. Impact is an engineered index with no traffic-flow ground truth (CLAUDE.md §7); the beat radius is a modelling assumption. Windows are exposure-weighted, not raw modal hour.*
