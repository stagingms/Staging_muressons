/**
 * FIN-06 (audit 2026-09-04, Wave 3) — the consequence waterfall is now a closed
 * bridge from opening treasury to the treasury the round persisted, and the
 * cockpit's cash section renders IT (the engine's own labels and `because`)
 * instead of a hand-picked list of event keys. Older rounds without `bridge`
 * keep the fallback list.
 */
const fs = require('fs');
const path = require('path');

function loadModel() {
  const src = fs
    .readFileSync(path.join(__dirname, '..', 'app', 'components', 'ebitdaWaterfallModel.js'), 'utf8')
    .replace(/^export default .*$/m, '')
    .replace(/export /g, '');
  const m = {};
  // eslint-disable-next-line no-new-func
  new Function('module', `${src}\nmodule.buildWaterfall = buildWaterfall;\nmodule.bridgeSteps = bridgeSteps;`)(m);
  return m;
}
const { buildWaterfall, bridgeSteps } = loadModel();

const bus = [{ revenue_base: 30e6, opex_base: 20e6 }, { revenue_base: 10e6, opex_base: 8e6 }];
const bridgedWaterfall = {
  initial_treasury: 50e6, final_treasury: 47.5e6, net_change: -2.5e6, engine_final_treasury: 54e6,
  entries: [
    { label: 'Gross Profit (CSF)', amount: 12e6, running_total: 62e6, because: 'EBITDA banked' },
    { label: 'CapEx (cash-funded)', amount: -4e6, running_total: 58e6 },
    { label: 'Regulatory ratchet fine', amount: -4e6, running_total: 54e6, because: 'governance risk above the baseline' },
    { label: 'Round option — treasury effect', amount: -3e6, running_total: 51e6, stage: 'post_tick' },
    { label: 'NPC stakeholders (enforcement fines, cascades)', amount: -3.5e6, running_total: 47.5e6, stage: 'engines' },
  ],
  entry_count: 5, unattributed: 0.0,
  bridge: { after_tick: 54e6, after_pillar: 54e6, after_post_tick: 51e6, after_engines: 47.5e6, stored: 47.5e6, closes: true },
};

describe('the cash section is the engine bridge when the round carries one', () => {
  test('opening → every named movement → closing, in the engine order', () => {
    const out = buildWaterfall({ businessUnits: bus, globalState: { historical_ebitda: 12e6 }, events: { consequence_waterfall: bridgedWaterfall } });
    const cash = out.steps.filter(s => s.section === 'cash');
    expect(cash.map(s => s.label)).toEqual([
      'Opening treasury', 'Gross Profit (CSF)', 'CapEx (cash-funded)', 'Regulatory ratchet fine',
      'Round option — treasury effect', 'NPC stakeholders (enforcement fines, cascades)', 'Closing treasury',
    ]);
    expect(cash[0].value).toBe(50e6);
    expect(cash[cash.length - 1].value).toBe(47.5e6);
    expect(out.treasury).toEqual({ opening: 50e6, closing: 47.5e6, closes: true, unattributed: 0 });
    // the engine's explanation travels with the row
    expect(cash[1].because).toBe('EBITDA banked');
    expect(cash[4].stage).toBe('post_tick');
    // the EBITDA section is untouched
    expect(out.steps.slice(0, 3).map(s => s.label)).toEqual(['Revenue', 'OPEX', 'EBITDA']);
    expect(out.reconciles).toBe(true);
  });

  test('a bridge that does not close says so', () => {
    const open = { ...bridgedWaterfall, final_treasury: 40e6, bridge: { ...bridgedWaterfall.bridge, closes: false } };
    const out = buildWaterfall({ businessUnits: bus, globalState: {}, events: { consequence_waterfall: open } });
    expect(out.treasury.closes).toBe(false);
  });

  test('a waterfall without a bridge (a round committed before FIN-06) falls back to the key list', () => {
    const legacy = { initial_treasury: 50e6, final_treasury: 60e6, entries: [{ label: 'Gross Profit (CSF)', amount: 10e6 }] };
    expect(bridgeSteps(legacy)).toBeNull();
    const out = buildWaterfall({ businessUnits: bus, globalState: {}, events: { consequence_waterfall: legacy, actual_damage: 2e6 } });
    expect(out.treasury).toBeNull();
    expect(out.steps.map(s => s.label)).toContain('Crisis damage');
  });

  test('flags carry the persisted copy — the dashboard renders the bridge after a reload', () => {
    const out = buildWaterfall({ businessUnits: bus, globalState: { active_event_flags: { consequence_waterfall: bridgedWaterfall } }, events: {} });
    expect(out.treasury.closing).toBe(47.5e6);
  });
});

describe('the component renders the bridge and warns when it is open', () => {
  test('source wiring', () => {
    const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'EBITDAWaterfall.js'), 'utf8');
    expect(src).toMatch(/const \{ steps, reconciles, treasury \} = useMemo/);
    expect(src).toMatch(/how treasury moved this round, opening to closing/);
    expect(src).toMatch(/data-testid="treasury-bridge-open"/);
    expect(src).toMatch(/title=\{bar\.because \|\| undefined\}/);
  });
});
