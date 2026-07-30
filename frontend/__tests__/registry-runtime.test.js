/**
 * Execute the registry, don't just parse it.
 *
 * Every other test in this area reads the source with a regex — necessary,
 * because the profiles are asserted against Python that jest cannot import. But
 * a regex will happily confirm a card that a browser then chokes on: a duplicate
 * key, a missing comma between fields, an audience tag that is a typo of a real
 * one. Babel parsing catches syntax; only running the module catches meaning.
 *
 * This matters more than usual here because the audience field was inserted into
 * 65 existing card literals by a script, and the 19 legacy cards had a different
 * field order from the 46 newer ones.
 */
import {
  PLAYER_VISIBILITY_CARDS,
  PLAYER_VISIBILITY_KEYS,
  PLAYER_VISIBILITY_DEFAULTS,
  AUDIENCE_TAGS,
  visibilityForAudiences,
  playerVisibilityGroups,
} from '../app/config/playerVisibilityRegistry';

describe('registry, executed', () => {
  test('65 cards, every one well-formed', () => {
    expect(PLAYER_VISIBILITY_CARDS).toHaveLength(65);
    for (const c of PLAYER_VISIBILITY_CARDS) {
      expect(typeof c.key).toBe('string');
      expect(c.key).toMatch(/^[a-z0-9_]+$/);
      expect(c.label).toBeTruthy();
      expect(c.icon).toBeTruthy();
      expect(c.tooltip).toBeTruthy();
      expect(c.group).toBeTruthy();
      expect(AUDIENCE_TAGS).toContain(c.audience);
    }
  });

  test('no duplicate keys', () => {
    // A duplicate silently shadows: the later card wins in the map, the earlier
    // one still renders a switch that does nothing.
    expect(new Set(PLAYER_VISIBILITY_KEYS).size).toBe(PLAYER_VISIBILITY_KEYS.length);
  });

  test('defaults cover every key and only five ship off', () => {
    expect(Object.keys(PLAYER_VISIBILITY_DEFAULTS)).toHaveLength(65);
    const off = Object.entries(PLAYER_VISIBILITY_DEFAULTS)
      .filter(([, v]) => !v).map(([k]) => k).sort();
    expect(off).toEqual(['balanced_scorecard', 'competitor_intel', 'esg_leadership',
                         'regret_meter', 'what_if_simulator'].sort());
  });

  test('grouping loses nothing and preserves order', () => {
    const groups = playerVisibilityGroups();
    const flat = groups.flatMap((g) => g.cards.map((c) => c.key));
    expect(flat).toEqual(PLAYER_VISIBILITY_KEYS);   // same cards, same order
    expect(groups.length).toBeGreaterThan(1);
    for (const g of groups) expect(g.cards.length).toBeGreaterThan(0);  // no empty section
  });

  test('the deriver produces the agreed profiles', () => {
    const count = (tags) => Object.values(visibilityForAudiences(tags)).filter(Boolean).length;
    expect(count(['core', 'scaffold', 'narrative', 'insight', 'debrief', 'flourish'])).toBe(40);
    expect(count(['core', 'scaffold', 'narrative', 'insight', 'finance', 'causal',
                  'compare', 'metacog', 'debrief', 'flourish'])).toBe(58);
    expect(count(['core', 'narrative', 'insight', 'finance', 'causal', 'specialist',
                  'compare', 'metacog', 'debrief'])).toBe(51);
    expect(count(['core', 'narrative', 'insight', 'finance', 'causal', 'specialist',
                  'compare', 'debrief'])).toBe(45);
  });

  test('the deriver is total and safe at the edges', () => {
    // It seeds a cohort's map, so a partial result would silently drop panels.
    for (const arg of [[], undefined, null, ['nonsense_tag']]) {
      const map = visibilityForAudiences(arg);
      expect(Object.keys(map)).toHaveLength(65);
      expect(Object.values(map).every((v) => v === false)).toBe(true);
    }
    const all = visibilityForAudiences(AUDIENCE_TAGS);
    expect(Object.values(all).every(Boolean)).toBe(true);
  });

  test('every audience tag is actually used', () => {
    // A declared-but-unused tag means a preset can name something that turns
    // nothing on — a switch-set with no effect.
    const used = new Set(PLAYER_VISIBILITY_CARDS.map((c) => c.audience));
    expect([...AUDIENCE_TAGS].filter((t) => !used.has(t))).toEqual([]);
  });
});
