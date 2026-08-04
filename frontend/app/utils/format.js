/**
 * format.js — the single place a number becomes a string.
 *
 * WHY THIS EXISTS
 *   Before this module there were three systems and they disagreed:
 *
 *     formatCurrency.js  hard-coded '$', ignored the session currency entirely
 *     kpiFormats.js      built on formatCurrency, so also always '$'
 *     CurrencyContext    session-aware, but only reachable from inside React
 *
 *   That is why a cohort running in rupees saw '₹16.6M' in the BU strip and
 *   '$11.62' in the share price ON THE SAME SCREEN. It was never a styling
 *   inconsistency; it was a bug with a styling symptom.
 *
 *   It is also why the same score rendered '1.4237×' on the archetype reveal
 *   and '1.42×' on the scorecard one screen later, and why '$99.4M' and
 *   '$104M' could sit in one column — each call site chose its own precision.
 *
 * THE RULE
 *   One symbol, resolved at the root. One precision policy per unit class.
 *   One minus glyph (U+2212, which aligns in tabular figures — the ASCII
 *   hyphen does not). One placeholder for "not recorded" (U+2014).
 *
 * HOW THE SYMBOL GETS HERE
 *   These are plain functions, called from render bodies and from module
 *   scope, so they cannot use a React hook. CurrencyProvider pushes the active
 *   symbol in via setCurrencySymbol() whenever it changes; everything below
 *   reads that one value. There is exactly one writer.
 */

const MINUS = '−';   // U+2212 MINUS SIGN — same advance width as a digit
const EMPTY = '—';   // U+2014 EM DASH — "not recorded", never "zero"

let _symbol = '₹';        // matches CurrencyContext's DEFAULT_CURRENCY

/** Called by CurrencyProvider. The only writer. */
export function setCurrencySymbol(symbol) {
  if (typeof symbol === 'string' && symbol) _symbol = symbol;
}
export function currencySymbol() {
  return _symbol;
}

const isNum = (v) => v !== null && v !== undefined && v !== '' && !isNaN(Number(v));
const sign = (v) => (v < 0 ? MINUS : '');

/**
 * Money. One ladder, applied everywhere:
 *   ≥ 1B → 2dp   ≥ 1M → 1dp   ≥ 1K → 0dp   else 0dp
 *
 * 1dp at the millions step is deliberate: treasury, EBITDA and allocations all
 * live there, and '₹11.0M' is the figure a team argues about. 2dp there buys
 * false precision on an engine output; 0dp hides a ₹400K swing.
 */
export function money(value, { dp } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  const abs = Math.abs(v);
  const s = sign(v);
  if (abs >= 1e9) return `${s}${_symbol}${(abs / 1e9).toFixed(dp ?? 2)}B`;
  if (abs >= 1e6) return `${s}${_symbol}${(abs / 1e6).toFixed(dp ?? 1)}M`;
  if (abs >= 1e3) return `${s}${_symbol}${(abs / 1e3).toFixed(dp ?? 0)}K`;
  return `${s}${_symbol}${abs.toFixed(dp ?? 0)}`;
}

/**
 * Money pinned to millions, whatever the magnitude.
 *
 * money()'s ladder is right for a single figure but wrong for a ROW of them:
 * NOPAT ₹8.6M / Carbon Charge ₹600K / Adj. Capital ₹26.2M reads as three
 * unrelated quantities, because the reader has to re-scale between columns.
 * Where figures are meant to be compared against each other, pin the unit and
 * let the small ones show as 0.6M.
 *
 * This is the currency-aware replacement for the ~30 private
 *   const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`
 * definitions that used to live one per component.
 */
export function moneyM(value, { dp = 1 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${_symbol}${(Math.abs(v) / 1e6).toFixed(dp)}M`;
}

/**
 * A figure that is ALREADY expressed in millions — engine narratives and
 * chart axes often carry 12.3 meaning 12.3M. Prefixes the symbol and appends
 * the unit without rescaling.
 */
export function moneyMScaled(value, { dp = 1 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${_symbol}${Math.abs(v).toFixed(dp)}M`;
}

/** Money at full precision, grouped. For balance sheets, not for KPI belts. */
export function moneyFull(value, { dp = 0 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${_symbol}${Math.abs(v).toLocaleString('en-US', {
    minimumFractionDigits: dp, maximumFractionDigits: dp,
  })}`;
}

/** A price, where the cents genuinely matter. Always 2dp. */
export function price(value) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${_symbol}${Math.abs(v).toFixed(2)}`;
}

/**
 * A multiple, e.g. M_R. ALWAYS 2dp — this is the fix for the same score
 * reading 1.4237× on one screen and 1.42× on the next.
 */
export function ratio(value) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${Math.abs(v).toFixed(2)}×`;
}

/** A percentage. 1dp. */
export function percent(value, { dp = 1 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${Math.abs(v).toFixed(dp)}%`;
}

/** An index or score on an arbitrary scale. Whole numbers. */
export function score(value) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value);
  return `${sign(v)}${Math.round(Math.abs(v))}`;
}

/**
 * A change since last round. Always carries an explicit sign glyph, because
 * colour alone is not an encoding — roughly 1 in 12 men cannot use it.
 * Returns the string; the caller decides the colour from `direction`.
 */
export function delta(value, format = score) {
  if (!isNum(value) || Number(value) === 0) return EMPTY;
  const v = Number(value);
  const body = format(Math.abs(v));
  return `${v > 0 ? '+' : MINUS}${body}`;
}

/** +1 improving, −1 worsening, 0 flat — for choosing a semantic token. */
export function direction(value, higherIsBetter = true) {
  if (!isNum(value) || Number(value) === 0) return 0;
  return (Number(value) > 0) === higherIsBetter ? 1 : -1;
}

export const GLYPH = { MINUS, EMPTY };

export default {
  setCurrencySymbol, currencySymbol,
  money, moneyM, moneyMScaled, moneyFull, price, ratio, percent, score, delta, direction, GLYPH,
};
