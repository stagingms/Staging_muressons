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
export const MR_OPPORTUNITIES = [
  { round: 2, flag: 'materiality_aligned',  mr: 0.10, label: 'Double-Materiality Alignment', category: 'governance' },
  { round: 3, flag: 'early_decarboniser',   mr: 0.10, label: 'Early Decarbonisation',         category: 'climate' },
  { round: 6, flag: 'ethical_ai_overhaul',  mr: 0.15, label: 'Ethical-AI Overhaul',           category: 'governance' },
  { round: 7, flag: 'synergy_unlock',       mr: 0.15, label: 'Cross-BU Synergy Unlock',       category: 'strategic' },
  { round: 9, flag: 'community_fund',        mr: 0.18, label: 'Community Champion Fund',       category: 'social' },
  // The +0.20 Resilience bonus is available UNLESS a defensive choice blocks it.
  { round: 5, flag: '__resilience__', mr: 0.20, label: 'Climate Resilience Investment', category: 'climate',
    blockedByFlags: ['insurance_only', 'electronics_water_priority'] },
];

/**
 * Given the team's active flags, classify every opportunity as captured or missed
 * and total the M_R "left on the table". Conservative: an opportunity only counts
 * as captured when its flag is set (or, for resilience, when no blocking flag is set).
 */
export function computeMrRegret(activeFlags = {}) {
  const flags = activeFlags || {};
  const items = MR_OPPORTUNITIES.map((op) => {
    let captured;
    if (op.blockedByFlags) {
      // Resilience: captured when NO blocking flag was chosen.
      captured = !op.blockedByFlags.some((f) => flags[f]);
    } else {
      captured = !!flags[op.flag];
    }
    return { ...op, captured };
  });
  const missed = items.filter((i) => !i.captured);
  const captured = items.filter((i) => i.captured);
  const mrLeftOnTable = Math.round(missed.reduce((s, i) => s + i.mr, 0) * 100) / 100;
  const mrCaptured = Math.round(captured.reduce((s, i) => s + i.mr, 0) * 100) / 100;
  return { items, missed, captured, mrLeftOnTable, mrCaptured };
}
