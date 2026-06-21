"""
build_map.py — ParkPulse Step 2/3
================================================================================
Interactive folium map of the H3 res-9 hotspot cells, colored by Congestion
Impact Score, with a RAW-COUNT <-> IMPACT-SCORE toggle (two FeatureGroup layers
+ LayerControl). The contrast is the key demo moment: it shows how impact
weighting re-ranks the city vs. raw violation density (e.g. a cell with huge
counts logged during the pre-dawn enforcement sweep stays "hot" on the raw layer
but cools on the impact layer — CLAUDE.md §6.6).

Input : data/hex_scored.csv   (from compute_impact_score.py)
Output: outputs/parkpulse_map.html
"""
from __future__ import annotations

import branca.colormap as cm
import folium
import h3
import pandas as pd

IN_PATH = "data/hex_scored.csv"
OUT_PATH = "outputs/parkpulse_map.html"

BENGALURU_CENTER = (12.965, 77.59)
ZOOM_START = 12

# YlOrRd sequential ramp (low -> high severity)
YLORRD = ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c",
          "#fc4e2a", "#e31a1c", "#bd0026", "#800026"]


def load_scored(path: str = IN_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "impact_score" not in df.columns:
        raise ValueError(f"{path} has no impact_score — run compute_impact_score.py first")
    return df


def hex_ring_lonlat(h3id: str) -> list[list[float]]:
    """Closed GeoJSON ring [[lon, lat], ...] for an H3 cell (h3 v4 -> (lat, lon))."""
    ring = [[lon, lat] for lat, lon in h3.cell_to_boundary(h3id)]
    ring.append(ring[0])                 # close the polygon
    return ring


def build_geojson(df: pd.DataFrame) -> dict:
    """One FeatureCollection; each cell carries display props + both color values."""
    feats = []
    for r in df.itertuples(index=False):
        props = {
            "station": str(r.dom_station),
            "violation": str(r.dom_violation),
            "modal_hour": f"{int(r.modal_hour):02d}:00 IST",
            "n_violations": int(r.n_violations),
            "impact_score": round(float(r.impact_score), 1),
            "impact_rank": int(r.impact_rank),
            "count_pct": round(float(r.vol_pct) * 100, 1),       # raw-density percentile
            "axes": (f"Volume {r.vol_pct*100:.0f} · Intensity {r.intensity_pct*100:.0f} · "
                     f"Exposure {r.expo_pct*100:.0f} · Persistence {r.persist_pct*100:.0f}"),
            "why": str(r.why),
        }
        feats.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Polygon", "coordinates": [hex_ring_lonlat(r.h3_9)]},
        })
    return {"type": "FeatureCollection", "features": feats}


def _style_by(field: str, cmap: cm.LinearColormap):
    def style(feat):
        return {"fillColor": cmap(feat["properties"][field]), "color": "#3a3a3a",
                "weight": 0.3, "fillOpacity": 0.72}
    return style


def _highlight(_feat):
    return {"weight": 2.2, "color": "#000000", "fillOpacity": 0.9}


def _popup() -> folium.GeoJsonPopup:
    return folium.GeoJsonPopup(
        fields=["station", "impact_score", "impact_rank", "n_violations",
                "violation", "modal_hour", "axes", "why"],
        aliases=["Police station", "Impact score (0–100)", "Impact rank",
                 "Violations (count)", "Top violation", "Most-logged hour",
                 "Axis percentiles", "Why it scores"],
        localize=True, labels=True, max_width=340,
    )


def build_map(df: pd.DataFrame) -> folium.Map:
    gj = build_geojson(df)
    cmap = cm.LinearColormap(YLORRD, vmin=0, vmax=100)
    cmap.caption = ("Severity 0–100   |   Impact layer = Congestion Impact Score   ·   "
                    "Raw layer = violation-count percentile")

    m = folium.Map(location=BENGALURU_CENTER, zoom_start=ZOOM_START,
                   tiles="cartodbpositron", control_scale=True)

    # Layer 1 — impact-weighted (shown by default)
    fg_impact = folium.FeatureGroup(name="🎯 Congestion impact (impact-weighted)", show=True)
    folium.GeoJson(gj, name="impact", style_function=_style_by("impact_score", cmap),
                   highlight_function=_highlight, popup=_popup()).add_to(fg_impact)
    fg_impact.add_to(m)

    # Layer 2 — raw violation density (hidden by default; tick to compare)
    fg_raw = folium.FeatureGroup(name="📊 Raw violation density (count percentile)", show=False)
    folium.GeoJson(gj, name="raw", style_function=_style_by("count_pct", cmap),
                   highlight_function=_highlight, popup=_popup()).add_to(fg_raw)
    fg_raw.add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    _add_titlebar(m, df)
    return m


def _add_titlebar(m: folium.Map, df: pd.DataFrame) -> None:
    """Floating header: title, how-to, and the honest no-ground-truth caveat."""
    n = len(df)
    html = f"""
    <div style="position:fixed; top:12px; left:60px; z-index:9999; width:430px;
        background:rgba(255,255,255,.94); border:1px solid #bbb; border-radius:8px;
        padding:10px 14px; font-family:'DejaVu Sans',Arial,sans-serif; box-shadow:0 1px 6px rgba(0,0,0,.2);">
      <div style="font-size:16px; font-weight:700; color:#1b2a4a;">ParkPulse — Congestion Impact Map</div>
      <div style="font-size:12px; color:#333; margin-top:3px;">
        {n} parking hotspot cells (H3 res-9, ~150&nbsp;m), Bengaluru. Color = severity 0–100.
      </div>
      <div style="font-size:12px; color:#333; margin-top:5px;">
        Use the layer control (top-right) to switch between
        <b>impact-weighted</b> and <b>raw violation density</b> — the re-ranking is the point.
        Click any cell for its score breakdown.
      </div>
      <div style="font-size:11px; color:#777; margin-top:6px; font-style:italic;">
        Impact is a transparent engineered index (volume × intensity × exposure × persistence),
        not a measured value — there is no traffic-flow ground truth in this data.
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(html))


def main() -> None:
    import os
    df = load_scored()
    m = build_map(df)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    m.save(OUT_PATH)
    size_mb = os.path.getsize(OUT_PATH) / 1e6
    print(f"Saved -> {OUT_PATH}  ({len(df)} cells, {size_mb:.1f} MB)")
    print("Layers: impact-weighted (default) + raw violation density; toggle via LayerControl.")


if __name__ == "__main__":
    main()
