/**
 * The EBITDA waterfall must actually render after an ordinary round.
 *
 * BUG-2026-07-29 (audit). This panel was invisible for its entire life. It was
 * imported, rendered, and its visibility toggle defaulted ON — but it read six
 * fields and FIVE ARE NEVER WRITTEN BY THE BACKEND (`capex_spent`,
 * `crisis_cost`, `cost_impact`, `inflation_opex_increase`,
 * `reputation_revenue_bonus`; the sixth, `internal_carbon_fee_deducted`, only
 * fires on a path that did not occur in 6 rounds of ordinary play).
 *
 * All six were 0 every round, so `steps.length <= 2` returned null, silently,
 * forever. Nothing errored. Nothing logged. The facilitator toggle said ON.
 *
 * A unit test of the component would have passed the whole time, because the
 * component was correct about its own (imaginary) contract. The only test that
 * catches this is one fed REAL ENGINE OUTPUT — so these fixtures are captured
 * verbatim from five consecutive commits and trimmed to the numeric fields.
 *
 * Regenerate with backend running:
 *   commit rounds 1-5, keep {businessUnits, globalState, events} per round.
 */
const fs = require('fs');
const path = require('path');

const ROUNDS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures', 'commit-rounds.json'), 'utf8'),
);

// The model is ESM; load it by stripping export keywords rather than adding a
// transform, so this test stays independent of jest config.
function loadModel() {
  const src = fs
    .readFileSync(path.join(__dirname, '..', 'app', 'components', 'ebitdaWaterfallModel.js'), 'utf8')
    .replace(/^export default .*$/m, '')
    .replace(/export /g, '');
  const module_ = {};
  // eslint-disable-next-line no-new-func
  new Function('module', `${src}\nmodule.buildWaterfall = buildWaterfall;\nmodule.sumByPrefix = sumByPrefix;\nmodule.readRoundKey = readRoundKey;`)(module_);
  return module_;
}

const { buildWaterfall, sumByPrefix, readRoundKey } = loadModel();

describe('EBITDA waterfall — real engine output', () => {
  test('the fixtures are real rounds, not an empty array', () => {
    expect(ROUNDS.length).toBeGreaterThanOrEqual(3);
    expect(ROUNDS[0].businessUnits.length).toBeGreaterThan(0);
  });

  test.each(ROUNDS.map(r => [r.round, r]))('round %i renders a visible waterfall', (n, round) => {
    const { steps } = buildWaterfall(round);
    expect(steps.length).toBeGreaterThanOrEqual(3);
    // The exact condition that used to fail: the component returns null below 3.
    expect(steps.length).not.toBeLessThan(3);
  });

  test.each(ROUNDS.map(r => [r.round, r]))(
    'round %i reconciles to the engine\'s own historical_ebitda',
    (n, round) => {
      const { ebitda, reconciles } = buildWaterfall(round);
      expect(reconciles).toBe(true);
      expect(Math.abs(ebitda - round.globalState.historical_ebitda)).toBeLessThan(1);
    },
  );

  test('every round produces at least one below-EBITDA cash movement', () => {
    // If this ever fails the panel has degenerated back to Revenue/OPEX only,
    // which is what "invisible" looked like.
    for (const round of ROUNDS) {
      const cash = buildWaterfall(round).steps.filter(s => s.section === 'cash');
      expect(cash.length).toBeGreaterThan(0);
    }
  });

  test('the EBITDA bar sits above the cash section, not inside it', () => {
    // The accounting point: engine defines historical_ebitda = revenue - opex,
    // so carbon/crisis/supply-chain costs must NOT be deducted before EBITDA.
    const { steps } = buildWaterfall(ROUNDS[ROUNDS.length - 1]);
    const ebitdaIdx = steps.findIndex(s => s.label === 'EBITDA');
    const firstCashIdx = steps.findIndex(s => s.section === 'cash');
    expect(ebitdaIdx).toBeGreaterThan(-1);
    expect(firstCashIdx).toBeGreaterThan(ebitdaIdx);
    const ebitdaStep = steps[ebitdaIdx];
    const rev = steps.find(s => s.label === 'Revenue').value;
    const opex = steps.find(s => s.label === 'OPEX').value;
    expect(Math.abs(ebitdaStep.value - (rev + opex))).toBeLessThan(1);
  });

  test('a crisis round surfaces the damage as a cash line', () => {
    const crisis = ROUNDS.find(r =>
      (r.events && r.events.actual_damage) ||
      (r.globalState.active_event_flags && r.globalState.active_event_flags.actual_damage));
    if (!crisis) return; // not every capture contains a crisis
    const labels = buildWaterfall(crisis).steps.map(s => s.label);
    expect(labels).toContain('Crisis damage');
  });

  test('dead field names alone can no longer make it render', () => {
    // The old contract, in full. If someone "restores" these names the panel
    // must still be empty-handed rather than quietly wrong.
    const fake = {
      businessUnits: [{ bu_id: 'x', revenue_base: 1000, opex_base: 400 }],
      globalState: { round_number: 1, historical_ebitda: 600, active_event_flags: {} },
      events: {
        capex_spent: 50, crisis_cost: 60, cost_impact: 70,
        inflation_opex_increase: 80, reputation_revenue_bonus: 90,
      },
    };
    const cash = buildWaterfall(fake).steps.filter(s => s.section === 'cash');
    expect(cash).toHaveLength(0);
  });
});

describe('helpers', () => {
  test('sumByPrefix adds the per-BU keys the engine emits', () => {
    expect(sumByPrefix({
      supply_chain_contagion_pharma: 100,
      supply_chain_contagion_software: 50,
      unrelated_key: 999,
    }, 'supply_chain_contagion_')).toBe(150);
  });

  test('sumByPrefix ignores non-numeric and missing sources', () => {
    expect(sumByPrefix(null, 'x_')).toBe(0);
    expect(sumByPrefix({ x_a: 'nope', x_b: 5 }, 'x_')).toBe(5);
  });

  test('readRoundKey finds the round-suffixed form the engine writes', () => {
    const bag = { midgame_carbon_cost_r3: 54830 };
    expect(readRoundKey(bag, 'midgame_carbon_cost', 3)).toBe(54830);
    // and still finds it when the caller's round is off by one at a boundary
    expect(readRoundKey(bag, 'midgame_carbon_cost', 4)).toBe(54830);
    expect(readRoundKey({}, 'midgame_carbon_cost', 3)).toBe(0);
  });

  test('events are merged with flags, not short-circuited', () => {
    // The original read `active_event_flags || events`, which always collapsed
    // to flags because that object is virtually always truthy.
    const out = buildWaterfall({
      businessUnits: [{ bu_id: 'x', revenue_base: 1000, opex_base: 400 }],
      globalState: { round_number: 1, historical_ebitda: 600, active_event_flags: { nothing: 1 } },
      events: { supply_chain_contagion_pharma: 250 },
    });
    expect(out.steps.map(s => s.label)).toContain('Supply-chain shock');
  });
});
