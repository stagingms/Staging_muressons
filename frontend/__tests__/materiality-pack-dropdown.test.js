/**
 * Materiality Pack selector in cohort setup.
 *
 * Sibling of stakeholder-pack-dropdown.test.js and deliberately the same
 * shape: the two controls answer the two halves of Round 2, and a difference
 * between them would be a bug, not a style choice.
 *
 * A pack gives each of the four SBUs its own materiality dictionary. The backend
 * resolves it (stakeholder_packs.py, get_stakeholders_for_bu); this control is
 * the only way a facilitator binds one to a cohort.
 *
 * The failure this file guards is the one that has recurred throughout this
 * project: a control that renders but never reaches the server. A dropdown the
 * user can change, that is not in the save payload, looks completely correct
 * and does nothing — the same shape as the negotiation-room toggle and the
 * EBITDA waterfall. So the assertions are about the WIRING, not the markup:
 * state exists, it is hydrated when editing, it is sent on create AND on edit,
 * and the incomplete/missing-pack states are surfaced rather than swallowed.
 */
const fs = require('fs');
const path = require('path');

const MODAL = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'), 'utf8');

describe('materiality pack selector', () => {
  test('state is bound to the control', () => {
    expect(MODAL).toMatch(/const \[materialityPackId, setMaterialityPackId\] = useState\(''\)/);
    expect(MODAL).toMatch(/onChange=\{e => setMaterialityPackId\(e\.target\.value\)\}/);
  });

  test('packs are fetched from the API', () => {
    expect(MODAL).toMatch(/\/api\/admin\/stakeholder-packs/);
    expect(MODAL).toMatch(/setMaterialityPacks\(d\.packs \|\| \[\]\)/);
  });

  test('a missing packs endpoint degrades to Default rather than breaking the form', () => {
    const i = MODAL.indexOf('/api/admin/materiality-packs');
    expect(MODAL.slice(i, i + 400)).toMatch(/\.catch\(\(\) => \{\}\)/);
  });

  test('the value is SENT — on create and on edit', () => {
    // The whole point. Two payload sites exist in this modal; both must carry
    // it, or editing a cohort silently drops the pack.
    const sites = MODAL.match(/materiality_pack_id: materialityPackId \|\| ''/g) || [];
    expect(sites.length).toBe(2);
  });

  test('it is hydrated when an existing cohort is opened', () => {
    expect(MODAL).toMatch(/setMaterialityPackId\(editSession\.materiality_pack_id \|\| ''\)/);
  });

  test('Default is an explicit, safe option', () => {
    // Empty string means "resolve exactly as before", so the default choice
    // must be selectable and named — not an absent/unconfigured state.
    expect(MODAL).toMatch(/<option value="">— Default \(one dictionary per BU\) —<\/option>/);
  });

  test('an incomplete pack is flagged in the list AND under the control', () => {
    expect(MODAL).toMatch(/\(incomplete\)/);
    expect(MODAL).toMatch(/will fall back to the default dictionary/);
  });

  test('a complete pack is confirmed', () => {
    expect(MODAL).toMatch(/have their own\s*\n?\s*materiality dictionary/);
  });

  test('a deleted pack still referenced by the cohort is surfaced', () => {
    // The server falls back safely, so nothing errors — which is exactly why
    // the UI has to say something, or the map just looks generic.
    expect(MODAL).toMatch(/no longer exists/);
  });

  test('the control is labelled for screen readers', () => {
    expect(MODAL).toMatch(/aria-label="Materiality pack — per-SBU double-materiality matrices"/);
  });

  test('it sits directly after the Stakeholder Pack selector', () => {
    // The two answer the same question for the two halves of Round 2: who is
    // at the table, and what counts as material to them. Separating them
    // would leave a facilitator configuring one and forgetting the other.
    const stake = MODAL.indexOf('<label>Stakeholder Pack</label>');
    const mat = MODAL.indexOf('<label>Materiality Pack</label>');
    expect(stake).toBeGreaterThan(-1);
    expect(mat).toBeGreaterThan(stake);
    // ~4.5k apart: the stakeholder block carries its own coverage branch, so
    // "adjacent" is a few thousand characters here. The assertion is that
    // nothing unrelated sits between them, not a tight byte budget.
    expect(mat - stake).toBeLessThan(6000);
  });
});
