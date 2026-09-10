/**
 * Found by the scripted classroom rehearsal (2026-09-10), finale screen: the
 * terminal-valuation waterfall's M_SDG row read "not used this run" and the
 * formula caption printed "M_SDG(1.25×)" while the engine had used 1.0635×
 * — GameOverSummary recomputed the multiplier from sdg_impact_score with the
 * 2026.09 arithmetic (neutral 0) instead of reading the one the engine
 * reports. The seat's stored finale: EBITDA 31,413,540.08 × 18.0 × 1.77 ×
 * 1.0635 = 1,064,388,434.02, the V_T the screen printed under a caption
 * whose factors multiply to 1.25 billion.
 */
const fs = require('fs');
const path = require('path');
const { sdgMultiplierRow } = require('../app/lib/sdgMultiplierRow');

const REHEARSAL_SEAT = {           // seat A, R10, mur_drill (2026.10 rules)
  terminal_ebitda: 31413540.08, exit_multiple: 18.0, regenerative_multiple: 1.77,
  sdg_multiplier: 1.0635, sdg_impact_score: 98.9, sdg_neutral: 73.5, sdg_coeff: 0.25,
  terminal_value: 1064388434.02,
};

test('the row prints the multiplier the engine used, and its derivation with the neutral', () => {
  const row = sdgMultiplierRow(REHEARSAL_SEAT, {});
  expect(row.mSdg).toBe(1.0635);
  expect(row.used).toBe(true);
  expect(row.desc).toBe('SDG index 98.9 vs neutral 73.5 → M_SDG = 1.0 + ((98.9 − 73.5)/100) × 0.25');
  const { terminal_ebitda: e, exit_multiple: x, regenerative_multiple: mr } = REHEARSAL_SEAT;
  expect(e * x * mr * row.mSdg).toBeCloseTo(REHEARSAL_SEAT.terminal_value, 0);
  // the old arithmetic is what the screen printed — and it is not the product
  expect(1.0 + (98.9 / 100) * 0.25).toBeCloseTo(1.24725, 5);
  expect(e * x * mr * 1.24725).toBeGreaterThan(1.24e9);
});

test('the flags column is read when the report lacks the keys (resume after R10)', () => {
  const row = sdgMultiplierRow({ terminal_value: 1 }, REHEARSAL_SEAT);
  expect(row.mSdg).toBe(1.0635);
  expect(row.neutral).toBe(73.5);
});

test('2026.09 without the side track still reads "not used this run"', () => {
  const row = sdgMultiplierRow({ sdg_multiplier: 1.0, sdg_impact_score: 0, sdg_neutral: 0, sdg_coeff: 0.25 }, {});
  expect(row.used).toBe(false);
  expect(row.mSdg).toBe(1);
  expect(row.desc).toBe('SDG Impact Score: 0/105 → M_SDG = 1.0 + (0/100) × 0.25');
});

test('2026.09 with the side track played prints the engine multiplier under the old caption', () => {
  const row = sdgMultiplierRow({ sdg_multiplier: 1.2, sdg_impact_score: 80, sdg_neutral: 0, sdg_coeff: 0.25, sdg_track_completed: true }, {});
  expect(row.used).toBe(true);
  expect(row.mSdg).toBe(1.2);
  expect(row.desc).toBe('SDG Impact Score: 80/105 → M_SDG = 1.0 + (80/100) × 0.25');
});

test('a 2026.10 seat at the neutral index is shown as 1.00×, not as unused — the factor is in the product', () => {
  const row = sdgMultiplierRow({ sdg_multiplier: 1.0, sdg_impact_score: 73.5, sdg_neutral: 73.5, sdg_coeff: 0.25 }, {});
  expect(row.used).toBe(true);
  expect(row.mSdg).toBe(1);
});

test('a payload written before the engine reported its multiplier falls back to the old arithmetic', () => {
  const row = sdgMultiplierRow({ sdg_impact_score: 80, sdg_track_completed: true }, {});
  expect(row.mSdg).toBeCloseTo(1.2, 10);
  expect(row.used).toBe(true);
  expect(sdgMultiplierRow({}, {}).used).toBe(false);
});

test('GameOverSummary reads the row from the helper and no longer recomputes M_SDG', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'GameOverSummary.js'), 'utf8');
  expect(src).toMatch(/sdgMultiplierRow\(d, flags\)/);
  expect(src).not.toMatch(/1\.0 \+ \(safeScore \/ 100\.0\) \* 0\.25/);
  expect(src).toMatch(/value: sdgRow\.used \? ratio\(mSdg\) : 'not used this run'/);
  expect(src).toMatch(/M_SDG\(\{ratio\(mSdg\)\}\)/);   // the caption prints the same number as the row
});
