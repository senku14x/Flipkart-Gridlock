# ParkPulse pitch deck outline

12 slides, about 5 minutes. Each slide has the on-screen content, a short speaker
note, and a visual cue. Keep slides sparse and let the screenshots carry the weight.
Plain voice, no jargon dumps.

---

### 1. Title

**ParkPulse**
Find the parking that actually chokes traffic, and patrol it first.

> Gridlock Hackathon 2.0 · Round 2 · Theme: Poor Visibility on Parking-Induced Congestion

*Visual:* the impact map as a full-bleed background, logo top-left.

---

### 2. The problem

- Bengaluru logs thousands of parking violations every day.
- But the feed shows where **tickets get written**, not where parking **blocks traffic**.
- Those are not the same place.

> Speaker: A lane that gets a daily pre-dawn sweep can collect more tickets than the
> junction that jams a main road every evening. Enforcement can see the tickets, but
> not the traffic pain, so it can't prioritise. That blind spot is the whole theme.

*Visual:* two side-by-side photos, a sleepy lane vs a jammed junction, same ticket count.

---

### 3. What we had to work with

- 298,445 real violation records, five months, the whole city.
- Rich detail: location, vehicle, violation type, timestamps.
- One thing missing: **no traffic speeds, anywhere in the data.**

> Speaker: This matters. We can see every violation, but we never see the actual
> slowdown it causes. So we can't just look up the answer. We have to derive impact,
> and be honest that it's derived.

*Visual:* a few rows of the raw data with the "speed = ?" column greyed out.

---

### 4. The insight

- A raw violation count is mostly "where patrols happen to be."
- A daily 4–5am sweep alone is **15% of all records.**
- Real impact depends on **how much** a violation blocks a **busy** road, and how
  **often** the same spot reoffends.

> Speaker: Two corrections drive everything. First, we don't trust the violation hour,
> we weight by when roads are actually busy. Second, we separate volume from
> intensity, because a thousand tickets on a side street is not the same as a hundred
> blocking a carriageway at rush hour.

*Visual:* the daily hour histogram with the 4–5am spike circled.

---

### 5. The Congestion Impact Score

- One score, 0 to 100, per cell (~150 m).
- Built from four parts: **volume × intensity × exposure × persistence.**
- Deliberately disagrees with a plain count (rank correlation 0.56).

> Speaker: We rank every cell on each of the four axes, then combine them. If the
> score just re-spelled the violation count it would be useless, so the fact that it
> only correlates 0.56 with raw count is a feature, not a bug. The worst 1% of cells
> carry 35% of the city's impact.

*Visual:* the four-axis breakdown card from the map hover.

---

### 6. See it re-rank

- Toggle the map between **raw density** and **impact.**
- Pre-dawn sweep clusters fade. Rush-hour chokepoints take over.

> Speaker: This is where the idea lands. Same city, two colorings. Watch the
> bright spots move when we switch to impact. That movement is the visibility
> the brief asks for.

*Visual:* the two map states, raw vs impact, side by side (or a short clip of the toggle).

---

### 7. From map to shortlist

- The top 30 cells, ranked.
- Each with its main violation, the **streets** involved, and a **two-hour window.**
- Where **and** when, not just where.

> Speaker: A map is nice, but an officer needs a list. So we hand them a shortlist with
> the actual streets and the best time to be there. This is the ops payload.

*Visual:* the ranked-zones table.

---

### 8. The forecasting model

- Forecasts next-day violations per cell. Trained on past months, tested on unseen ones.
- Beats the standard seasonal baseline by **36%** on next-day hit rate.
- We tried 29 more features and heavier models. **None beat the simple base set.**

> Speaker: This is the supervised part, with real answers to check against.
> It wins clearly. And we're honest about the limit: when extra features and tuning
> stop helping, that tells you the ceiling is the data, not the algorithm. Saying that
> out loud is more useful than a fake accuracy number.

*Visual:* the bake-off bar chart plus the small "features didn't help" chart.

---

### 9. Turn it into a patrol plan

- A greedy optimizer assigns N patrol beats for maximum impact covered.
- **20 patrols cover 53%** of citywide impact, against 47% for a naive top-20.
- Live slider: pick your fleet size, get the plan.

> Speaker: Finally we make it actionable. Because the worst cells cluster, you don't
> want twenty patrols in the same square, you want them spread across the clusters. The
> optimizer does that, and you can dial the fleet size live.

*Visual:* the optimizer with the slider at 20 and the coverage curve.

---

### 10. The cost, and two more models

- **The cost:** the impact score becomes ~Rs 5.2 crore/year of delay (vehicle-hours, with a band); the worst 20 cells carry 31% of it.
- **Rising hotspots:** 227 cells are escalating faster than the city, an early warning before they entrench.
- **False-report triage:** a second model (ROC-AUC 0.758) flags likely-rejected reports; flag the top 20% and you catch 43% of them.

> Speaker: Three additions that turn the prioritisation into a business case and a
> fuller toolkit. The cost gives leadership a number. Rising hotspots make it proactive.
> And the triage model means patrols go to real problems, not the roughly one-in-three
> reports that get thrown out on review.

*Visual:* the cost headline beside the rising and triage panels.

---

### 11. Honest about the gap

- No traffic speeds means the score is an **estimate, not a measurement.** We say so.
- We validate by **face validity** (20 of the top 20 are known bad spots) and
  **month-to-month stability** (ρ ≈ 0.75).
- **Fusion-ready:** the day a speed feed exists, it becomes the training target and the
  score becomes a learned model.

> Speaker: Being upfront here builds trust, with judges and with anyone who would deploy this. We never claim
> to have measured congestion. We show the ranking is structural, not noise, and we
> built the system so a real flow feed plugs straight in. The data gap is a roadmap,
> not a wall.

*Visual:* the three methodology cards.

---

### 12. The product

- A fast, **static** web app: Next.js + deck.gl + Recharts.
- All compute is precomputed, so it runs on a CDN with **no backend, no API keys.**
- Scales to any traffic, costs almost nothing to host.

> Speaker: This isn't a notebook screenshot. It's a real site that renders 2,500 cells
> on the GPU and runs the optimizer live in the browser. Static hosting means it can't
> fall over under load and there's nothing to maintain.

*Visual:* the hero, plus small logos for Next.js / deck.gl / Vercel.

---

### 13. Impact and what's next

- **Today:** turns a noisy violation feed into a ranked where-and-when for patrols.
- **Next:** plug in live speeds, an events calendar, and patrol rosters.
- One sentence: **send the next patrol where it relieves the most congestion.**

> Speaker: Right now ParkPulse gives enforcement the prioritisation they're missing.
> With one more data feed it goes from a smart estimate to a measured, learning system.
> Thank you, and the live demo is in the link.

*Visual:* the one-liner big and centered, demo URL underneath.
