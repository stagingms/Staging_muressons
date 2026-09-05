/**
 * mrJourney.js — the M_R-bearing decisions across the 5-year journey.
 *
 * Mirrors the positive/blocked M_R effects in backend terminal_valuation.py's
 * FLAG_DEPENDENCY_GRAPH (the backend remains the source of truth for scoring —
 * this is a presentation-only copy used by the Regret Meter and Rewind Ribbon).
 *
 * Each opportunity: the round it's decided, the flag that captures it, the M_R
 * it's worth, and a short label. `blockedBy` marks a bonus that a *different*
 * choice forfeits (e.g. insurance-only blocks the resilience bonus).
 */
/**
 * F-15 (audit 2026-09-04): each opportunity now also names the ARBITER's
 * breakdown key (terminal_valuation.calculate_mr → flags.mr_breakdown) and
 * the round/option that earns it, so "earned" is read from what the finale
 * actually awarded rather than from a client-side flag table — and the
 * flag fallback (mid-game, before mr_breakdown exists) looks inside the
 * `rN_flags` lists where production stores every strategic flag.
 */
export const MR_OPPORTUNITIES = [
  { round: 2, flag: 'materiality_aligned',  breakdownKey: 'materiality_governance', mr: 0.10, label: 'Double-Materiality Alignment', category: 'governance', option: 'A', optionLabel: 'Full Materiality Alignment (≥80% matrix accuracy)' },
  // NOTE: "Early Decarbonisation +0.10" was listed here as an M_R lever; the
  // arbiter has no such component — early_decarboniser is a +0.10 SYNERGY
  // MULTIPLIER effect (flag graph), so it no longer inflates the ladder.
  { round: 6, flag: 'ethical_ai_overhaul',  breakdownKey: 'truth_premium',          mr: 0.15, label: 'Ethical-AI Overhaul',           category: 'governance', option: 'B', optionLabel: 'Ethical AI Overhaul' },
  { round: 7, flag: 'synergy_unlock',       breakdownKey: 'synergy_bonus',          mr: 0.15, label: 'Cross-BU Synergy Unlock',       category: 'strategic',  option: 'C', optionLabel: 'Waste-to-Energy Partnership' },
  { round: 9, flag: 'community_fund',        breakdownKey: 'community_champion_bonus', mr: 0.18, label: 'Community Champion Fund',     category: 'social',     option: 'C', optionLabel: 'Community Investment Fund', altBreakdownKey: 'just_transition_bonus' },
  // The +0.20 Resilience bonus is available UNLESS a defensive choice blocks it.
  { round: 5, flag: '__resilience__', breakdownKey: 'resilience_bonus', mr: 0.20, label: 'Climate Resilience Investment', category: 'climate', option: 'A/B', optionLabel: 'Hard Engineering or Nature-Based Solutions',
    blockedByFlags: ['insurance_only', 'electronics_water_priority', 'civil_water_priority'] },
];

/**
 * Is `name` set in this flag dict, the way the backend's collect_all_flags
 * reads it: a truthy top-level boolean, a string value equal to the name, or
 * a member of any list-valued entry (`r7_flags: ["synergy_unlock"]`).
 */
export function hasFlag(flags, name) {
  if (!flags || !name) return false;
  if (flags[name] === true) return true;
  for (const [k, v] of Object.entries(flags)) {
    if (typeof k === 'string' && k.startsWith('_')) continue;
    if (Array.isArray(v) && v.some((x) => String(x) === name)) return true;
    if (typeof v === 'string' && v === name) return true;
  }
  return false;
}

/**
 * Classify every opportunity as captured or missed and total the M_R "left on
 * the table". When the finale's `mr_breakdown` is present (flags.mr_breakdown,
 * or passed explicitly) the ARBITER decides: a component is captured iff the
 * breakdown carries it with a positive value. Before the finale, fall back to
 * the list-aware flag reading. Conservative either way.
 */
export function computeMrRegret(activeFlags = {}, mrBreakdown = null) {
  const flags = activeFlags || {};
  const bd = mrBreakdown && typeof mrBreakdown === 'object' ? mrBreakdown
    : (flags.mr_breakdown && typeof flags.mr_breakdown === 'object' ? flags.mr_breakdown : null);
  const items = MR_OPPORTUNITIES.map((op) => {
    let captured;
    let mrValue = op.mr;
    if (bd && op.breakdownKey) {
      const v = Number(bd[op.breakdownKey]);
      const alt = op.altBreakdownKey ? Number(bd[op.altBreakdownKey]) : 0;
      captured = (Number.isFinite(v) && v > 0) || (Number.isFinite(alt) && alt > 0);
      // the value the arbiter actually awarded (JT scaling, ramps)
      if (captured) mrValue = Math.round(((Number.isFinite(v) && v > 0) ? v : alt) * 100) / 100;
    } else if (op.blockedByFlags) {
      // Resilience: captured when NO blocking flag was chosen.
      captured = !op.blockedByFlags.some((f) => hasFlag(flags, f));
    } else {
      captured = hasFlag(flags, op.flag);
    }
    return { ...op, captured, mr: mrValue, nominalMr: op.mr };
  });
  const missed = items.filter((i) => !i.captured);
  const captured = items.filter((i) => i.captured);
  const mrLeftOnTable = Math.round(missed.reduce((s, i) => s + i.mr, 0) * 100) / 100;
  const mrCaptured = Math.round(captured.reduce((s, i) => s + i.mr, 0) * 100) / 100;
  return { items, missed, captured, mrLeftOnTable, mrCaptured, source: bd ? 'mr_breakdown' : 'flags' };
}
