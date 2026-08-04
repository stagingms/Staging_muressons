/**
 * kpiFormats — single source of truth for KPI labels + formatting (audit #14).
 *
 * KPI labels and number formatting were re-implemented per component, which is
 * exactly the "same metric, two labels / two formats" drift the CLAUDE.md
 * slotting rule warns about. Import from here so the player, facilitator, and
 * admin surfaces render every metric identically.
 *
 * Currency numbers reuse the existing formatCurrency helper; this module adds
 * the canonical label + unit + delta formatting per metric key.
 */

import { money, percent, score as _fmtScore, ratio as _fmtRatio, delta as _fmtDelta, direction } from './format';

const _pct = (v) => percent(v, { dp: 0 });
const _score = _fmtScore;
const _ratio = _fmtRatio;
const _money = money;

/**
 * Canonical KPI catalog. key → { label, unit, format, goodDirection }.
 * goodDirection: +1 = higher is better, -1 = lower is better (drives delta color).
 */
export const KPI = {
  corporate_treasury:    { label: 'Treasury',            unit: '$',     format: _money, goodDirection: +1 },
  historical_ebitda:     { label: 'EBITDA',              unit: '$',     format: _money, goodDirection: +1 },
  stock_price:           { label: 'Share Price',         unit: '$',     format: _money, goodDirection: +1 },
  social_license_score:  { label: 'Social License',      unit: 'score', format: _score, goodDirection: +1 },
  reputation_score:      { label: 'Reputation',          unit: 'score', format: _score, goodDirection: +1 },
  governance_risk_score: { label: 'Governance Risk',     unit: 'score', format: _score, goodDirection: -1 },
  natural_capital_debt:  { label: 'Natural Capital Debt', unit: '$',    format: _money, goodDirection: -1 },
  carbon_intensity:      { label: 'Carbon Intensity',    unit: 'tCO₂e', format: _score, goodDirection: -1 },
  water_dependency:      { label: 'Water Dependency',    unit: '%',     format: _pct,   goodDirection: -1 },
  staff_burnout_index:   { label: 'Staff Burnout',       unit: 'score', format: _score, goodDirection: -1 },
  regenerative_multiple: { label: 'Regenerative Multiple', unit: '×',   format: _ratio, goodDirection: +1 },
};

/** Canonical display label for a metric key (falls back to a humanized key). */
export function kpiLabel(key) {
  return KPI[key]?.label || String(key || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Format a metric value using its canonical formatter. */
export function formatKpi(key, value) {
  const fmt = KPI[key]?.format || _score;
  return fmt(value);
}

/**
 * Format a delta with sign and a semantic direction flag so callers can color
 * it with tokens.css danger/success (never raw hex — see CLAUDE.md).
 * Returns { text, isGood } where isGood aligns with the metric's goodDirection.
 */
export function formatKpiDelta(key, delta) {
  if (delta == null || isNaN(delta) || delta === 0) {
    return { text: '—', isGood: null };
  }
  const meta = KPI[key];
  /* The old line ended `.replace(/^[$]?/, (m) => m)` — a no-op that replaced
     the currency symbol with itself. Whatever it was meant to strip, it never
     did. utils/format.delta owns the sign glyph now (U+2212, not a hyphen, so
     it aligns in a tabular column). */
  const dir = meta?.goodDirection ?? +1;
  return {
    text: _fmtDelta(delta, meta ? meta.format : _score),
    isGood: direction(delta, dir > 0) > 0,
  };
}
