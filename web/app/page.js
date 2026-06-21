"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Gap from "../components/Gap";
import Zones from "../components/Zones";
import Cost from "../components/Cost";
import Emerging from "../components/Emerging";
import Forecaster from "../components/Forecaster";
import Detection from "../components/Detection";
import Optimizer from "../components/Optimizer";
import Methodology from "../components/Methodology";
import { inr } from "../lib/format";

const ImpactMap = dynamic(() => import("../components/ImpactMap"), {
  ssr: false,
  loading: () => <div className="grid h-[78vh] place-items-center rounded-2xl border border-white/10 text-slate-500">Loading map…</div>,
});

const NAV = [["map", "Map"], ["zones", "Zones"], ["cost", "Cost"], ["forecast", "Forecast"], ["patrols", "Patrols"], ["method", "Method"]];

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
          <a href="https://github.com/senku14x/Flipkart-Gridlock" className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5">GitHub</a>
        </nav>
      </header>

      <main id="top" className="mx-auto max-w-6xl px-5 pb-28">
        <section className="aurora relative pt-14">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
              Gridlock Hackathon 2.0 · Poor Visibility on Parking-Induced Congestion
            </div>
            <h1 className="mt-5 max-w-3xl text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
              Patrol the parking that actually <span className="text-accent">chokes traffic</span>.
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-slate-300">
              Bengaluru logs thousands of parking violations a day, but enforcement can&apos;t tell which ones
              actually hurt traffic. ParkPulse reads 298,000 real records and scores every hotspot by how much it
              slows the road, so patrols go <b>where and when</b> they&apos;ll relieve the most congestion.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a href="#map" className="rounded-xl bg-accent px-5 py-2.5 font-medium text-white shadow-lg shadow-accent/20 hover:brightness-110">Explore the map</a>
              <a href="#patrols" className="rounded-xl border border-white/10 px-5 py-2.5 font-medium text-slate-200 hover:bg-white/5">Patrol optimizer</a>
            </div>
          </div>
          <div className="relative z-10 mt-6 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-gold/30 bg-gold/10 px-4 py-2.5 text-sm text-slate-200">
            <span>Estimated <b className="text-gold">{k ? inr(k.cost_year_base) : "…"}/year</b> in lost time from these violations.</span>
            <span className="text-slate-300">A focused patrol plan relieves <b className="text-acc2">{k ? `${k.beats20_greedy}%` : "…"}</b> of it.</span>
          </div>
          <div className="relative z-10 mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat value={k ? `${(k.violations / 1000).toFixed(0)}K` : "…"} label="violation records" />
            <Stat value={k ? k.hotspots.toLocaleString() : "…"} label="H3 hotspot cells" />
            <Stat value={k ? `${k.top1_impact}%` : "…"} label="of impact in top 1% of cells" accent="text-gold" />
            <Stat value={k ? `${k.beats20_greedy}%` : "…"} label="impact covered by 20 patrols" accent="text-acc2" />
          </div>
        </section>

        <Section id="map" eyebrow="Where it hurts" title="The impact-weighted hotspot map"
          sub="Every cell, about 150 m across, is colored by its Congestion Impact Score. Switch to raw density and the map shifts: spots that mostly catch pre-dawn enforcement fade out, while the ones blocking busy roads at rush hour jump forward. Hover any cell to see why it scores.">
          <ImpactMap />
        </Section>

        <Section id="gap" eyebrow="The visibility gap" title="Effort is going to the wrong hours"
          sub="Recorded violations double as a map of enforcement effort. Weight each by congestion impact and a gap opens up: a large share of effort lands at night, when roads are empty, and misses the peak-hour chokepoints.">
          <Gap />
        </Section>

        <Section id="zones" eyebrow="The shortlist" title="Ranked enforcement zones"
          sub="The 30 highest-impact cells, each with its main violation, the streets involved, and the two-hour window when enforcing there does the most good. Where and when, not just where.">
          <Zones />
        </Section>

        <Section id="cost" eyebrow="What it costs" title="The price of the gridlock"
          sub="Impact is a rank; this turns it into a number. We estimate the delay these violations cause in vehicle-hours and rupees, with a sensitivity band, so the case for acting is concrete.">
          <Cost />
        </Section>

        <Section id="trends" eyebrow="What is getting worse" title="Emerging hotspots"
          sub="The map shows where things are bad on average. This shows where they are getting worse: we trend each cell against the city, so a rising spot stands out before it becomes entrenched.">
          <Emerging />
        </Section>

        <Section id="forecast" eyebrow="Looking ahead" title="Violation forecaster"
          sub="This is the one piece with real answers to check against. We train on past months and test on ones the model has never seen, compare every major gradient-boosting library, then push hard to squeeze out more accuracy. Here is what actually helped.">
          <Forecaster />
        </Section>

        <Section id="triage" eyebrow="Don't chase ghosts" title="Flagging false reports"
          sub="Almost a third of reviewed reports are rejected on review. A second model predicts which ones, so patrols are sent to real problems instead of contested or false ones.">
          <Detection />
        </Section>

        <Section id="patrols" eyebrow="Put it to work" title="Patrol optimizer"
          sub="Set your fleet size with the slider. The optimizer picks beats that together cover the most congestion impact. Since the worst cells sit close to one another, spreading patrols out beats simply taking the top N. Same number of patrols, more of the city covered.">
          <Optimizer />
        </Section>

        <Section id="method" eyebrow="The fine print" title="What this is, and what it isn't"
          sub="A few things worth saying plainly: what the score really measures, where the data falls short, and how the whole system gets sharper the day it can read live traffic speeds.">
          <Methodology />
        </Section>

        <footer className="mt-24 border-t border-white/5 pt-8 text-sm text-slate-500">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>ParkPulse, built for Gridlock Hackathon 2.0 (Round 2) on 298,445 real Bengaluru parking-violation records.</span>
            <a href="https://github.com/senku14x/Flipkart-Gridlock" className="hover:text-slate-300">Repository</a>
          </div>
        </footer>
      </main>
    </>
  );
}
