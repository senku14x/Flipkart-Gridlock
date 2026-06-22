# ParkPulse submission copy

Everything here is written to paste straight into the Gridlock submission form.
Same plain voice as the site. Swap in the video URL marked `[…]` once you have it.

---

## Title

**ParkPulse**

## Team

**Spectres:** Kavya Mahajan, Aarav Harshvardhan, Souhardyo Dasgupta, Vishesh Gupta

## One-liner / tagline

Find the parking that actually chokes traffic, and patrol it first.

## Theme

Poor Visibility on Parking-Induced Congestion

---

## Description

Bengaluru's traffic police already log thousands of parking violations a day. The
problem is that the feed only tells them where tickets get written, not where parking
actually hurts traffic. Those are two different things. A quiet lane that catches a
daily pre-dawn sweep can rack up more tickets than a junction that jams a main road
every evening, yet the junction is the one that matters.

ParkPulse closes that gap. It reads 298,445 real violation records from across the
city and turns them into a single ranked answer to one question: where, and when,
should a patrol go to relieve the most congestion?

It works in several parts:

- **A Congestion Impact Score** that rates every cell (about 150 m across) on the
  things a raw count misses: how much each violation blocks the carriageway, how busy
  that road normally is, how often the same spot reoffends, and the plain volume. The
  score disagrees with a simple violation count (they correlate only 0.56), which is
  intentional. The worst 1% of cells carry 35% of the city's impact.
- **An interactive map** where you flip between raw density and impact and watch the
  city re-rank in front of you. The spots that mostly catch pre-dawn enforcement fade,
  and the ones blocking busy roads at rush hour jump out.
- **A violation forecaster** trained on past months and tested on months it never
  saw. It beats the standard seasonal baseline by 36% on next-day hit rate, and we
  report where it does and doesn't help.
- **A patrol optimizer** that turns all of this into a deployment plan. Because the
  worst spots cluster together, 20 well-placed patrols cover 53% of the city's
  parking-induced congestion impact, against 47% if you just take the top 20.
- **A cost estimate** that converts the impact score into vehicle-hours and rupees of
  delay (about Rs 5.2 crore/year, with a sensitivity band), so the case for acting is a
  number, not just a rank, and the worst 20 cells carry 31% of it.
- **Emerging-hotspot detection** that flags the cells escalating faster than the city,
  so enforcement can act before a spot becomes entrenched.
- **A second machine-learning model** that predicts which reports are likely false
  (ROC-AUC 0.758), so patrols are sent to real problems instead of contested ones.

We are upfront about the one thing the data does not contain: actual traffic speeds.
So the impact score is a careful estimate, not a measurement, and we validate it the
honest way. The top spots are places locals already know are bad (20 of the top 20),
and the ranking holds steady month to month (rank correlation around 0.75 between
consecutive months, 0.86 against the full period). The day a live speed feed exists,
the same system trains straight into it, with measured slowdown as the target.

The whole thing ships as a fast static web app (Next.js + deck.gl) that runs on a CDN
with no backend and no API keys.

---

## Links

- **Demo:** https://flipkart-gridlock-gamma.vercel.app/
- **Repository:** https://github.com/senku14x/Flipkart-Gridlock
- **Video:** [your video URL]

---

## Instructions to run

**See the live app:** open the demo link above. Nothing to install.

**Run the web app locally:**

```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

**Reproduce the analysis (Python):**

```bash
pip install -r requirements.txt
# the cleaned data + features are already committed under data/
python scripts/compute_impact_score.py   # Congestion Impact Score -> data/hex_scored.csv
python scripts/rank_zones.py             # ranked zones + windows  -> outputs/top_zones.*
python scripts/forecast.py               # forecaster bake-off      -> outputs/forecast_*
python scripts/patrol_optimizer.py       # patrol plan + Pareto     -> outputs/patrol_plan.*
python scripts/congestion_cost.py        # delay cost estimate      -> outputs/congestion_cost.md
python scripts/detection_validity.py     # false-detection model    -> outputs/detection_metrics.*
python scripts/emerging_hotspots.py      # rising hotspots          -> outputs/emerging_hotspots.md
python scripts/enforcement_gap.py        # effort vs impact         -> outputs/enforcement_gap.md
python web/prepare_data.py               # refresh the app's JSON   -> web/public/data/*

# optional, needs network access (run on your own machine, then re-run prepare_data.py):
python scripts/enrich_osm.py             # real road class + betweenness + POIs -> data/hex_osm.csv
python scripts/osm_validate.py           # cross-check the score vs OSM -> outputs/osm_validation.md
```

The raw 105 MB violations CSV is not committed (it exceeds GitHub's limit and is the
provided dataset); drop it in as `data/violations.csv` only if you want to re-run the
cleaning step.

---

## Deliverables checklist

- [x] Title, one-liner, theme
- [x] Description
- [x] Repository URL
- [x] Instructions to run
- [ ] **Demo link** (deploy `web/` to Vercel, root directory = `web`)
- [ ] **Video** (2–3 min; script below)
- [ ] **Pitch deck** (outline in `submission/PITCH_DECK.md`)
- [ ] **Snapshots** (grab from the live site once deployed)
- [ ] **Source code zip** (≤50 MB; the repo minus `web/node_modules`, `web/.next`,
      `web/out`, and `data/violations.csv` is already well under)

---

## Video walkthrough script (about 2.5 minutes)

> Spoken lines in plain text, screen cues in *italics*.

**[0:00] The problem**
Every day, Bengaluru's traffic police log thousands of parking violations. But that
data only shows where tickets get written, not where parking actually blocks traffic.
A quiet lane that gets a daily pre-dawn sweep can look worse than the junction that
jams a main road every evening. Enforcement is flying half-blind.

**[0:25] What we built**
*Open the site, scroll the hero.*
ParkPulse takes 298,000 real violation records and answers one question: where, and
when, should a patrol go to relieve the most congestion.

**[0:45] The impact map**
*Hover a couple of cells, then hit the Impact / Raw toggle.*
This is the map. Every cell has a Congestion Impact Score built from how much it
blocks the road, how busy that road is, how often it reoffends, and the volume. Watch
the toggle: on raw count the pre-dawn sweep zones light up, but on impact they fade,
and the real chokepoints take over. That re-ranking is the product.

**[1:20] Ranked zones**
*Scroll to the zones table.*
It comes out as a shortlist: the thirty worst cells, each with the main violation, the
streets involved, and the two-hour window when enforcing there does the most good.

**[1:40] Forecaster**
*Scroll to the forecaster charts.*
This is the one real machine-learning model. We trained it on past months and tested
on months it never saw. It beats the standard seasonal baseline by 36 percent. And
we were honest: we tried 29 more features and heavier models, and none of them beat
the simple base set. The ceiling here is the data, not the algorithm.

**[2:05] Patrol optimizer**
*Drag the slider.*
Finally, the optimizer turns it into a plan. Drag to twenty patrols and we cover
53 percent of the city's parking-induced congestion, because the worst spots cluster,
so spreading out beats just taking the top of the list.

**[2:30] Honesty and close**
*Scroll to methodology.*
One thing we never had is actual traffic speeds, so we don't pretend the score is a
measurement. But the moment a speed feed exists, this whole system trains straight
into it. That's ParkPulse: where and when to send the next patrol. Thank you.
