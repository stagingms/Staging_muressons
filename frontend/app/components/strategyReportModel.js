/**
 * strategyReportModel — the rows of the Strategy Report's Decision Timeline.
 *
 * F05 (audit AUDIT_Engines_Flow_Classroom50_20260909, P1). StudentReportExport
 * read `h.treasury ?? h.corporate_treasury ?? 0` off a dashboard history row.
 * Neither key exists — a row is {round_number, choice_selected, global_state,
 * business_units} with the balance at global_state.corporate_treasury — so the
 * take-home report printed "$0" for every round (the audit generated the HTML
 * from a schema-valid $50M row and got `$0`). The same defect was fixed for
 * the key-insights block (lib/keyInsights.js) but not here.
 *
 * History convention (history_semantics.py / WP-19): row K is the state
 * ENTERING round K; `choice_selected` on row K is the decision MADE in K. So a
 * decision's opening treasury is row K's and its closing treasury is row K+1's
 * — or, for the last round played, the closing state (`globalState`, which
 * the game-over path sets from the R10 commit). The report shows both, so a
 * participant can see what each decision started from and what it produced,
 * rather than one unlabelled number.
 *
 * Pillar rounds (multi_toggles): the commit translates the pillar set to a
 * proxy letter for the round engine, and that letter is what the decision log
 * carries. The flags entering the NEXT round carry `pillar_selections`, so a
 * pillar round is labelled by its selections, not the proxy letter.
 */
const OPTION_LABEL = { option_a: 'Option A', option_b: 'Option B', option_c: 'Option C' };

const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : null);

export function labelChoice(row, nextRow) {
  const nextFlags = nextRow?.global_state?.active_event_flags || {};
  const pillars = nextFlags.pillar_selections;
  if (pillars && typeof pillars === 'object' && Object.keys(pillars).length > 0) {
    return Object.values(pillars)
      .map((p) => (p && typeof p === 'object' ? (p.title || p.action_key) : String(p)))
      .filter(Boolean)
      .join(' · ');
  }
  const key = row?.choice_title || row?.choice_label || row?.choice_selected || '';
  return key ? (OPTION_LABEL[key] || key) : '—';
}

/**
 * @param {Array} history  dashboard history rows (entering-state convention)
 * @param {Object} globalState  the current / closing state (for the last row)
 * @returns {Array<{round:number, choice:string, opening:number|null, closing:number|null, delta:number|null}>}
 */
export function strategyReportRows(history, globalState) {
  const all = Array.isArray(history) ? history.filter((h) => h && Number.isFinite(Number(h.round_number))) : [];
  const rows = all.filter((h) => !h.is_final).slice()
    .sort((a, b) => Number(a.round_number) - Number(b.round_number));
  const byRound = new Map(rows.map((h) => [Number(h.round_number), h]));
  // The closing state of the last round played: an explicit is_final row
  // (exports fetched with include_final) or, once the game is over, the
  // current state (the game-over path sets it from the R10 commit). While
  // the game is still in play the last round has no closing balance yet.
  const finalRow = all.find((h) => h.is_final);
  const flags = globalState?.active_event_flags || {};
  const gameOver = !!(finalRow || globalState?.game_over || flags.game_over || flags.profile);
  const closingState = finalRow
    ? num(finalRow.global_state?.corporate_treasury)
    : (gameOver ? num(globalState?.corporate_treasury) : null);
  return rows.map((h) => {
    const round = Number(h.round_number);
    const next = byRound.get(round + 1);
    const opening = num(h.global_state?.corporate_treasury);
    const closing = next ? num(next.global_state?.corporate_treasury) : closingState;
    return {
      round,
      choice: labelChoice(h, next),
      opening,
      closing,
      delta: opening != null && closing != null ? Math.round((closing - opening) * 100) / 100 : null,
    };
  });
}

export default strategyReportRows;
