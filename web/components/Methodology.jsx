const CARDS = [
  {
    t: "No traffic-flow ground truth",
    d: "There are no speeds or travel-times in the data, so the Congestion Impact Score is a transparent engineered index — never claimed as a measured value. We validate it by face validity (20/20 top zones match known chokepoints) and month-to-month stability (ρ≈0.86), not accuracy.",
    tag: "Honesty",
  },
  {
    t: "The enforcement-schedule confound",
    d: "Recorded violations ≈ parking demand × patrol presence — a daily 4–5am sweep is 15.3% of the data. So impact and enforcement windows are weighted by an exogenous road-utilisation curve, not by the observed violation hour. The forecaster predicts expected detections under current enforcement, stated plainly.",
    tag: "Rigor",
  },
  {
    t: "Fusion-ready by design",
    d: "The impact score is a model awaiting labels: the day a live speed feed exists, observed delay becomes the label and today's factors become features learned by regression. The data gap is a roadmap, not a wall — the architecture plugs straight into a flow feed, an events calendar, or patrol-roster data.",
    tag: "Architecture",
  },
];

export default function Methodology() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {CARDS.map((c) => (
        <div key={c.t} className="card p-5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-accent">{c.tag}</span>
          <h3 className="mt-2 font-semibold text-white">{c.t}</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-400">{c.d}</p>
        </div>
      ))}
    </div>
  );
}
