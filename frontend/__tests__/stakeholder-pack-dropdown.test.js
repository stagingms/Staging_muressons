/**
 * Stakeholder Pack selector in cohort setup.
 *
 * A pack gives each of the four SBUs its own stakeholder matrix. The backend
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

describe('stakeholder pack selector', () => {
  test('state is bound to the control', () => {
    expect(MODAL).toMatch(/const \[stakeholderPackId, setStakeholderPackId\] = useState\(''\)/);
    expect(MODAL).toMatch(/onChange=\{e => setStakeholderPackId\(e\.target\.value\)\}/);
  });

  test('packs are fetched from the API', () => {
    expect(MODAL).toMatch(/\/api\/admin\/stakeholder-packs/);
    expect(MODAL).toMatch(/setStakeholderPacks\(d\.packs \|\| \[\]\)/);
  });

  test('a missing packs endpoint degrades to Default rather than breaking the form', () => {
    const i = MODAL.indexOf('/api/admin/stakeholder-packs');
    expect(MODAL.slice(i, i + 400)).toMatch(/\.catch\(\(\) => \{\}\)/);
  });

  test('the value is SENT — on create and on edit', () => {
    // The whole point. Two payload sites exist in this modal; both must carry
    // it, or editing a cohort silently drops the pack.
    const sites = MODAL.match(/stakeholder_pack_id: stakeholderPackId \|\| ''/g) || [];
    expect(sites.length).toBe(2);
  });

  test('it is hydrated when an existing cohort is opened', () => {
    expect(MODAL).toMatch(/setStakeholderPackId\(editSession\.stakeholder_pack_id \|\| ''\)/);
  });

  test('Default is an explicit, safe option', () => {
    // Empty string means "resolve exactly as before", so the default choice
    // must be selectable and named — not an absent/unconfigured state.
    expect(MODAL).toMatch(/<option value="">— Default \(one map for the cohort\) —<\/option>/);
  });

  test('an incomplete pack is flagged in the list AND under the control', () => {
    expect(MODAL).toMatch(/\(incomplete\)/);
    expect(MODAL).toMatch(/will fall back to the default map/);
  });

  test('a complete pack is confirmed', () => {
    expect(MODAL).toMatch(/have their own\s*\n?\s*stakeholder matrix/);
  });

  test('a deleted pack still referenced by the cohort is surfaced', () => {
    // The server falls back safely, so nothing errors — which is exactly why
    // the UI has to say something, or the map just looks generic.
    expect(MODAL).toMatch(/no longer exists/);
  });

  test('the control is labelled for screen readers', () => {
    expect(MODAL).toMatch(/aria-label="Stakeholder pack — per-SBU stakeholder matrices"/);
  });

  test('it sits with the region control, which it refines', () => {
    // Anchor on the region SELECT, not the words "Geographic Region" — those
    // also appear in a validation message ~270 lines earlier, which made an
    // earlier version of this test measure the wrong distance.
    const region = MODAL.indexOf('onChange={e => setRegionId(e.target.value)}');
    const pack = MODAL.indexOf('<label>Stakeholder Pack</label>');
    expect(region).toBeGreaterThan(-1);
    expect(pack).toBeGreaterThan(region);
    expect(pack - region).toBeLessThan(1500);
  });
});
