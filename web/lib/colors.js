// Inferno-ish sequential ramp — low scores read as deep indigo, high scores glow
// orange→yellow on the dark basemap. Used for hex fill + legends.
const STOPS = [
  [0.0, [22, 26, 56]],
  [0.15, [52, 22, 92]],
  [0.3, [96, 28, 112]],
  [0.45, [146, 38, 104]],
  [0.6, [198, 58, 78]],
  [0.72, [230, 98, 52]],
  [0.85, [246, 154, 42]],
  [1.0, [252, 232, 140]],
];

const lerp = (a, b, t) => a + (b - a) * t;

export function ramp(t) {
  t = Math.max(0, Math.min(1, t || 0));
  for (let i = 1; i < STOPS.length; i++) {
    if (t <= STOPS[i][0]) {
      const [t0, c0] = STOPS[i - 1];
      const [t1, c1] = STOPS[i];
      const f = (t - t0) / (t1 - t0 || 1);
      return [
        Math.round(lerp(c0[0], c1[0], f)),
        Math.round(lerp(c0[1], c1[1], f)),
        Math.round(lerp(c0[2], c1[2], f)),
      ];
    }
  }
  return STOPS[STOPS.length - 1][1];
}

export const rgb = (c) => `rgb(${c[0]},${c[1]},${c[2]})`;
export const rgba = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

export const legendGradient = `linear-gradient(90deg, ${STOPS
  .map((s) => `${rgba(s[1])} ${Math.round(s[0] * 100)}%`)
  .join(", ")})`;
