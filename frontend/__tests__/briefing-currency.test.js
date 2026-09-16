/**
 * Briefing prose prints money in the cohort currency (2026-09-16).
 *
 * Found in the classroom walk-through on a ₹ cohort: the round briefings showed
 * hardcoded DOLLAR amounts in their prose — the R2 CFO-gate callout ("reduces
 * your R3 Green Bond cost by $500K … a $1M Green Bond risk premium") and, more
 * broadly, $-figures across the narrative ($12M cyclone, $30M desalination,
 * $15M fine) and a metric chip or two ("Damage Exposure ($18M)"). The engine's
 * own figures were in ₹ and correct; only the authored briefing copy leaked $.
 *
 * The cause was the RENDER PATH, not the data. The codebase already has
 * localiseAuthored() — the one symbol-and-rate boundary for money inside
 * authored prose — and RoundBriefing already applied it to the theory card and
 * the climate supplement, but NOT to the four main prose surfaces. This pins
 * that every authored money surface in the briefing goes through it.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

describe('RoundBriefing routes every authored money surface through localiseAuthored', () => {
  const src = read('components/RoundBriefing.js');

  test('narrative paragraphs', () => {
    expect(src).toMatch(/sanitizeHtml\(localiseAuthored\(showTheory \? para : stripPedagogy\(para\)\)\)/);
  });
  test('the CFO / regulatory warning box', () => {
    expect(src).toMatch(/sanitizeHtml\(localiseAuthored\(b\.warning\.text\)\)/);
  });
  test('strategic objectives', () => {
    expect(src).toMatch(/localiseAuthored\(obj\)/);
  });
  test('key-metric chip labels', () => {
    expect(src).toMatch(/localiseAuthored\(m\.label\)/);
  });
});

describe('the authored briefing copy still carries the dollars the render point converts', () => {
  // The defect is real only while the data authors amounts in $ — if a future
  // edit rewrites the copy this test says so, rather than silently passing.
  const data = read('briefings/data/standard.js');
  test('the R2 CSRD warning still authors $500K / $1M', () => {
    expect(data).toMatch(/Green Bond cost by \$500K/);
    expect(data).toMatch(/\$1M Green Bond risk premium/);
  });
});

describe('localiseAuthored converts that copy to the cohort currency', () => {
  // ESM module with module-level currency state — load fresh, restore after.
  const load = () => { jest.resetModules(); return require('../app/utils/format'); };
  const CSRD = 'reduces your R3 Green Bond cost by $500K. Option C triggers a $1M Green Bond risk premium.';

  test('a ₹ cohort at rate 1 (the classroom case): rupees, no dollars, numbers unchanged', () => {
    const f = load();
    f.setCurrencySymbol('₹'); f.setCurrencyRate(1);
    const out = f.localiseAuthored(CSRD);
    expect(out).not.toContain('$');
    expect(out).toContain('₹500K');
    expect(out).toContain('₹1M');
    f.setCurrencySymbol('$'); f.setCurrencyRate(1);
  });

  test('a cohort with a real conversion rate rescales the amount, still no dollars', () => {
    const f = load();
    f.setCurrencySymbol('₹'); f.setCurrencyRate(83);
    const out = f.localiseAuthored('base cyclone damage of $12M this round');
    expect(out).not.toContain('$');
    expect(out).toContain('₹');
    expect(out).not.toContain('$12M');   // it was converted, not passed through
    f.setCurrencySymbol('$'); f.setCurrencyRate(1);
  });

  test('a $ cohort at rate 1 is left byte-for-byte unchanged (ships inert)', () => {
    const f = load();
    f.setCurrencySymbol('$'); f.setCurrencyRate(1);
    expect(f.localiseAuthored(CSRD)).toBe(CSRD);
  });
});
