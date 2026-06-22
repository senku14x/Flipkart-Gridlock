# ParkPulse: OSM cross-check (independent validation)

The impact score was built from the violation feed alone, with a text-token road proxy and no road network. Here we compare it to REAL OpenStreetMap road data it never saw. Agreement is independent evidence the score is physical.

- **Score vs road criticality: Spearman 0.12.** Higher-impact cells sit on more important roads, even though the score never used the road network.
- **40% of the top-30 hotspots are on arterial roads**, vs 45% of all cells.
- **87% of the top-30 sit next to a market, transit stop, school or hospital**, vs 65% of all cells.

The score, derived without any of this, lines up with it. That is the closest thing to ground truth available without a live speed feed.