/**
 * SEAM-14 (audit 2026-09-04, Wave 3) — the facilitator's projected surfaces and
 * the ticker print money through the one symbol-and-rate source every player
 * surface uses, and load the cohort's currency for the cohort they show. They
 * used to hard-code "$" at rate 1, so a ₹-at-83 cohort saw one number on the
 * cockpit and another on the projector.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

const SURFACES = [
  'components/DebriefNarrative.js',
  'components/DebriefReport.js',
  'admin/trading-floor/page.js',
  'admin/projector/page.js',
  'components/MarketTicker.js',
];

describe('no projected surface builds money by hand', () => {
  test.each(SURFACES)('%s has no `$${` interpolation and imports the formatter', (rel) => {
    const src = read(rel).replace(/^\s*(\/\/|\*|\/\*).*$/gm, '');
    expect(src).not.toMatch(/\$\$\{/);
    expect(src).toMatch(/from '(\.\.\/)+utils\/format'/);
  });

  test('the cohort-scoped surfaces load the cohort currency they display', () => {
    expect(read('components/DebriefNarrative.js')).toMatch(/loadSessionCurrency\(sessionId\)/);
    expect(read('components/DebriefReport.js')).toMatch(/loadSessionCurrency\(sessionId\)/);
    expect(read('admin/projector/page.js')).toMatch(/loadSessionCurrency\(cohortId\)/);
    expect(read('admin/trading-floor/page.js')).toMatch(/loadSessionCurrency\(cohortId\)/);
  });

  test('the ticker labels the carbon price in the cohort symbol', () => {
    expect(read('components/MarketTicker.js')).toMatch(/symbol: `Carbon \$\{currencySymbol\(\)\}\/t`/);
  });
});

describe('the formatter applies the rate the surfaces now route through', () => {
  // The module is ESM with module-level state; load it fresh in isolation.
  const load = () => {
    jest.resetModules();
    return require('../app/utils/format');
  };
  test('moneyM and price carry symbol and rate', () => {
    const f = load();
    f.setCurrencySymbol('₹'); f.setCurrencyRate(83);
    expect(f.moneyM(1_000_000)).toBe('₹83.0M');
    expect(f.moneyM(-2_500_000, { dp: 2 })).toMatch(/^[−-]₹207\.50M$/);
    expect(f.moneyMScaled(12.3, { dp: 0 })).toBe('₹1021M');
    expect(f.price(2.5)).toBe('₹2.50');
    f.setCurrencySymbol('$'); f.setCurrencyRate(1);
  });
});
