/**
 * Five-year decision ledger + the three key insights, derived from the REAL
 * per-round history the dashboard already returns.
 *
 * Why this module exists
 * ----------------------
 * The insights block in GameOverSummary read `h.treasury ?? h.corporate_treasury`
 * off each history row. Neither key is on a history row — the shape is
 *
 *     { round_number, choice_selected, business_units, global_state }
 *
 * and the treasury lives at `global_state.corporate_treasury`. Every delta
 * therefore computed as `0 - 0`, `best` and `worst` collapsed onto the same
 * (last) row, and the class was shown "Best Decision … +$0.0M" alongside
 * "Most Costly Mistake … $0.0M" for the SAME round. Reading real numbers is
 * only half the fix: the other half is refusing to print an insight the data
 * does not support, which is what `deriveKeyInsights` returns null for.
 *
 * Both the game-over insights section and the newspaper's INSIDE THE NUMBERS
 * column import from here, so the two can never disagree.
 */

/** Round titles as scripted by the engine's round flow. */
export const ROUND_NAMES = {
  1: 'ESG Audit',
  2: 'Double Materiality',
  3: 'Scope 3 Emissions',
  4: 'Contagion Crisis',
  5: 'Climate Event',
  6: 'AI Bias Scandal',
  7: 'Circular Economy',
  8: 'Water Scarcity',
  9: 'Just Transition',
  10: 'Grand Finale',
};

/** The one true treasury accessor for a history row. */
export function rowTreasury(h) {
  if (!h) return null;
  const v =
    h.global_state?.corporate_treasury ??
    h.corporate_treasury ??
    h.treasury;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function rowReputation(h) {
  const n = Number(h?.global_state?.group_reputation ?? h?.group_reputation);
  return Number.isFinite(n) ? n : null;
}

/** "option_b" → "Option B". Returns null rather than inventing a label. */
export function choiceLabel(h) {
  if (h?.choice_title) return h.choice_title;
  if (h?.choice_label) return h.choice_label;
  const raw = h?.choice_selected || h?.choice;
  if (typeof raw !== 'string' || !raw) return null;
  const m = /^option_([a-z])$/i.exec(raw);
  return m ? `Option ${m[1].toUpperCase()}` : raw;
}

/**
 * The full ten-round ledger: closing treasury per round and the change from
 * the previous close.
 *
 * Round 1 gets `delta: null`, not 0. Its opening balance is not in `history`
 * (the first row is already a CLOSE), and the engine's starting treasury can
 * be inherited from a parent track, so assuming $50M would be a guess. A
 * missing number prints as "—"; it never competes to be the best or worst
 * decision.
 */
export function roundLedger(history) {
  if (!Array.isArray(history)) return [];
  const rows = history
    .map((h) => ({ h, round: Number(h?.round_number) }))
    .filter((r) => Number.isFinite(r.round))
    .sort((a, b) => a.round - b.round);

  let prev = null;
  return rows.map(({ h, round }) => {
    const treasury = rowTreasury(h);
    const delta = prev !== null && treasury !== null ? treasury - prev : null;
    if (treasury !== null) prev = treasury;
    return {
      round,
      name: ROUND_NAMES[round] || null,
      choice: choiceLabel(h),
      treasury,
      delta,
      reputation: rowReputation(h),
    };
  });
}

/**
 * Best decision, most costly decision, and the sharpest reputation swing.
 *
 * Returns `null` — meaning "print nothing" — whenever the data cannot tell
 * these apart:
 *   • fewer than two rounds carry a real delta;
 *   • every delta is identical (nothing distinguishes a best from a worst);
 *   • best and worst resolve to the same round.
 * Each of those was reachable before, and each produced a confidently-worded
 * claim about a round the numbers said nothing about.
 */
export function deriveKeyInsights(history) {
  const ledger = roundLedger(history);
  const scored = ledger.filter((r) => Number.isFinite(r.delta));
  if (scored.length < 2) return null;

  const best = scored.reduce((a, b) => (b.delta > a.delta ? b : a), scored[0]);
  const worst = scored.reduce((a, b) => (b.delta < a.delta ? b : a), scored[0]);
  if (best.round === worst.round) return null;
  if (best.delta === worst.delta) return null;

  // Reputation swing: real only if reputation was actually tracked and moved.
  let swing = null;
  const repRows = ledger.filter((r) => Number.isFinite(r.reputation));
  if (repRows.length >= 2) {
    let prev = repRows[0];
    let biggest = null;
    for (let i = 1; i < repRows.length; i += 1) {
      const d = repRows[i].reputation - prev.reputation;
      if (biggest === null || Math.abs(d) > Math.abs(biggest.change)) {
        biggest = { ...repRows[i], change: d, from: prev.reputation };
      }
      prev = repRows[i];
    }
    if (biggest && Math.abs(biggest.change) >= 0.5) swing = biggest;
  }

  return { best, worst, swing, ledger };
}

/** $-12.3M / +$4.0M, with a real minus sign. Null-safe: returns '—'. */
export function fmtDeltaM(v) {
  if (!Number.isFinite(v)) return '—';
  const m = v / 1_000_000;
  return `${m < 0 ? '−' : '+'}$${Math.abs(m).toFixed(1)}M`;
}

export function fmtM(v) {
  if (!Number.isFinite(Number(v))) return '—';
  const m = Number(v) / 1_000_000;
  const a = Math.abs(m);
  return `${m < 0 ? '−' : ''}$${a >= 100 ? a.toFixed(0) : a.toFixed(1)}M`;
}
