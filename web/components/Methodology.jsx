const CARDS = [
  {
    t: "We never measured traffic",
    d: "The data has no speeds or travel times, so the impact score is a careful estimate, not a measurement, and we don't pretend otherwise. Instead of claiming accuracy, we check that the top-scoring spots are places locals already know are bad (20 of the top 20 are), and that the ranking barely moves month to month.",
    tag: "Upfront",
  },
  {
    t: "A violation only counts when someone logs it",
    d: "One daily 4–5am sweep makes up 15% of the records, and that isn't when traffic is bad. So we weight everything by when roads are actually busy, not by when tickets happen to get written. The forecaster predicts logged violations under today's patrol habits, and we say that out loud rather than dressing it up as pure demand.",
    tag: "The catch",
  },
  {
    t: "Built to get sharper",
    d: "Right now the score is hand-built. The moment a live speed feed shows up, those same factors become inputs and the measured slowdown becomes the thing to predict. The missing data is a roadmap, not a dead end. Plug in traffic speeds, an events calendar, or patrol rosters and the whole system improves.",
    tag: "What's next",
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
