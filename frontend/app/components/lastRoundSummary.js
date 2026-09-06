/**
 * lastRoundSummary — what the briefing's "📋 Last Round Summary" shows.
 *
 * FLOW-06 (audit 2026-09-04, Wave 3). The panel read `prevRoundData.choice`,
 * `.treasury_delta`, `.reputation_delta` and `.events.strike_triggered` off a
 * history row that carries none of them (rows are {round_number, global_state,
 * business_units, choice_selected}), so it rendered empty on every briefing.
 *
 * History convention (WP-19): row K is the state ENTERING round K, and
 * `choice_selected` on row K is the choice MADE in round K. So for the
 * briefing of round N the previous round is N−1: its choice is row N−1's
 * choice_selected, and its outcome is row N minus row N−1.
 */
const OPTION_LABEL = { option_a: 'Option A', option_b: 'Option B', option_c: 'Option C' };

export function lastRoundSummary(history, roundNumber) {
  if (!Array.isArray(history) || !roundNumber || roundNumber < 2) return null;
  const prev = roundNumber - 1;
  const rowPrev = history.find((h) => h && h.round_number === prev);
  const rowNow = history.find((h) => h && h.round_number === roundNumber);
  if (!rowPrev || !rowNow) return null;
  const gsPrev = rowPrev.global_state || {};
  const gsNow = rowNow.global_state || {};
  const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : null);
  const tPrev = num(gsPrev.corporate_treasury), tNow = num(gsNow.corporate_treasury);
  const rPrev = num(gsPrev.group_reputation), rNow = num(gsNow.group_reputation);
  const choiceKey = rowPrev.choice_selected || '';
  const flagsNow = gsNow.active_event_flags || {};
  return {
    round: prev,
    choice: choiceKey ? (OPTION_LABEL[choiceKey] || choiceKey) : '',
    choice_key: choiceKey,
    treasury_delta: tPrev != null && tNow != null ? Math.round((tNow - tPrev) * 100) / 100 : undefined,
    reputation_delta: rPrev != null && rNow != null ? Math.round((rNow - rPrev) * 100) / 100 : undefined,
    // the flags entering round N carry round N−1's outcome events
    events: { strike_triggered: flagsNow.strike_triggered === true },
  };
}

export default lastRoundSummary;
