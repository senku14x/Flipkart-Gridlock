// Compact Indian-rupee formatting (crore / lakh / thousand).
export function inr(x) {
  if (x == null) return "—";
  if (x >= 1e7) return `₹${(x / 1e7).toFixed(2)} cr`;
  if (x >= 1e5) return `₹${(x / 1e5).toFixed(1)} L`;
  if (x >= 1e3) return `₹${(x / 1e3).toFixed(0)}k`;
  return `₹${Math.round(x)}`;
}
