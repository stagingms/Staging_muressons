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

/* ── THE RATE ────────────────────────────────────────────────────────────────
 * Owner decision: cohort figures convert, using a factor a super admin sets on
 * the session, rather than the symbol changing while the number stays put.
 * Before this, a rupee cohort read "₹11.0M" for an engine value of 11,000,000
 * dollars — the glyph was localised and the quantity was not, which is a worse
 * lie than leaving it in dollars.
 *
 * WHERE IT IS APPLIED. Here, once, at the boundary where a number becomes a
 * string. Not in the engine: config.py's constants, the covenant thresholds
 * and every tuned ratio are expressed in engine units, and multiplying before
 * the engine would silently redefine all of them. Not in components either —
 * a component that converts on its own reintroduces exactly the three-
 * formatting-systems defect the currency pass existed to kill.
 *
 * DEFAULT 1. Until a facilitator sets a rate, every figure is unchanged. This
 * ships inert.
 */
let _rate = 1;

/** Called by CurrencyProvider. The only writer. */
export function setCurrencySymbol(symbol) {
  if (typeof symbol === 'string' && symbol) _symbol = symbol;
}
export function currencySymbol() {
  return _symbol;
}

/** Called by CurrencyProvider. The only writer. Guards hard: a rate of 0, a
 *  negative, a NaN or a string would silently zero or invert every money
 *  figure in the product, and the failure would look like an engine bug. */
export function setCurrencyRate(rate) {
  const r = Number(rate);
  if (Number.isFinite(r) && r > 0) _rate = r;
}
export function currencyRate() {
  return _rate;
}

/**
 * atRate — the rate, for the 150-odd sites that build money BY HAND.
 *
 * WHAT WENT WRONG
 *   The rate was added to money(), moneyM(), moneyFull() and the rest, and a
 *   count of their adoption looked finished. It was not. Forty-three files
 *   never call them; they take the SYMBOL from here and do the arithmetic
 *   themselves:
 *
 *     {currencySymbol()}{(team.treasury / 1_000_000).toFixed(1)}M
 *     const fmtM = (v) => `${currencySymbol()}${((v || 0) / 1e6).toFixed(1)}M`;
 *
 *   That localises the glyph and not the quantity, which is the precise defect
 *   the currency pass existed to remove and which the comment above calls a
 *   worse lie than leaving it in dollars. Nothing caught it because every
 *   currency tripwire in the suite asserts on the SYMBOL; not one asserts the
 *   rate is applied.
 *
 * WHY THIS AND NOT A MIGRATION
 *   Those 150 sites each carry a precision decision -- 1dp here, 2dp there,
 *   'k' lowercase in one module and 'K' in another. Folding them into money()
 *   would change what ~150 figures look like, with no screenshot, in a session
 *   that has already shipped four regressions found only by screenshot. So the
 *   quantity is fixed now and the appearance is not: multiplication is linear,
 *   so wrapping the numeric operand converts the figure and cannot move a
 *   decimal place. At rate 1 this is Number(v) -- an exact identity.
 *
 * IT IS A BRIDGE. Every call site here is still a private formatter that will
 * disagree with money() the day someone changes the ladder. Converging them is
 * follow-up work that needs eyes on the screens, not another sweep.
 */
export function atRate(value) {
  return Number(value) * _rate;
}

/**
 * ONE SIGNIFICANT FIGURE, for authored teaching numbers only.
 *
 * $40/tonne at a rate of 83 is ₹3,320/tonne, which reads as false precision on
 * a figure an author chose because it was round. It becomes ₹3,000.
 *
 * THIS IS FOR AUTHORED COPY AND NOTHING ELSE. Rounded numbers stop summing:
 * three option costs of ₹3,000 do not add to a rounded ₹9,000, and a team that
 * checks the arithmetic will find it does not tie. Treasury balances,
 * allocations and every computed figure keep full precision through money()
 * above. The boundary is the whole point, and it is silent when crossed, which
 * is why a tripwire pins it.
 */
export function authoredMoney(value, { unit = '' } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value) * _rate;
  const abs = Math.abs(v);
  if (abs === 0) return `${_symbol}0${unit}`;
  const mag = Math.pow(10, Math.floor(Math.log10(abs)));
  const rounded = Math.round(abs / mag) * mag;
  return `${sign(v)}${_symbol}${rounded.toLocaleString('en-US')}${unit}`;
}

/**
 * localiseAuthored — the SESSION SYMBOL AND RATE, applied to authored prose.
 *
 * THE PROBLEM THIS SOLVES
 *   authoredMoney() above takes a NUMBER. It is the right tool for a single
 *   value in a data field. It is useless for the other shape authored money
 *   takes in this product, which is a dollar sign sitting inside a sentence:
 *
 *     'every $1M of green CapEx reduces NCD by 0.5 per BU'
 *     'Internal carbon fee forcibly escalates from $40 -> $90/tonne'
 *     'Tier 3 avoidance credits cost $4 per tonne'
 *
 *   There is no number to pass. Converting these one call site at a time would
 *   mean restructuring ~90 sentences into fragments and interpolations, which
 *   is a large diff across scenario copy that no test can check the meaning of.
 *   So this takes the whole string and rewrites the amounts inside it, and is
 *   applied at the RENDER POINT — one edit per screen, not one per amount.
 *
 * IDENTITY AT RATE 1, DELIBERATELY
 *   When no rate is set, the numeral is passed through CHARACTER FOR CHARACTER
 *   and only the glyph changes. This matters: one significant figure would turn
 *   an author's '$1.2M' into '1M' and an author's '$50.00' into '50', throwing
 *   away detail that was chosen, in exchange for nothing. Rounding is right
 *   only for a number a machine just produced. So rounding is conditional on a
 *   rate actually having been applied, and this ships as a pure glyph swap.
 *
 * WHAT IT DOES NOT TOUCH
 *   A dollar sign not followed by digits. That is the guard for '$M revenue' in
 *   the glossary, where '$M' is a UNIT and converting it would be nonsense.
 *   It CANNOT guard a regex replacement string -- '$1' in a .replace() call
 *   looks identical to one dollar. That guard is the call site's job: this is
 *   for display copy, never for a replacement pattern.
 *
 * REGISTER IS PRESERVED
 *   '$900K' stays a letter suffix, '$30 million' stays a word, and
 *   '$5,000,000' stays long-form grouped. An author who wrote a figure out in
 *   full meant the weight of it, and 'R400M' does not carry that.
 */
const _AMOUNT =
  /\$\s?(\d[\d,]*(?:\.\d+)?)(?:\s*([\u2013\u2014])\s*(\d[\d,]*(?:\.\d+)?))?(?:\s?(billion|million|thousand|bn|[KMB]))?(?![A-Za-z0-9])/gi;

const _MULT = { k: 1e3, thousand: 1e3, m: 1e6, million: 1e6, b: 1e9, bn: 1e9, billion: 1e9 };

/* One significant figure, on the magnitude only. */
const _oneSigFig = (n) => {
  if (!n) return 0;
  const mag = Math.pow(10, Math.floor(Math.log10(Math.abs(n))));
  return Math.round(n / mag) * mag;
};

/* Re-render a converted magnitude in the register the author used. `word` is
   the suffix they wrote, so its capitalisation carries ('$1 Billion'). */
const _unitFor = (abs, suffix) => {
  if (!suffix) return [1, ''];
  const isWord = suffix.length > 2 || /^bn$/i.test(suffix);
  const upper = /^[A-Z]/.test(suffix);
  const cap = (w) => (upper ? w[0].toUpperCase() + w.slice(1) : w);
  const tiers = isWord
    ? [[1e9, ' ' + cap('billion')], [1e6, ' ' + cap('million')], [1e3, ' ' + cap('thousand')]]
    : [[1e9, 'B'], [1e6, 'M'], [1e3, 'K']];
  for (const t of tiers) if (abs >= t[0]) return t;
  /* Converted below the smallest suffix the author used: drop the suffix
     rather than print '0.4M'. A rate can move a figure between registers. */
  return [1, ''];
};

const _mantissa = (abs, divisor) =>
  divisor === 1 ? abs.toLocaleString('en-US') : String(Number((abs / divisor).toFixed(2)));

export function localiseAuthored(text) {
  if (typeof text !== 'string' || text.indexOf('$') === -1) return text;
  const flat = _rate === 1;
  return text.replace(_AMOUNT, (whole, lo, dash, hi, suffix) => {
    /* Glyph swap only, numeral untouched. See IDENTITY AT RATE 1 above. */
    if (flat) return _symbol + whole.slice(1);
    const mult = suffix ? _MULT[suffix.toLowerCase()] : 1;
    const conv = (t) => _oneSigFig(parseFloat(String(t).replace(/,/g, '')) * mult * _rate);
    const a = conv(lo);
    if (dash && hi) {
      /* A range carries ONE glyph and ONE suffix, as the author wrote it:
         '$1-5M', not '$1M-$5M'. Both bounds are therefore shown in the same
         unit, chosen from the larger, or '80-400M' would come out '0.08-400M'. */
      const b = conv(hi);
      const [div, label] = _unitFor(Math.max(a, b), suffix);
      return `${_symbol}${_mantissa(a, div)}${dash}${_mantissa(b, div)}${label}`;
    }
    const [div, label] = _unitFor(a, suffix);
    return `${_symbol}${_mantissa(a, div)}${label}`;
  });
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
  const v = Number(value) * _rate;
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
  const v = Number(value) * _rate;
  return `${sign(v)}${_symbol}${(Math.abs(v) / 1e6).toFixed(dp)}M`;
}

/**
 * A figure that is ALREADY expressed in millions — engine narratives and
 * chart axes often carry 12.3 meaning 12.3M. Prefixes the symbol and appends
 * the unit without rescaling.
 */
export function moneyMScaled(value, { dp = 1 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value) * _rate;
  return `${sign(v)}${_symbol}${Math.abs(v).toFixed(dp)}M`;
}

/** Money at full precision, grouped. For balance sheets, not for KPI belts. */
export function moneyFull(value, { dp = 0 } = {}) {
  if (!isNum(value)) return EMPTY;
  const v = Number(value) * _rate;
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
  setCurrencySymbol, currencySymbol, setCurrencyRate, currencyRate,
  money, moneyM, moneyMScaled, moneyFull, price, ratio, percent, score, delta, direction, GLYPH,
  authoredMoney, localiseAuthored,
};
