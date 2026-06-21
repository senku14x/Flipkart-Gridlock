# ParkPulse video demo script

A scene-by-scene shooting script for a ~2 minute 50 second demo. Read the **Voiceover**
lines aloud at a calm pace (~150 words/min); follow the **Screen** directions as you
record. Everything points at the live site, so nothing is faked.

## Before you record
- Open the deployed site (the Vercel URL) in a clean browser window. Hide the bookmarks
  bar and any extensions. Record at 1080p or higher.
- Do a dry run once so the scrolls and hovers feel smooth. Scroll slowly; let each
  section settle for a beat before talking over it.
- Keep the cursor deliberate. When the script says "hover," pause on the cell so the
  tooltip is clearly visible.
- Total target 2:50. If you run long, trim the forecaster and triage lines first.

---

### [0:00] Cold open — the problem
**Screen:** Start at the top of the site (hero on screen, not scrolling yet).
**Voiceover:** "Every day, Bengaluru's traffic police log thousands of parking
violations. But that data only shows where tickets get written, not where parking
actually blocks traffic. A quiet lane that gets a daily pre-dawn sweep can look worse
than the junction that jams a main road every evening. Enforcement is flying half-blind."

### [0:18] What we built
**Screen:** Stay on the hero. Let the headline and the gold cost line ("Estimated Rs 5.2
crore/year... relieves 53% of it") be readable.
**Voiceover:** "ParkPulse reads 298,000 real violation records and answers one question:
where, and when, should a patrol go to relieve the most congestion. And it puts a number
on it: these violations cost an estimated five crore rupees a year in lost time."

### [0:35] The impact map (the core idea)
**Screen:** Scroll to the map. Hover one or two bright cells so the breakdown tooltip
shows (impact score, the four bars, the cost line). Then click the **Raw density** toggle,
pause two seconds, click back to **Impact**.
**Voiceover:** "This is the map. Every cell has a Congestion Impact Score, built from how
much it blocks the road, how busy that road is, how often it reoffends, and the volume.
Watch the toggle. On raw count, the pre-dawn-sweep zones light up. Switch to impact and
they fade, and the real chokepoints take over. That re-ranking is the whole product."

### [1:05] The visibility gap (the punch)
**Screen:** Scroll to the "Effort is going to the wrong hours" section. Let the two big
numbers (33.7% and 7.9%) and the effort-vs-impact bars be on screen.
**Voiceover:** "And here is the gap. A third of recorded enforcement effort lands in the
night window, when roads are empty, and captures under eight percent of the congestion
impact. The four-to-five a.m. sweep alone is fifteen percent of effort for four percent
of impact. ParkPulse moves that effort to where it matters."

### [1:25] The shortlist
**Screen:** Scroll to the ranked-zones table. Let a few rows scroll past.
**Voiceover:** "It comes out as a shortlist: the worst thirty cells, each with the main
violation, the streets involved, and the best window to be there."

### [1:40] What it costs
**Screen:** Scroll to the Cost section. Rest on the three numbers and the costliest list.
**Voiceover:** "Impact is a rank, so we turn it into money: about 574 vehicle-hours of
delay a day, and the worst twenty cells carry nearly a third of the cost. That is the
case for acting, in one number."

### [1:55] The forecaster (honest ML)
**Screen:** Scroll to the forecaster charts (bake-off bars + the small ablation chart).
**Voiceover:** "This is the one model with real labels to check against. Trained on past
months, tested on months it never saw, it beats the standard baseline by thirty-six
percent. And we were honest: we tried twenty-nine more features and heavier models, and
none of them beat the simple one. The ceiling here is the data, not the algorithm."

### [2:15] Catching false reports
**Screen:** Scroll to the Triage section. Rest on the AUC numbers and the orange callout.
**Voiceover:** "A second model flags reports likely to be false, since almost a third get
rejected on review. Flag the top twenty percent and you catch over forty percent of them,
so patrols are sent to real problems."

### [2:28] The patrol optimizer (act)
**Screen:** Scroll to the optimizer. Drag the slider from a low number up to about 20 and
let it settle. Point the cursor at the "53.4% ... Rs 77k/day relieved" readout.
**Voiceover:** "Finally, the optimizer turns it into a plan. Drag to twenty patrols and we
cover fifty-three percent of the city's impact, relieving about seventy-seven thousand
rupees of delay a day, because the worst spots cluster, so spreading out beats taking the
top of the list."

### [2:45] Honesty and close
**Screen:** Scroll to the methodology cards, then back up to the hero for the final frame.
**Voiceover:** "One thing we never had is live traffic speeds, so we do not pretend the
score is a measurement. But the moment a speed feed exists, this whole system trains
straight into it. That is ParkPulse: where, when, and at what cost to send the next
patrol. Thank you."

---

## Shot list (quick reference)
1. Hero (problem + cost line)
2. Map: hover a cell, toggle raw <-> impact
3. Visibility gap section
4. Ranked zones table
5. Cost section
6. Forecaster charts
7. Triage section
8. Optimizer: drag slider to 20, show ROI
9. Methodology cards, end on hero

## If you need a 60-second cut
Keep scenes [0:00], [0:35] (map toggle), [1:05] (the gap), and [2:28] (optimizer + ROI),
then the last line of [2:45]. That is the problem, the idea, the punch, the payoff, and
the honest close.
