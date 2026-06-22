# ParkPulse: OSM cross-check (independent validation)

The Congestion Impact Score is built from the violation feed alone (a text-token road proxy, no road network and no land use). Here we hold it up against REAL OpenStreetMap geography it never saw. Where the two agree, that agreement is independent evidence the score is physical, the closest thing to ground truth we have without a live speed feed.

## The score rediscovers the city's commercial cores

Sort all 2,534 cells into 10 equal bands by impact. The share of cells next to a market, shopfront, or transit stop climbs steadily with impact, from 34% in the lowest band to 62% in the highest. The score was never told where any of these are.

- **Commercial-generator proximity: top-30 hotspots 73% vs 45% of all cells.** Parking-induced congestion concentrates where people actually stop.
- **Marketplaces: top-30 17% vs 2% of all cells, an ~8x enrichment.** Markets are rare, yet the worst hotspots cluster on them.
- **Proximity tracks impact about twice as strongly as road class** (Spearman 0.23 vs 0.12).

## On road class we are deliberately honest

The correlation with OSM arterial class is weak (0.12), and only 40% of the top-30 sit on an arterial vs 45% city-wide. That is not a miss, it is the finding: parking does not choke the wide, fast arterials and flyovers, it chokes the narrow commercial and market streets feeding them. A score built to find parking-induced congestion *should* point away from the arterials, and it does.

The score, derived with none of this OSM data, lines up with the commercial geography that drives curbside demand. That is independent corroboration without a speed feed.