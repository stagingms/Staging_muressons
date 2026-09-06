/**
 * SEAM-17 / SEAM-16 (audit 2026-09-04, Wave 3).
 * The KPI-belt deltas were computed against history's LAST row — this round's own
 * snapshot — so they were zero at rest and flashed only during the advance→refetch
 * window. They read the prior round's row now, like the FocusOverlay strip.
 * And the belt names which of the two WACCs prices the exit multiple.
 */
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'ExecutiveCockpit.js'), 'utf8');

test('the belt\'s "previous" state is the prior round, not this round\'s snapshot', () => {
  expect(src).not.toMatch(/const previousGlobalState = history\?\.length > 0 \? history\[history\.length - 1\]/);
  expect(src).toMatch(/const previousGlobalState = priorRoundState \|\| \{\}/);
  expect(src).toMatch(/const priorRoundBUs = history\?\.length > 1/);
  expect(src).not.toMatch(/history\?\.\[history\?\.length-1\]\?\.business_units/);
  // the four chips carry the "vs R{N-1}" reading
  expect((src.match(/data-testid="kpi-delta"/g) || []).length).toBe(4);
  expect(src).toMatch(/vs R\$\{Math\.max\(1, roundNumber - 1\)\}/);
  // the BU ticker's revenue delta is against the prior round's row too
  expect(src).toMatch(/const prevBu = priorRoundBUs\?\.find\(/);
});

test('the belt says which WACC prices the exit multiple', () => {
  expect(src).toMatch(/Cost of Capital \(corporate\)/);
  expect(src).toMatch(/data-testid="esg-wacc-row"/);
  expect(src).toMatch(/WACC \(ESG-adj\., prices the exit multiple\)/);
  expect(src).toMatch(/esgWacc\?\.adjusted_wacc/);
});
