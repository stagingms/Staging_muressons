/**
 * Player-dashboard toggle search.
 *
 * DISCOVERABILITY-2026-07-30. Reported as "option for Quick reflection is not
 * appearing in the toggles". It WAS appearing — 41 rows down, in group 8 of 11.
 * The catalogue held all 65 cards, playerVisibilityGroups() returned all 11
 * groups, and the render loop had no filter, no slice and no height cap. The
 * panel was simply too long to scan, and five of the largest groups (12, 12,
 * 10, 5, 5 cards) sit below the fold.
 *
 * That the author of the catalogue could not find an entry in it is the actual
 * signal. A facilitator configuring a cohort ten minutes before class has less
 * patience than that.
 *
 * The search filters on label OR key OR group, because the audiences differ: a
 * facilitator knows "Quick Reflection", a developer reading a tooltip or a bug
 * report knows `quick_reflection_box`, and someone who half-remembers the
 * section types "prediction".
 *
 * These tests exercise the same predicate the component uses, against the real
 * registry — so a card added without a searchable label, or a regression in
 * the filter, fails here rather than in front of a class.
 */
const fs = require('fs');
const path = require('path');

const MODAL = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'), 'utf8');

async function loadRegistry() {
  const src = fs
    .readFileSync(path.join(__dirname, '..', 'app', 'config', 'playerVisibilityRegistry.js'), 'utf8')
    .replace(/export /g, '');
  const mod = {};
  // eslint-disable-next-line no-new-func
  new Function('module', `${src}\nmodule.PLAYER_VISIBILITY_CARDS = PLAYER_VISIBILITY_CARDS;\nmodule.playerVisibilityGroups = playerVisibilityGroups;`)(mod);
  return mod;
}

let CARDS;
let groupsOf;

beforeAll(async () => {
  const m = await loadRegistry();
  CARDS = m.PLAYER_VISIBILITY_CARDS;
  // Mirrors the component's filter exactly.
  groupsOf = (q0) => {
    const q = (q0 || '').trim().toLowerCase();
    if (!q) return m.playerVisibilityGroups();
    return m.playerVisibilityGroups()
      .map(({ group, cards }) => ({
        group,
        cards: group.toLowerCase().includes(q)
          ? cards
          : cards.filter(c => c.label.toLowerCase().includes(q) || c.key.toLowerCase().includes(q)),
      }))
      .filter(g => g.cards.length > 0);
  };
});

const flat = (gs) => gs.flatMap(g => g.cards);

describe('toggle search', () => {
  test('the case that prompted it: "reflection" finds Quick Reflection box', () => {
    const labels = flat(groupsOf('reflection')).map(c => c.label);
    expect(labels).toContain('Quick Reflection box');
  });

  test('searching the exact key pinpoints one card', () => {
    const hits = flat(groupsOf('quick_reflection_box'));
    expect(hits).toHaveLength(1);
    expect(hits[0].key).toBe('quick_reflection_box');
  });

  test('searching by label works for a card in a different group', () => {
    const hits = flat(groupsOf('scorecard'));
    expect(hits.map(c => c.key)).toContain('balanced_scorecard');
  });

  test('a group name surfaces its whole section', () => {
    const gs = groupsOf('prediction');
    expect(gs).toHaveLength(1);
    expect(gs[0].group).toBe('Prediction & reflection');
    expect(gs[0].cards.length).toBe(4);
  });

  test('search is case-insensitive', () => {
    expect(flat(groupsOf('QUICK REFLECTION')).length)
      .toBe(flat(groupsOf('quick reflection')).length);
  });

  test('an empty query shows everything — the filter cannot hide the catalogue', () => {
    const gs = groupsOf('');
    expect(flat(gs)).toHaveLength(CARDS.length);
    expect(gs.length).toBe(11);
  });

  test('a non-matching query yields nothing (and the UI must say so)', () => {
    expect(flat(groupsOf('zzzznotathing'))).toHaveLength(0);
    // A silently empty panel would read as the very bug this prevents.
    expect(MODAL).toMatch(/No panel matches/);
  });

  test('every card is reachable by its own label', () => {
    // A card whose label cannot find it is invisible in a 65-row list.
    const unreachable = CARDS.filter(c => {
      const hits = flat(groupsOf(c.label));
      return !hits.some(h => h.key === c.key);
    });
    expect(unreachable.map(c => c.key)).toEqual([]);
  });

  test('every card is reachable by its own key', () => {
    const unreachable = CARDS.filter(c => {
      const hits = flat(groupsOf(c.key));
      return !hits.some(h => h.key === c.key);
    });
    expect(unreachable.map(c => c.key)).toEqual([]);
  });
});

describe('the search is actually wired into the modal', () => {
  test('there is a search input bound to state', () => {
    expect(MODAL).toMatch(/const \[visSearch, setVisSearch\] = useState\(''\)/);
    expect(MODAL).toMatch(/onChange=\{\(e\) => setVisSearch\(e\.target\.value\)\}/);
  });

  test('it filters on label, key AND group', () => {
    // Anchor on the group-filter itself: `const q = ...` appears three times
    // (match count, empty state, and this), and picking the wrong one made an
    // earlier version of this test fail against correct code.
    const i = MODAL.indexOf('cards: group.toLowerCase().includes(q)');
    expect(i).toBeGreaterThan(-1);
    const block = MODAL.slice(i, i + 500);
    expect(block).toMatch(/c\.label\.toLowerCase\(\)\.includes\(q\)/);
    expect(block).toMatch(/c\.key\.toLowerCase\(\)\.includes\(q\)/);
    // …and empty groups are dropped so no bare headers are left behind.
    expect(block).toMatch(/\.filter\(g => g\.cards\.length > 0\)/);
  });

  test('it is clearable and labelled for screen readers', () => {
    expect(MODAL).toMatch(/aria-label="Filter player dashboard panels by name or key"/);
    expect(MODAL).toMatch(/aria-label="Clear filter"/);
  });
});
