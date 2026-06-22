"""
scripts/enrich_osm.py: enrich each hotspot with the REAL road network and nearby
congestion-generators from OpenStreetMap, so road-importance stops being a text proxy.

For every H3 hotspot cell it records:
  - the class of the nearest drivable road (motorway/trunk/primary/.../residential)
    mapped to a road-criticality weight, and
  - counts of nearby congestion-generators (markets, malls, schools, hospitals,
    transit stops) within the cell, which explain WHY a spot chokes and give a
    quantitative face-validity check.

This needs network access to OSM (Overpass), which the build sandbox blocks, so run
it on a normal machine:

    pip install "osmnx>=2.0" "networkx>=3.0"
    python scripts/enrich_osm.py
    python web/prepare_data.py        # re-export so the site picks it up

Output: data/hex_osm.csv. Everything downstream treats this file as OPTIONAL: if it
is absent the impact score and the site fall back to the text-token road proxy.
Edge betweenness centrality (true flow-criticality) is a further upgrade noted below.
"""
from __future__ import annotations
import os
import sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORED = os.path.join(ROOT, "data", "hex_scored.csv")
OUT = os.path.join(ROOT, "data", "hex_osm.csv")
PAD = 0.01  # ~1 km bbox padding around the hotspot extent

# OSM highway class -> road-criticality weight (how much flow the road carries)
ROAD_W = {"motorway": 1.0, "trunk": 0.9, "primary": 0.8, "secondary": 0.6,
          "tertiary": 0.45, "unclassified": 0.3, "residential": 0.25,
          "living_street": 0.15, "service": 0.1}
POI_TAGS = {"amenity": ["marketplace", "school", "hospital", "college"],
            "shop": ["mall", "supermarket"], "public_transport": ["station", "stop_position"],
            "railway": ["station"]}
BETW_K = 500          # sampled sources for approximate (k-sampled) betweenness centrality


def _crit(highway):
    """Highway tag can be a string or a list; take the most critical class."""
    if isinstance(highway, list):
        return max((ROAD_W.get(h, 0.2) for h in highway), default=0.2)
    return ROAD_W.get(highway, 0.2)


def main():
    try:
        import osmnx as ox
        import h3
    except ImportError:
        sys.exit("Needs osmnx + h3. Run:  pip install \"osmnx>=2.0\" networkx h3")

    cells = pd.read_csv(SCORED)[["h3_9", "lat", "lon"]]
    north, south = cells.lat.max() + PAD, cells.lat.min() - PAD
    east, west = cells.lon.max() + PAD, cells.lon.min() - PAD
    print(f"hotspot bbox: N{north:.3f} S{south:.3f} E{east:.3f} W{west:.3f}  ({len(cells)} cells)")

    # 1) nearest drivable road class per cell
    print("downloading drive network from OSM (a few minutes)...")
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive")
    edges = ox.distance.nearest_edges(G, X=cells.lon.values, Y=cells.lat.values)
    hwy = []
    for (u, v, k) in edges:
        data = G.edges[u, v, k]
        hwy.append(data.get("highway"))
    cells["nearest_highway"] = [h[0] if isinstance(h, list) else h for h in hwy]
    cells["road_criticality"] = [round(_crit(h), 3) for h in hwy]

    # 2) node betweenness centrality: how critical each cell's nearest road is to flow
    if "--no-betweenness" not in sys.argv:
        import networkx as nx
        print(f"computing k-sampled betweenness centrality (k={BETW_K}, a couple of minutes)...")
        bc = nx.betweenness_centrality(G, k=min(BETW_K, len(G.nodes)), weight="length", seed=1)
        cnodes = ox.distance.nearest_nodes(G, X=cells.lon.values, Y=cells.lat.values)
        raw = [bc.get(nd, 0.0) for nd in cnodes]
        mx = max(raw) or 1.0
        cells["betweenness"] = [round(r / mx, 4) for r in raw]

    # 3) nearby congestion-generators (assign each POI to its H3 res-9 cell, count)
    print("downloading POIs from OSM...")
    feats = ox.features_from_bbox(bbox=(west, south, east, north), tags=POI_TAGS)
    feats = feats[feats.geometry.notna()].copy()
    feats["pt"] = feats.geometry.representative_point()
    feats["h3_9"] = feats["pt"].apply(lambda p: h3.latlng_to_cell(p.y, p.x, 9))

    def kind(row):
        if str(row.get("shop", "")) in ("mall", "supermarket"):
            return "retail"
        if str(row.get("amenity", "")) == "marketplace":
            return "market"
        if str(row.get("amenity", "")) in ("school", "college"):
            return "school"
        if str(row.get("amenity", "")) == "hospital":
            return "hospital"
        return "transit"
    feats["kind"] = feats.apply(kind, axis=1)
    poi = feats.groupby(["h3_9", "kind"]).size().unstack(fill_value=0)
    cells = cells.merge(poi, on="h3_9", how="left").fillna({c: 0 for c in poi.columns})

    poi_cols = [c for c in ["market", "retail", "school", "hospital", "transit"] if c in cells.columns]
    cells["n_poi"] = cells[poi_cols].sum(axis=1).astype(int) if poi_cols else 0

    def context(r):
        bits = []
        if r.get("nearest_highway"):
            bits.append(f"{r['nearest_highway']} road")
        for c in poi_cols:
            if r.get(c, 0) > 0:
                bits.append(f"{int(r[c])} {c}")
        return ", ".join(bits)
    cells["osm_context"] = cells.apply(context, axis=1)
    cells.to_csv(OUT, index=False)

    near = (cells["n_poi"] > 0).mean() if "n_poi" in cells else 0
    print(f"wrote {OUT}: {len(cells)} cells; {near*100:.0f}% sit next to a market/transit/school/hospital")
    if "betweenness" in cells.columns:
        print("included node betweenness centrality (normalized 0-1).")
    print("next: python scripts/osm_validate.py   # cross-check the impact score against this OSM data")


if __name__ == "__main__":
    main()
