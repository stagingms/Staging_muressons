/**
 * Every paradigm the UI offers must be one cohort creation ACCEPTS.
 *
 * Reported shape (C5 in the failure-mode register): the cohort form offered
 * un_sdg and brsr_ngrbc, the server's config.VALID_DECISION_PARADIGMS
 * contained neither, and a facilitator who picked one filled in the entire
 * form before hitting a 422 wall at submit. The options had been added to the
 * UI in anticipation of server support that never landed.
 *
 * Same tripwire pattern as shockwave-catalog: parse the backend source and
 * pin the frontend to it, so the next aspirational option fails CI instead of
 * a facilitator.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const configSrc = fs.readFileSync(path.join(ROOT, 'backend', 'config.py'), 'utf8');
const modalSrc = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'), 'utf8');
const facMgrSrc = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'FacilitatorManager.js'), 'utf8');

function serverParadigms() {
  const m = configSrc.match(/VALID_DECISION_PARADIGMS[^=]*=\s*frozenset\(\{([\s\S]*?)\}\)/);
  expect(m).toBeTruthy();
  return new Set([...m[1].matchAll(/"([a-z0-9_]+)"/g)].map((x) => x[1]));
}

/** ids offered by an option-list source, scoped to its PARADIGM block. */
function offeredIds(src, blockStart, blockEnd) {
  const start = src.indexOf(blockStart);
  expect(start).toBeGreaterThan(-1);
  const end = src.indexOf(blockEnd, start);
  const block = src.slice(start, end > -1 ? end : start + 4000);
  return [...block.matchAll(/id:\s*'([a-z0-9_]+)'/g)].map((m) => m[1]);
}

test('cohort form offers only paradigms the server accepts', () => {
  const server = serverParadigms();
  const offered = offeredIds(modalSrc, 'PARADIGM_OPTIONS', 'const toggleVis');
  expect(offered.length).toBeGreaterThan(0);
  for (const id of offered) {
    expect(server.has(id)).toBe(true);
  }
});

test('facilitator manager default-paradigm list matches the server too', () => {
  const server = serverParadigms();
  const offered = offeredIds(facMgrSrc, 'const PARADIGM_OPTIONS', 'const EMPTY_FORM');
  expect(offered.length).toBeGreaterThan(0);
  for (const id of offered) {
    expect(server.has(id)).toBe(true);
  }
});

test('the rejected paradigms are actually gone from the cohort form', () => {
  const offered = offeredIds(modalSrc, 'PARADIGM_OPTIONS', 'const toggleVis');
  expect(offered).not.toContain('un_sdg');
  expect(offered).not.toContain('brsr_ngrbc');
});
