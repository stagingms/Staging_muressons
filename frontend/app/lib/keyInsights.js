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
import { currencySymbol, atRate } from '../utils/format';


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

/** How many rounds the plan runs; the closing state is what round FINAL_ROUND produced. */
export const FINAL_ROUND = 10;

/**
 * The ten-round ledger, one row per round PLAYED: the call made in that
 * round, the treasury it closed on, and the change that call produced.
 *
 * A dashboard history row K is the state ENTERING round K — row 1 is the
 * seed, row K+1 is what round K's decision produced — the same convention
 * the server's analytics and debrief use (SEAM-08/09, audit 2026-09-04).
 * So round K's outcome is row K+1 minus row K, its choice is row K's own
 * `choice_selected`, and round 1 has a real delta (the seed is its opening
 * balance). The history never carries what round 10 produced: pass the
 * closing state as `closing` (the game-over global_state, or the final
 * report's final_treasury / group_reputation) and the last round gets its
 * outcome. Without it — or for a round still being played — the round has
 * nothing to report and is not listed.
 *
 * Before this the ledger read row K as the CLOSE of round K: every delta
 * was the previous round's outcome under this round's choice, round 1 was
 * printed as "no change", and round 10's actual result never appeared.
 */
export function roundLedger(history, closing = null) {
  if (!Array.isArray(history)) return [];
  const rows = history
    .filter((h) => h && !h.is_final)
    .map((h) => ({ h, round: Number(h?.round_number) }))
    .filter((r) => Number.isFinite(r.round))
    .sort((a, b) => a.round - b.round);
  const closingRow = closing
    ? (closing.global_state ? closing : { global_state: closing })
    : null;
  const out = [];
  for (let i = 0; i < rows.length; i += 1) {
    const { h, round } = rows[i];
    let next = null;
    if (i + 1 < rows.length) next = rows[i + 1].h;
    else if (closingRow && round >= FINAL_ROUND) next = closingRow;
    if (!next) break; // the round in play — no outcome yet
    const opening = rowTreasury(h);
    const treasury = rowTreasury(next);
    const delta = opening !== null && treasury !== null ? treasury - opening : null;
    out.push({
      round,
      name: ROUND_NAMES[round] || null,
      choice: choiceLabel(h),
      opening,
      treasury,
      delta,
      reputation_from: rowReputation(h),
      reputation: rowReputation(next),
    });
  }
  return out;
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
export function deriveKeyInsights(history, closing = null) {
  const ledger = roundLedger(history, closing);
  const scored = ledger.filter((r) => Number.isFinite(r.delta));
  if (scored.length < 2) return null;
  const best = scored.reduce((a, b) => (b.delta > a.delta ? b : a), scored[0]);
  const worst = scored.reduce((a, b) => (b.delta < a.delta ? b : a), scored[0]);
  if (best.round === worst.round) return null;
  if (best.delta === worst.delta) return null;
  // Reputation swing: the round whose call moved reputation the most —
  // real only if reputation was actually tracked and moved.
  let swing = null;
  let biggest = null;
  for (const r of ledger) {
    if (!Number.isFinite(r.reputation) || !Number.isFinite(r.reputation_from)) continue;
    const d = r.reputation - r.reputation_from;
    if (biggest === null || Math.abs(d) > Math.abs(biggest.change)) {
      biggest = { ...r, change: d, from: r.reputation_from };
    }
  }
  if (biggest && Math.abs(biggest.change) >= 0.5) swing = biggest;
  return { best, worst, swing, ledger };
}

/** $-12.3M / +$4.0M, with a real minus sign. Null-safe: returns '—'. */
export function fmtDeltaM(v) {
  if (!Number.isFinite(v)) return '—';
  const m = atRate(v) / 1_000_000;
  return `${m < 0 ? '−' : '+'}${currencySymbol()}${Math.abs(m).toFixed(1)}M`;
}

export function fmtM(v) {
  if (!Number.isFinite(Number(v))) return '—';
  const m = atRate(v) / 1_000_000;
  const a = Math.abs(m);
  return `${m < 0 ? '−' : ''}${currencySymbol()}${a >= 100 ? a.toFixed(0) : a.toFixed(1)}M`;
}
