/**
 * RNG-2 (audit 2026-09-04, Wave 3) — the Create-Cohort wizard sends rng_seed only
 * when a seed was typed. It used to send `rng_seed: ''` on every create AND every
 * edit save (it never pre-fills the box in edit mode), which — once the server
 * honours a blank as "un-seed" — would strip a running cohort's seed on any save.
 */
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'), 'utf8');

test('a blank seed box is omitted from the cohort-settings PATCH', () => {
  expect(src).toMatch(/\.\.\.\(rngSeed\.trim\(\) \? \{ rng_seed: rngSeed\.trim\(\) \} : \{\}\)/);
  expect(src).not.toMatch(/^\s*rng_seed: rngSeed\.trim\(\),/m);
});
