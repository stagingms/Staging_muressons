/**
 * ebitdaWaterfallModel — the pure step builder behind EBITDAWaterfall.
 *
 * BUG-2026-07-29 (audit). The waterfall was invisible in normal play. It was
 * imported, rendered, and its visibility toggle defaulted ON — but it read six
 * fields and FIVE OF THEM ARE NEVER WRITTEN BY THE BACKEND:
 *
 *     capex_spent, crisis_cost, cost_impact,
 *     inflation_opex_increase, reputation_revenue_bonus     <- none exist
 *     internal_carbon_fee_deducted   <- exists, but on a path that rarely fires
 *
 * With all six zero the component hit `steps.length <= 2` and returned null,
 * silently, every round. Measured over 6 rounds of ordinary play: every one of
 * the six was 0 in every round. It was written against a contract nobody
 * implemented.
 *
 * It was also reading the wrong object: `globalState.active_event_flags ||
 * events` short-circuits on the flags object, which is almost always truthy,
 * so the round's `events` were never consulted at all.
 *
 * THE ACCOUNTING, WHICH THE OLD VERSION GOT WRONG
 * -----------------------------------------------
 * The engine defines (engine.py, _run_financial_layer):
 *
 *     historical_ebitda = sum(revenue_base - opex_base for bu in bus)
 *
 * EBITDA here IS gross margin — nothing else is subtracted. Verified to the
 * cent across rounds 1-3 (delta 0.00). So the old chart, which deducted carbon
 * tax and crisis cost *from EBITDA*, was not merely empty — it was
 * financially wrong. Those costs hit TREASURY, not EBITDA.
 *
 * Presenting that to a finance audience would teach the wrong model, so the
 * bridge is now explicitly two sections:
 *
 *   Section 1  Revenue - OPEX = EBITDA        <- reconciles exactly, checkpoint
 *   Section 2  below EBITDA: what moved CASH  <- carbon, supply chain, working
 *                                                capital, synergy, crisis
 *
 * That separation is the actual lesson: a round can post healthy EBITDA and
 * still drain treasury. Section 2 is where the student sees it.
 *
 * Kept as a pure function, separate from the component, so a test can assert
 * "a real commit response produces a visible waterfall" without a DOM.
 */

/** Sum every event key matching a prefix (the engine emits per-BU keys, e.g.
 *  supply_chain_contagion_pharma / _electronics / _consumer_goods / _software). */
export function sumByPrefix(source, prefix) {
  if (!source || typeof source !== 'object') return 0;
  let total = 0;
  for (const [k, v] of Object.entries(source)) {
    if (k.startsWith(prefix) && typeof v === 'number' && Number.isFinite(v)) total += v;
  }
  return total;
}

/** Read a key the engine suffixes with the round number (midgame_carbon_cost_r3).
 *  Falls back to any round's value so the panel still works if the caller's
 *  round number is off by one at a boundary. */
export function readRoundKey(source, base, roundNumber) {
  if (!source || typeof source !== 'object') return 0;
  const exact = source[`${base}_r${roundNumber}`];
  if (typeof exact === 'number' && Number.isFinite(exact)) return exact;
  const plain = source[base];
  if (typeof plain === 'number' && Number.isFinite(plain)) return plain;
  const re = new RegExp(`^${base}_r\\d+$`);
  for (const [k, v] of Object.entries(source)) {
    if (re.test(k) && typeof v === 'number' && Number.isFinite(v)) return v;
  }
  return 0;
}

/**
 * Build the waterfall steps from a commit response.
 *
 * @returns {{steps: Array, ebitda: number, reconciles: boolean}}
 *   `reconciles` is true when Revenue - OPEX equals the engine's own
 *   historical_ebitda — if it ever goes false the engine's definition changed
 *   and this chart is lying, which the test asserts on.
 */
export function buildWaterfall({ businessUnits = [], globalState = {}, events = {}, commitResults = {} } = {}) {
  const bus = (businessUnits && businessUnits.length)
    ? businessUnits
    : (commitResults?.businessUnits || []);

  const totalRevenue = bus.reduce((a, b) => a + (b?.revenue_base || 0), 0);
  const totalOpex = bus.reduce((a, b) => a + (b?.opex_base || 0), 0);
  const ebitda = totalRevenue - totalOpex;

  // Read BOTH bags. The engine writes round outcomes into `events` and mirrors
  // many of them into active_event_flags; the old `flags || events` collapsed
  // to one and missed the other. Merge, with events last so the freshest wins.
  const flags = (globalState && globalState.active_event_flags) || {};
  const bag = { ...flags, ...(events || {}) };

  const roundNumber = Number(globalState?.round_number) || 0;
  const engineEbitda = Number(globalState?.historical_ebitda);
  const reconciles = Number.isFinite(engineEbitda)
    ? Math.abs(engineEbitda - ebitda) < 1
    : true;

  const steps = [
    { label: 'Revenue', value: totalRevenue, type: 'positive', icon: '💰', section: 'ebitda' },
    { label: 'OPEX', value: -totalOpex, type: 'negative', icon: '🏭', section: 'ebitda' },
    { label: 'EBITDA', value: ebitda, type: 'total', icon: '📊', section: 'ebitda' },
  ];

  // ── Below EBITDA: what actually moved cash this round ──────────────────
  // FIN-06 (audit 2026-09-04, Wave 3): when the engine's consequence waterfall
  // is a closed bridge — opening treasury → every named movement → the
  // treasury the round persisted (`bridge` present) — it IS the cash section:
  // exact, complete, and the same figures the facilitator reads. The
  // hand-picked key list below stays as the fallback for rounds committed
  // before the bridge existed.
  const bridged = bridgeSteps(bag.consequence_waterfall);
  if (bridged) {
    steps.push(...bridged.steps);
    return { steps, ebitda, reconciles, treasury: bridged.treasury };
  }

  // Every entry below is a REAL key, confirmed emitted in ordinary play.
  const cash = [];
  const push = (label, value, icon, opts = {}) => {
    if (!value || !Number.isFinite(value) || Math.abs(value) < 1) return;
    cash.push({
      label,
      value: opts.positive ? Math.abs(value) : -Math.abs(value),
      type: opts.positive ? 'positive' : 'negative',
      icon,
      section: 'cash',
    });
  };

  push('Carbon cost', readRoundKey(bag, 'midgame_carbon_cost', roundNumber)
    || bag.internal_carbon_fee_deducted, '🌡️');
  push('Supply-chain shock', sumByPrefix(bag, 'supply_chain_contagion_'), '🔗');
  push('Working-capital drag', sumByPrefix(bag, 'cash_conversion_drag_'), '⏳');
  push('Revenue cannibalised', sumByPrefix(bag, 'revenue_cannibalized_'), '🍽️');
  push('Working capital released', bag.revenue_generation_completed, '💧', { positive: true });
  push('Synergy realised', sumByPrefix(bag, 'synergy_lag_completed_'), '🔧', { positive: true });
  push('Capex overrun', bag.capex_overrun_amount, '🧱');
  push('Crisis damage', bag.actual_damage, '🚨');

  // Signed: the engine emits this negative when the market moves against them.
  const revDelta = readRoundKey(bag, 'revenue_delta_applied', roundNumber);
  if (revDelta && Math.abs(revDelta) >= 1) {
    cash.push({
      label: 'Market revenue delta',
      value: revDelta,
      type: revDelta >= 0 ? 'positive' : 'negative',
      icon: '📉',
      section: 'cash',
    });
  }

  if (cash.length) {
    steps.push(...cash);
    steps.push({
      label: 'Net cash impact',
      value: cash.reduce((a, s) => a + s.value, 0),
      type: 'total',
      icon: '🏦',
      section: 'cash',
    });
  }

  return { steps, ebitda, reconciles, treasury: null };
}

/**
 * The treasury bridge from a FIN-06 consequence waterfall (one with `bridge`).
 * Returns null for older waterfalls so the caller falls back to the key list.
 *
 * Steps: an opening total, one row per entry (the engine's own label and
 * `because`), a closing total. `closes` is the engine's own verdict that
 * opening + Σ entries == closing to the cent.
 */
export function bridgeSteps(wf) {
  if (!wf || typeof wf !== 'object' || !wf.bridge || !Array.isArray(wf.entries)) return null;
  const opening = Number(wf.initial_treasury);
  const closing = Number(wf.final_treasury);
  if (!Number.isFinite(opening) || !Number.isFinite(closing)) return null;
  const rows = [];
  rows.push({ label: 'Opening treasury', value: opening, type: 'total', icon: '🏦', section: 'cash' });
  for (const e of wf.entries) {
    const v = Number(e?.amount);
    if (!Number.isFinite(v) || Math.abs(v) < 1) continue;
    rows.push({
      label: String(e.label || 'Movement'),
      value: v,
      type: v >= 0 ? 'positive' : 'negative',
      icon: v >= 0 ? '▲' : '▼',
      section: 'cash',
      because: e.because || null,
      stage: e.stage || 'tick',
      severity: e.severity?.severity_tier || null,
    });
  }
  rows.push({ label: 'Closing treasury', value: closing, type: 'total', icon: '🏦', section: 'cash' });
  const summed = wf.entries.reduce((a, e) => a + (Number(e?.amount) || 0), 0);
  const closes = wf.bridge.closes === true && Math.abs(opening + summed - closing) < 1;
  return { steps: rows, treasury: { opening, closing, closes, unattributed: Number(wf.unattributed) || 0 } };
}

export default buildWaterfall;
