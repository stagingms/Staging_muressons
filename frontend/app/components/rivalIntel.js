/**
 * rivalIntel.js — W-B (W2 + W6)
 *
 * Pure, deterministic derivations that give the NPC competitor a face
 * ("Nordhaven Group") and add an ESG rating-agency narrative ("Meridian
 * ESG Ratings"). Everything here is computed from data the engine already
 * produces (history snapshots) — no fetches, no state writes, and no
 * randomness: same history in ⇒ same intel out, preserving the sim's
 * shared-dice determinism doctrine.
 */

/* A11Y-M2 (WCAG 1.4.3): `color` is the identity hue and stays — it paints the
   card's 3px left border, where contrast does not apply. `textColor` is the
   same identity in the semantic text tier, which flips per theme, and is what
   the name label uses: as TEXT the raw hues measured 3.71:1 (rival) and
   3.16:1 (agency) on the dark card. */
export const RIVAL = { name: 'Nordhaven Group', avatar: '🏛️', color: '#64748b', textColor: 'var(--text-muted)' };
export const AGENCY = { name: 'Meridian ESG Ratings', avatar: '⚖️', color: '#7c3aed', textColor: 'var(--accent-text)' };

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const M = (v) => `$${((v || 0) / 1_000_000).toFixed(1)}M`;

// Per-round player EBITDA — same definition as the cockpit's historyData:
// Σ(revenue − opex) over the round's BU table, falling back to the stored
// per-round historical_ebitda.
function perRoundEbitda(h) {
  const bus = h?.business_units || [];
  return bus.length > 0
    ? bus.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0)
    : Math.max(0, h?.global_state?.historical_ebitda || 0);
}

/**
 * W2 — Rival press release for the latest committed round.
 * Tone bands on relative advantage (player EBITDA / rival EBITDA):
 *   ≥ 1.15 defensive · ≥ 1.00 neutral · ≥ 0.85 confident · < 0.85 aggressive
 * Returns null until a committed round carries competitor_ebitda.
 */
export function deriveRivalRelease(history) {
  const rows = (history || []).filter(h => (h?.global_state?.competitor_ebitda || 0) > 0);
  if (rows.length === 0) return null;
  const h = rows[rows.length - 1];
  const round = h.round_number || rows.length;
  const rival = h.global_state.competitor_ebitda;
  const player = perRoundEbitda(h);
  const adv = rival > 0 ? player / rival : 1.0;

  let tone, title, body;
  if (adv >= 1.15) {
    tone = 'defensive';
    title = 'Nordhaven vows to “close the gap” after Muressons outperforms';
    body = `Nordhaven Group reported ${M(rival)} EBITDA for the period against Muressons' ${M(player)} — a ${adv.toFixed(2)}× advantage to Muressons. Nordhaven's chief executive promised shareholders an “aggressive efficiency programme” and hinted at portfolio disposals next period.`;
  } else if (adv >= 1.0) {
    tone = 'neutral';
    title = 'Nordhaven posts steady quarter; analysts call the race “too close to call”';
    body = `Nordhaven Group delivered ${M(rival)} EBITDA, broadly in line with Muressons' ${M(player)} (${adv.toFixed(2)}×). Sector analysts note both groups face the same regulatory and climate headwinds — execution will decide the spread.`;
  } else if (adv >= 0.85) {
    tone = 'confident';
    title = 'Nordhaven edges ahead on operating margin';
    body = `Nordhaven Group posted ${M(rival)} EBITDA, ahead of Muressons' ${M(player)} (relative position ${adv.toFixed(2)}×). Nordhaven credits “disciplined capital allocation” — its investor letter singles out Muressons' cost base as “structurally heavier.”`;
  } else {
    tone = 'aggressive';
    title = 'Nordhaven announces record margins as Muressons trails';
    body = `Nordhaven Group announced record EBITDA of ${M(rival)} — well clear of Muressons' ${M(player)} (${adv.toFixed(2)}×). Nordhaven's CEO told investors the group is “consolidating leadership while competitors restructure,” and analysts are asking whether Muressons' strategy is working.`;
  }

  return { round, tone, title, body, advantage: Math.round(adv * 100) / 100 };
}

// ── W6: rating machinery ─────────────────────────────────────────
const GRADES = ['CCC', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA'];

// Factor subscores (0–100, higher = better), from state the engine already
// tracks. Weights sum to 1. Fully deterministic.
export function ratingFactors(h) {
  const gs = h?.global_state || {};
  const bus = h?.business_units || [];
  const reputation = clamp(gs.group_reputation ?? 50, 0, 100);
  const avgCI = bus.length ? bus.reduce((s, b) => s + (b.carbon_intensity || 0), 0) / bus.length : 50;
  const avgNCD = bus.length ? bus.reduce((s, b) => s + (b.natural_capital_debt || 0), 0) / bus.length : 0;
  const wacc = gs.cost_of_capital ?? 0.05;
  return {
    reputation: { label: 'stakeholder reputation', score: reputation, weight: 0.45 },
    carbon: { label: 'carbon intensity trajectory', score: clamp(100 - avgCI, 0, 100), weight: 0.25 },
    naturalCapital: { label: 'natural-capital debt', score: clamp(100 - avgNCD, 0, 100), weight: 0.15 },
    capitalAccess: { label: 'cost-of-capital resilience', score: clamp(100 - (wacc - 0.05) * 2000, 0, 100), weight: 0.15 },
  };
}

export function ratingGrade(h) {
  const f = ratingFactors(h);
  const score = Object.values(f).reduce((s, x) => s + x.score * x.weight, 0);
  const letter = score >= 80 ? 'AAA' : score >= 72 ? 'AA' : score >= 64 ? 'A'
    : score >= 56 ? 'BBB' : score >= 48 ? 'BB' : score >= 40 ? 'B' : 'CCC';
  return { letter, score: Math.round(score * 10) / 10, factors: f };
}

/**
 * W6 — Meridian ESG rating letter. Issued on EVEN committed rounds only
 * (the agency "reviews semi-annually"). Direction compares to the previous
 * even-round review. Rationale names the strongest and weakest factor.
 * Returns null until the first even round is committed.
 */
export function deriveRatingLetter(history) {
  const evens = (history || []).filter(h => ((h?.round_number || 0) % 2) === 0 && (h?.round_number || 0) > 0);
  if (evens.length === 0) return null;
  const cur = evens[evens.length - 1];
  const prev = evens.length > 1 ? evens[evens.length - 2] : null;
  const g = ratingGrade(cur);
  const pg = prev ? ratingGrade(prev) : null;

  const gi = GRADES.indexOf(g.letter);
  const pi = pg ? GRADES.indexOf(pg.letter) : null;
  const direction = pi == null ? 'initiated' : gi > pi ? 'upgrade' : gi < pi ? 'downgrade' : 'affirmed';

  const entries = Object.values(g.factors);
  const best = entries.reduce((a, b) => (b.score > a.score ? b : a));
  const worst = entries.reduce((a, b) => (b.score < a.score ? b : a));
  const rationale = `Supported by ${best.label} (${Math.round(best.score)}/100); principal constraint is ${worst.label} (${Math.round(worst.score)}/100).`;

  return {
    round: cur.round_number,
    grade: g.letter,
    score: g.score,
    direction,
    prevGrade: pg ? pg.letter : null,
    rationale,
  };
}

/**
 * W2c — Nordhaven benchmark enterprise value for the Trading-Floor board.
 * Mirrors the engine's NPC model (baseline EBITDA compounding at the default
 * competitor growth rate) × the baseline exit multiple. Presentation-only
 * estimate; clearly labelled EST on the board.
 */
export function rivalBenchmarkEV(maxRound, baseEbitda = 19_200_000, growth = 0.03, exitMultiple = 17) {
  const r = Math.max(1, Number(maxRound) || 1);
  return baseEbitda * Math.pow(1 + growth, r - 1) * exitMultiple;
}
