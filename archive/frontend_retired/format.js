/**
 * format.js (D4) — single source of truth for number/currency/percent display.
 *
 * Several components had their own inline formatters, which risked drift between
 * panels (treasury shown as "$1.2M" in one place, "$1,200,000" in another).
 * Import these instead of hand-rolling. Behaviour matches the previous inline
 * `fmtCurrency` in page.js so existing displays are unchanged.
 */

/**
 * Compact currency: >= $1M → "$1.2M", >= $1K → "$12K", else "$950".
 * Preserves sign. Matches the canonical inline formatter used in page.js.
 */
export function fmtCurrency(v, { signed = false } = {}) {
  if (v == null || Number.isNaN(v)) return '—';
  const sign = v < 0 ? '-' : (signed && v > 0 ? '+' : '');
  const a = Math.abs(v);
  let body;
  if (a >= 1_000_000) body = `$${(a / 1_000_000).toFixed(1)}M`;
  else if (a >= 1_000) body = `$${(a / 1_000).toFixed(0)}K`;
  else body = `$${a.toFixed(0)}`;
  return `${sign}${body}`;
}

/** Full currency with thousands separators: "$1,234,567". */
export function fmtCurrencyFull(v) {
  if (v == null || Number.isNaN(v)) return '—';
  return `$${Math.round(v).toLocaleString('en-US')}`;
}

/** Percentage: fmtPct(0.153) → "15.3%". Pass isRatio=false if already 0–100. */
export function fmtPct(v, { digits = 1, isRatio = true } = {}) {
  if (v == null || Number.isNaN(v)) return '—';
  const pct = isRatio ? v * 100 : v;
  return `${pct.toFixed(digits)}%`;
}

/** Plain number with optional fixed digits and thousands separators. */
export function fmtNumber(v, { digits = 0 } = {}) {
  if (v == null || Number.isNaN(v)) return '—';
  return v.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** A signed delta for KPI moves: fmtDelta(3) → "+3", fmtDelta(-2) → "-2". */
export function fmtDelta(v, { digits = 0 } = {}) {
  if (v == null || Number.isNaN(v)) return '—';
  const s = v > 0 ? '+' : '';
  return `${s}${v.toFixed(digits)}`;
}
