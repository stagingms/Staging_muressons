/**
 * greenClaimAdvice — the cockpit's pre-commit reading of the greenwash check.
 *
 * C-1 (owner calibration ruling, 2026-09-05): a green claim is backed by the
 * TEAM'S share of the CSF pool — the total allocation over the fund — or by
 * total CapEx at the absolute floor. The bars arrive on the round config
 * (`greenwash_bars`, served from the same constants the engine checks), so
 * this advice and engine.calc_greenwashing_risk cannot disagree.
 *
 * Returns null when the selected option makes no green claim; otherwise
 * { level, share, total, bar, floor, backed, message }.
 */
export const DEFAULT_GREENWASH_BARS = { full: 0.15, moderate: 0.1005, abs_capex_floor: 3_000_000 };

export function greenClaimAdvice({ option, allocations, csfPool, bars, fmtCurrency }) {
  const level = option?.green_claim;
  if (level !== 'full' && level !== 'moderate') return null;
  const b = { ...DEFAULT_GREENWASH_BARS, ...(bars || {}) };
  const total = Object.values(allocations || {}).reduce((s, v) => s + (Number(v) || 0), 0);
  const pool = Number(csfPool) || 0;
  const share = pool > 0 ? total / pool : 0;
  const bar = level === 'full' ? b.full : b.moderate;
  const floor = b.abs_capex_floor;
  const backed = share >= bar || total >= floor;
  // The cockpit passes its currency formatter (one symbol source); the bare
  // fallback carries no glyph on purpose.
  const money = fmtCurrency || ((v) => `${(v / 1e6).toFixed(1)}M`);
  const pct = (x) => `${(x * 100).toFixed(1)}%`;
  const message = backed
    ? `Green claim (${level}) backed — ${pct(share)} of the CSF pool behind it (bar ${pct(bar)}, or ${money(floor)} total).`
    : `This option makes a ${level} green claim; you have ${pct(share)} of the CSF pool behind it. ` +
      `The market wants ≥${pct(bar)} of the pool — or ≥${money(floor)} total CapEx — or it reads as greenwashing ` +
      `(social-licence penalty on every BU; stakeholders remember it as a betrayal).`;
  return { level, share, total, bar, floor, backed, message };
}
