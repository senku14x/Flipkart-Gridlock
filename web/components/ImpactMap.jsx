"use client";
import { useEffect, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import { H3HexagonLayer, TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { ramp, rgb, legendGradient } from "../lib/colors";

const INITIAL_VIEW = {
  longitude: 77.585, latitude: 12.972, zoom: 11, minZoom: 9.2, maxZoom: 16,
  pitch: 0, bearing: 0,
};
const CARTO_DARK = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png";

function AxisBar({ label, v }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 shrink-0 text-[11px] text-slate-400">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-white/10">
        <div className="h-full rounded-full" style={{ width: `${v}%`, background: rgb(ramp(v / 100)) }} />
      </div>
      <span className="mono w-7 text-right text-[11px] text-slate-300">{v}</span>
    </div>
  );
}

export default function ImpactMap() {
  const [hexes, setHexes] = useState(null);
  const [mode, setMode] = useState("impact"); // "impact" | "raw"
  const [hover, setHover] = useState(null);

  useEffect(() => {
    fetch("/data/hexes.json").then((r) => r.json()).then(setHexes).catch(() => {});
  }, []);

  const layers = useMemo(() => {
    const base = new TileLayer({
      id: "carto-dark", data: CARTO_DARK, minZoom: 0, maxZoom: 19, tileSize: 256,
      renderSubLayers: (props) => {
        const { boundingBox: bb } = props.tile;
        return new BitmapLayer(props, {
          data: null, image: props.data,
          bounds: [bb[0][0], bb[0][1], bb[1][0], bb[1][1]],
        });
      },
    });
    const hex = hexes &&
      new H3HexagonLayer({
        id: "impact-hex", data: hexes, pickable: true, stroked: true, filled: true,
        extruded: false, getHexagon: (d) => d.h,
        getFillColor: (d) => {
          const c = ramp((mode === "impact" ? d.s : d.c) / 100);
          return [c[0], c[1], c[2], 205];
        },
        getLineColor: [255, 255, 255, 18], lineWidthMinPixels: 0.4,
        onHover: (info) => setHover(info.object ? { o: info.object, x: info.x, y: info.y } : null),
        updateTriggers: { getFillColor: mode },
      });
    return [base, hex].filter(Boolean);
  }, [hexes, mode]);

  return (
    <div className="relative h-[78vh] min-h-[520px] w-full overflow-hidden rounded-2xl border border-white/10">
      <DeckGL
        initialViewState={INITIAL_VIEW}
        controller={{ dragRotate: false }}
        layers={layers}
        style={{ position: "absolute", inset: 0 }}
      />

      {/* toggle + caption */}
      <div className="pointer-events-auto absolute left-4 top-4 z-10 w-[260px] rounded-xl bg-ink/85 p-3 backdrop-blur ring-1 ring-white/10">
        <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Color cells by</div>
        <div className="mt-2 grid grid-cols-2 gap-1 rounded-lg bg-white/5 p-1">
          {[["impact", "Impact"], ["raw", "Raw density"]].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setMode(k)}
              className={`rounded-md px-2 py-1.5 text-sm font-medium transition ${
                mode === k ? "bg-accent text-white shadow" : "text-slate-300 hover:bg-white/5"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-[12px] leading-snug text-slate-400">
          {mode === "impact"
            ? "Congestion Impact Score — volume × intensity × exposure × persistence."
            : "Raw violation-count percentile. Toggle to Impact to see the re-ranking."}
        </p>
      </div>

      {/* legend */}
      <div className="absolute bottom-4 left-4 z-10 rounded-xl bg-ink/85 px-3 py-2 backdrop-blur ring-1 ring-white/10">
        <div className="text-[11px] text-slate-400">{mode === "impact" ? "Impact score" : "Count percentile"}</div>
        <div className="mt-1 h-2 w-44 rounded-full" style={{ background: legendGradient }} />
        <div className="mono mt-1 flex w-44 justify-between text-[10px] text-slate-500"><span>0</span><span>50</span><span>100</span></div>
      </div>

      {/* count */}
      <div className="absolute right-4 top-4 z-10 rounded-xl bg-ink/85 px-3 py-2 text-right backdrop-blur ring-1 ring-white/10">
        <div className="mono text-lg font-semibold text-white">{hexes ? hexes.length.toLocaleString() : "…"}</div>
        <div className="text-[11px] text-slate-400">H3 hotspot cells</div>
      </div>

      {/* hover card */}
      {hover && (
        <div
          className="pointer-events-none absolute z-20 w-[268px] rounded-xl bg-ink/95 p-3 text-sm shadow-2xl ring-1 ring-white/15"
          style={{
            left: Math.min(hover.x + 14, 9999), top: hover.y + 14,
            transform: hover.x > 520 ? "translateX(-110%)" : "none",
          }}
        >
          <div className="flex items-baseline justify-between">
            <span className="font-semibold text-white">{hover.o.st}</span>
            <span className="mono text-xl font-bold" style={{ color: rgb(ramp(hover.o.s / 100)) }}>
              {hover.o.s}
            </span>
          </div>
          <div className="text-[12px] text-slate-400">{hover.o.vi} · {hover.o.n.toLocaleString()} violations</div>
          <div className="my-2 space-y-1">
            <AxisBar label="Volume" v={hover.o.vp} />
            <AxisBar label="Intensity" v={hover.o.ip} />
            <AxisBar label="Exposure" v={hover.o.ep} />
            <AxisBar label="Persist" v={hover.o.pp} />
          </div>
          <div className="text-[12px] leading-snug text-slate-300">{hover.o.wy}</div>
        </div>
      )}
    </div>
  );
}
