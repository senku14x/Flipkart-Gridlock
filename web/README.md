# ParkPulse web app

The interactive frontend for ParkPulse. **Next.js (static export) + deck.gl
(`H3HexagonLayer`) + Recharts**, styled with Tailwind v4. It is **fully static**:
it reads precomputed JSON from `public/data/`, so there is **no backend** and
nothing to scale. It serves from a CDN.

## Develop

```bash
npm install
npm run dev          # http://localhost:3000
```

## Data

`public/data/*.json` is generated from the repo's committed artifacts
(`data/hex_scored.csv`, `outputs/*`). It reuses
`scripts/patrol_optimizer.py` so the site matches the repo:

```bash
# from the repo root
python web/prepare_data.py
```

Re-run it whenever the pipeline outputs change, then commit the JSON.

## Build

```bash
npm run build        # -> out/  (static site)
```

## Deploy to Vercel

1. Import the GitHub repo in Vercel.
2. **Set Root Directory = `web`** (the app lives in this subfolder).
3. Framework preset **Next.js** is auto-detected; build command `next build`.
   No environment variables, no tokens (the basemap is token-free CARTO tiles).

Vercel serves the static export from its global CDN: no server, no cold starts,
and it scales freely. (Any static host works too: Netlify, GitHub Pages, Cloudflare Pages.)
