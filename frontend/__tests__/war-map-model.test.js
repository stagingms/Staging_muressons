/**
 * W-E determinism spot-check — warMapModel.
 * The map is a pure function of the leaderboard payload: same rows ⇒ same
 * nodes (order-independent), crisis detection by flag-name patterns,
 * region fallback to Global HQ, R5 cyclone gating.
 */
import {
  buildMapModel, regionAnchor, crisisFlags, isBlackSwan,
  nodeColor, nodeRadius, spreadPosition, MAP_W, MAP_H,
} from '../app/components/warMapModel';

const row = (id, over = {}) => ({
  session_id: id,
  player_name: `Team ${id}`,
  parent_cohort_id: 'cohort-1',
  region_id: 'europe',
  terminal_value: 100_000_000,
  group_reputation: 60,
  round_number: 3,
  active_flags: [],
  ...over,
});

describe('buildMapModel (W7)', () => {
  test('deterministic and order-independent', () => {
    const rows = [row('a'), row('b', { region_id: 'asean' }), row('c', { region_id: '' })];
    const m1 = buildMapModel(rows);
    const m2 = buildMapModel([...rows].reverse());
    expect(m1).toEqual(m2);
    expect(m1).toEqual(buildMapModel(JSON.parse(JSON.stringify(rows))));
  });

  test('filters non-team rows, same rule as the Trading Floor board', () => {
    const m = buildMapModel([row('a'), { session_id: 'ghost' }]);
    expect(m.nodes).toHaveLength(1);
  });

  test('unknown or empty region falls back to Global HQ', () => {
    expect(regionAnchor('').label).toBe('GLOBAL HQ');
    expect(regionAnchor('atlantis').label).toBe('GLOBAL HQ');
    expect(regionAnchor('south_asia').label).toBe('SOUTH ASIA');
  });

  test('all node coordinates stay inside the viewBox', () => {
    const rows = ['europe', 'africa', 'south_asia', 'asean', ''].flatMap((r, i) =>
      [0, 1, 2].map((j) => row(`${r}-${j}`, { region_id: r })));
    for (const n of buildMapModel(rows).nodes) {
      expect(n.x).toBeGreaterThan(0); expect(n.x).toBeLessThan(MAP_W);
      expect(n.y).toBeGreaterThan(0); expect(n.y).toBeLessThan(MAP_H);
    }
  });

  test('cyclone appears only while some team is in Round 5', () => {
    expect(buildMapModel([row('a', { round_number: 4 })]).cycloneActive).toBe(false);
    expect(buildMapModel([row('a', { round_number: 5 })]).cycloneActive).toBe(true);
  });

  test('crisis flags matched by pattern; black swan flagged separately', () => {
    expect(crisisFlags(['greenwashing_scandal', 'esg_reporting'])).toEqual(['greenwashing_scandal']);
    expect(isBlackSwan(['black_swan_r6'])).toBe(true);
    expect(isBlackSwan(['strike_occurred'])).toBe(false);
    const m = buildMapModel([row('a', { active_flags: ['black_swan_r6'] })]);
    expect(m.nodes[0].blackSwan).toBe(true);
    expect(m.events).toHaveLength(1);
    expect(m.events[0]).toContain('Team a');
  });

  test('node visuals are monotonic: reputation → colour, EV → radius', () => {
    expect(nodeColor(70)).toBe('#2dd4bf');
    expect(nodeColor(45)).toBe('#f59e0b');
    expect(nodeColor(20)).toBe('#ef4444');
    expect(nodeRadius(100, 100)).toBeGreaterThan(nodeRadius(10, 100));
  });

  test('ring spread is deterministic and centred for singletons', () => {
    const anchor = { x: 100, y: 100 };
    expect(spreadPosition(anchor, 0, 1)).toEqual({ x: 100, y: 100 });
    expect(spreadPosition(anchor, 1, 4)).toEqual(spreadPosition(anchor, 1, 4));
  });
});
