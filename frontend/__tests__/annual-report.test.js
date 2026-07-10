/**
 * W-C determinism spot-check — buildReportModel.
 * The report is a pure function of the commit snapshot + history:
 * same inputs ⇒ same report, materiality section reads the team's own
 * scored assessment, and everything is null-safe pre-R2.
 */
import { buildReportModel } from '../app/components/AnnualReport';

const bu = (rev, opex, ci = 40, ncd = 10) => ({ revenue_base: rev, opex_base: opex, carbon_intensity: ci, natural_capital_debt: ncd });

const snapshot = {
  roundNumber: 4,
  commitResults: {
    globalState: {
      historical_ebitda: 22_000_000,
      corporate_treasury: 55_000_000,
      group_reputation: 62,
      cost_of_capital: 0.07,
      synergy_multiplier: 1.05,
      tco2e_emissions: 480,
      competitor_ebitda: 21_000_000,
      materiality_full_accuracy: 83.3,
      materiality_status: 'aligned',
      materiality_bu_id: 'retail_fmcg',
      materiality_issue_scores: {
        low: { title: 'Low product', materiality_product: 6, credit: 1 },
        high: { title: 'High product', materiality_product: 20, credit: 0 },
        mid: { title: 'Mid product', materiality_product: 12, credit: 0.5 },
      },
    },
    businessUnits: [bu(60_000_000, 40_000_000), bu(50_000_000, 48_000_000)],
  },
  history: [
    { round_number: 1, global_state: { tco2e_emissions: 600, group_reputation: 50, historical_ebitda: 19_000_000, corporate_treasury: 50_000_000 }, business_units: [bu(58_000_000, 39_000_000)] },
    { round_number: 2, global_state: { tco2e_emissions: 560, group_reputation: 54, historical_ebitda: 20_000_000, corporate_treasury: 52_000_000, cost_of_capital: 0.06 }, business_units: [bu(59_000_000, 39_000_000)] },
    { round_number: 3, global_state: { tco2e_emissions: 510, group_reputation: 58, historical_ebitda: 21_000_000, corporate_treasury: 53_000_000 }, business_units: [bu(60_000_000, 39_000_000)] },
  ],
  businessUnits: [],
};

describe('buildReportModel (W3)', () => {
  test('deterministic: same snapshot ⇒ deep-equal model', () => {
    expect(buildReportModel(snapshot)).toEqual(buildReportModel(snapshot));
    expect(buildReportModel(snapshot)).toEqual(buildReportModel(JSON.parse(JSON.stringify(snapshot))));
  });

  test('year boundary math and emissions series include the closing snapshot', () => {
    const m = buildReportModel(snapshot);
    expect(m.year).toBe(2);
    expect(m.emissions.map(e => e.round)).toEqual([1, 2, 3, 4]);
    expect(m.emissions[3].tco2e).toBe(480);
  });

  test('year-ago comparison uses the round-2 snapshot', () => {
    const m = buildReportModel(snapshot);
    expect(m.yaGs.historical_ebitda).toBe(20_000_000);
  });

  test('rating letter is issued for the closing even round', () => {
    const m = buildReportModel(snapshot);
    expect(m.rating).not.toBeNull();
    expect(m.rating.round).toBe(4);
  });

  test('materiality issues sorted by materiality product, top first', () => {
    const m = buildReportModel(snapshot);
    expect(m.materiality.issues.map(i => i.id)).toEqual(['high', 'mid', 'low']);
    expect(m.materiality.accuracy).toBe(83.3);
    expect(m.materiality.buId).toBe('retail_fmcg');
  });

  test('null-safe before the materiality gate', () => {
    const bare = { roundNumber: 2, commitResults: { globalState: { tco2e_emissions: 500 }, businessUnits: [bu(50_000_000, 40_000_000)] }, history: [], businessUnits: [] };
    const m = buildReportModel(bare);
    expect(m.materiality).toBeNull();
    expect(m.emissions).toHaveLength(1);
    expect(m.sharePrice).toBeGreaterThan(0);
  });
});
