/**
 * formatCurrency — Shared number formatting utility (EX-3 fix)
 *
 * Enforces consistent compact notation globally.
 * Replaces ad-hoc fmtM / fmtK helpers scattered across components.
 */

const compactFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  compactDisplay: 'short',
  maximumFractionDigits: 1,
});

const preciseFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

/**
 * Format a number as a compact currency string.
 * e.g., 1_234_567 → "$1.2M", 45_000 → "$45K", 500 → "$500"
 */
export function fmtCompact(value) {
  if (value == null || isNaN(value)) return '$0';
  return '$' + compactFormatter.format(Math.abs(value));
}

/**
 * Format a number with full precision.
 * e.g., 1_234_567 → "$1,234,567"
 */
export function fmtFull(value) {
  if (value == null || isNaN(value)) return '$0';
  return preciseFormatter.format(value);
}

/**
 * Format as millions with 1 decimal.
 * e.g., 1_234_567 → "$1.2M"
 */
export function fmtM(value) {
  if (value == null || isNaN(value)) return '$0M';
  return `$${((value || 0) / 1_000_000).toFixed(1)}M`;
}

/**
 * Smart format: millions if >= 1M, thousands if >= 1K, raw otherwise.
 */
export function fmtK(value) {
  if (value == null || isNaN(value)) return '$0';
  const abs = Math.abs(value || 0);
  if (abs >= 1_000_000) return fmtM(value);
  if (abs >= 1_000) return `$${((value || 0) / 1_000).toFixed(0)}K`;
  return `$${Math.round(value || 0)}`;
}

/**
 * Format a percentage with 1 decimal.
 */
export function fmtPct(value) {
  if (value == null || isNaN(value)) return '0%';
  return `${Number(value).toFixed(1)}%`;
}

export default { fmtCompact, fmtFull, fmtM, fmtK, fmtPct };
