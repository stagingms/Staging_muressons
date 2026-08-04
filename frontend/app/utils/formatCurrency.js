/**
 * formatCurrency — kept as the public surface, now a thin delegate.
 *
 * These five helpers are called from ~100 sites. They used to hard-code '$'
 * and a per-helper precision, which is what put '₹16.6M' and '$11.62' on the
 * same screen. Rather than churn every call site, the behaviour moved to
 * utils/format.js (one symbol, one precision policy) and this file forwards.
 *
 * New code should import from utils/format.js directly.
 */
import { money, moneyFull, percent, currencySymbol } from './format';

/** Compact currency. e.g. 1_234_567 → "₹1.2M" */
export function fmtCompact(value) {
  return value == null || isNaN(value) ? `${currencySymbol()}0` : money(value);
}

/** Full precision, grouped. e.g. 1_234_567 → "₹1,234,567" */
export function fmtFull(value) {
  return value == null || isNaN(value) ? `${currencySymbol()}0` : moneyFull(value);
}

/** Millions, 1dp. e.g. 1_234_567 → "₹1.2M" */
export function fmtM(value) {
  if (value == null || isNaN(value)) return `${currencySymbol()}0M`;
  const v = Number(value);
  return `${v < 0 ? '−' : ''}${currencySymbol()}${(Math.abs(v) / 1_000_000).toFixed(1)}M`;
}

/** Millions / thousands / units, by magnitude. */
export function fmtK(value) {
  return value == null || isNaN(value) ? `${currencySymbol()}0` : money(value);
}

/** Percentage, 1dp. */
export function fmtPct(value) {
  return value == null || isNaN(value) ? '0%' : percent(value);
}

export default { fmtCompact, fmtFull, fmtM, fmtK, fmtPct };
