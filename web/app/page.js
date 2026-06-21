"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Zones from "../components/Zones";
import Forecaster from "../components/Forecaster";
import Optimizer from "../components/Optimizer";
import Methodology from "../components/Methodology";

const ImpactMap = dynamic(() => import("../components/ImpactMap"), {
  ssr: false,
  loading: () => <div className="grid h-[78vh] place-items-center rounded-2xl border border-white/10 text-slate-500">Loading map…</div>,
});

const NAV = [["map", "Map"], ["zones", "Zones"], ["forecast", "Forecast"], ["patrols", "Patrols"], ["method", "Method"]];

function Stat({ value, label, accent }) {
  return (
    <div className="card px-5 py-4">
      <div className={`mono text-3xl font-bold ${accent || "text-white"}`}>{value}</div>
      <div className="mt-1 text-sm text-slate-400">{label}</div>
    </div>
  );
}

function Section({ id, eyebrow, title, sub, children }) {
  return (
    <section id={id} className="scroll-mt-24 pt-20">
      <div className="text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</div>
      <h2 className="mt-1 text-3xl font-bold tracking-tight">{title}</h2>
      {sub && <p className="mt-2 max-w-2xl text-slate-400">{sub}</p>}
      <div className="mt-6">{children}</div>
    </section>
  );
}

export default function Home() {
  const [k, setK] = useState(null);
  useEffect(() => { fetch("/data/kpis.json").then((r) => r.json()).then(setK).catch(() => {}); }, []);

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-white/5 bg-ink/70 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <a href="#top" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent text-sm">P</span>
            ParkPulse
          </a>
          <div className="hidden items-center gap-6 text-sm text-slate-400 md:flex">
            {NAV.map(([id, label]) => <a key={id} href={`#${id}`} className="hover:text-white">{label}</a>)}
          </div>
          <a href="https://github.com/senku14x/Flipkart-Gridlock" className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5">GitHub ↗</a>
        </nav>
      </header>

      <main id="top" className="mx-auto max-w-6xl px-5 pb-28">
        <section className="aurora relative pt-14">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
              Gridlock Hackathon 2.0 · Poor Visibility on Parking-Induced Congestion
            </div>
            <h1 className="mt-5 max-w-3xl text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
              AI parking intelligence for <span className="text-accent">impact-prioritized</span> enforcement.
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-slate-300">
              ParkPulse turns 298K real Bengaluru parking-violation records into a decision tool — scoring every
              hotspot by its drag on traffic flow, and telling enforcement <b>where and when</b> to deploy for the
              most congestion relief per patrol-hour.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a href="#map" className="rounded-xl bg-accent px-5 py-2.5 font-medium text-white shadow-lg shadow-accent/20 hover:brightness-110">Explore the map</a>
              <a href="#patrols" className="rounded-xl border border-white/10 px-5 py-2.5 font-medium text-slate-200 hover:bg-white/5">Patrol optimizer</a>
            </div>
          </div>
          <div className="relative z-10 mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat value={k ? `${(k.violations / 1000).toFixed(0)}K` : "—"} label="violation records" />
            <Stat value={k ? k.hotspots.toLocaleString() : "—"} label="H3 hotspot cells" />
            <Stat value={k ? `${k.top1_impact}%` : "—"} label="of impact in top 1% of cells" accent="text-gold" />
            <Stat value={k ? `${k.beats20_greedy}%` : "—"} label="impact covered by 20 patrols" accent="text-acc2" />
          </div>
        </section>

        <Section id="map" eyebrow="Where it hurts" title="The impact-weighted hotspot map"
          sub="Every ~150 m cell, colored by Congestion Impact Score. Toggle to raw density and watch the city re-rank — chronic night-sweep clusters cool down; obstructive, peak-hour chokepoints light up. Hover any cell for its breakdown.">
          <ImpactMap />
        </Section>

        <Section id="zones" eyebrow="The ops payload" title="Ranked enforcement zones"
          sub="The top 30 cells by impact, each with a dominant violation, the streets involved, and an exposure-weighted enforcement window — where and when, not just where.">
          <Zones />
        </Section>

        <Section id="forecast" eyebrow="The one real ML model" title="Violation forecaster"
          sub="A genuine supervised model with real ground truth, on a strict temporal holdout — benchmarked across the whole gradient-boosting family and honestly stress-tested for more performance.">
          <Forecaster />
        </Section>

        <Section id="patrols" eyebrow="From insight to action" title="Patrol optimizer"
          sub="Drag the slider: a greedy max-coverage optimizer assigns N patrol beats to maximize the congestion impact relieved. Because the worst cells cluster, it beats a naive top-N pick — same fleet, more coverage.">
          <Optimizer />
        </Section>

        <Section id="method" eyebrow="Why you can trust it" title="Methodology & honesty"
          sub="The judging-grade caveats, surfaced — what the score is, what the data can and can't say, and how it sharpens the day a flow feed arrives.">
          <Methodology />
        </Section>

        <footer className="mt-24 border-t border-white/5 pt-8 text-sm text-slate-500">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>ParkPulse — Gridlock Hackathon 2.0, Round 2. Built on 298,445 Bengaluru parking-violation records.</span>
            <a href="https://github.com/senku14x/Flipkart-Gridlock" className="hover:text-slate-300">Repository ↗</a>
          </div>
        </footer>
      </main>
    </>
  );
}
