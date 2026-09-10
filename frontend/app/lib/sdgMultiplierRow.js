/**
 * The M_SDG line of the finale's terminal-valuation waterfall — read from the
 * engine, never recomputed.
 *
 * Found by the scripted classroom rehearsal (2026-09-10): GameOverSummary
 * recomputed M_SDG from `sdg_impact_score` with the 2026.09 arithmetic
 * (neutral 0) and printed "not used this run" unless the Corporate SDG side
 * track had been played. Under the 2026.10 rule set the engine's M_SDG is
 * 1 + ((sdg_index − neutral) / 100) × coeff and is ALWAYS in the product, so
 * the rehearsal seat's screen read "not used this run" on the row and
 * "M_SDG(1.25×)" in the formula caption while the engine had used 1.0635×
 * (EBITDA $31.4M × 18.0 × 1.77 × 1.0635 = the $1,064.39M it printed). The
 * finale payload carries `sdg_multiplier`, `sdg_impact_score`, `sdg_neutral`
 * and `sdg_coeff` (round_logic writes all four in both finale paths); this
 * helper reads them, and only a payload written before those keys existed
 * falls back to the old arithmetic.
 *
 * Pure: (report, flags) → { mSdg, used, score, neutral, coeff, desc }.
 */
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const pick = (report, flags, key) => num(report?.[key]) ?? num(flags?.[key]);
const fmt = (v) => (Number.isInteger(v) ? String(v) : String(+v.toFixed(2)));

export function sdgMultiplierRow(report, flags) {
  const reported = pick(report, flags, 'sdg_multiplier');
  const completed = Boolean(report?.sdg_track_completed || flags?.sdg_track_completed);
  const score = pick(report, flags, 'sdg_impact_score');

  if (reported == null) {
    // A payload from before the engine reported its multiplier: the 2026.09
    // arithmetic from the side track's score, exactly as the screen used to print it.
    const safe = score ?? 0;
    return {
      mSdg: 1.0 + (safe / 100.0) * 0.25,
      used: completed,
      score: safe, neutral: 0, coeff: 0.25,
      desc: `SDG Impact Score: ${fmt(safe)}/105 → M_SDG = 1.0 + (${fmt(safe)}/100) × 0.25`,
    };
  }

  const neutral = pick(report, flags, 'sdg_neutral') ?? 0;
  const coeff = pick(report, flags, 'sdg_coeff') ?? 0.25;
  const safe = score ?? neutral;
  // 2026.09 without the side track: the score is 0 against a neutral of 0 and the
  // multiplier is exactly 1 — the dimension really was inert, say so as before.
  const inert = !completed && neutral === 0 && Math.abs(reported - 1) < 1e-9;
  const desc = neutral === 0
    ? `SDG Impact Score: ${fmt(safe)}/105 → M_SDG = 1.0 + (${fmt(safe)}/100) × ${fmt(coeff)}`
    : `SDG index ${fmt(safe)} vs neutral ${fmt(neutral)} → M_SDG = 1.0 + ((${fmt(safe)} − ${fmt(neutral)})/100) × ${fmt(coeff)}`;
  return { mSdg: reported, used: !inert, score: safe, neutral, coeff, desc };
}
