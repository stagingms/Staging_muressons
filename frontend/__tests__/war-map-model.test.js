/**
 * warMapModel spot-check — the REDESIGNED operations/stakeholder situation map.
 *
 * The war-map was reworked (commit 9f8e08c) from "teams plotted by region" to
 * "the one world the sim models": Business Units at operating hubs, the five
 * reactive stakeholders at their home regions, and the round's crisis where it
 * strikes — all from the /api/admin/war-map cohort AGGREGATE payload. The old
 * test targeted the removed API (buildMapModel/regionAnchor/crisisFlags/...);
 * this replaces it with a determinism + behaviour guard on buildWarMap and the
 * helpers it actually exports.
 *
 * Crisis contract (Railway audit §3.2): the crisis NAME/ICON come from the
 * backend payload (`payload.crisis`, sourced from round_configs.get_round_crisis,
 * the single source of truth) — the client contributes only WHERE it strikes
 * (CRISIS_COORDS). The old client-side name catalog (ROUND_CRISIS) was removed
 * because it had drifted from the backend ("Cyclone" vs "Extreme Weather
 * Event"); these tests exercise the payload-driven contract.
 */
import {
  buildWarMap, project, buRadius, healthColor,
  BU_META, STAKEHOLDER_META, CRISIS_COORDS, STAGE_COLOR, STAGE_LABEL,
  MAP_W, MAP_H,
} from '../app/components/warMapModel';

const payload = (over = {}) => ({
  business_units: [
    { bu_id: 'pharma', revenue: 100_000_000, health: 70, slo: 60, carbon_intensity: 40, burnout: 20, teams: 3 },
    { bu_id: 'electronics', revenue: 50_000_000, health: 45, slo: 50, carbon_intensity: 80, burnout: 30, teams: 3 },
    { bu_id: 'software', revenue: 10_000_000, health: 20, slo: 30, carbon_intensity: 10, burnout: 55, teams: 3 },
  ],
  stakeholders: [
    { agent_id: 'the_regulator', name: 'The Regulator', stage: 'hostile', teams_hostile: 2 },
    { agent_id: 'the_journalist', name: 'The Journalist', stage: 'watching', teams_hostile: 0 },
  ],
  cohort_round: 5,
  crisis: { name: 'Extreme Weather Event', icon: '🌪️' },
  events: [],
  team_count: 3,
  ...over,
});

describe('buildWarMap (war-map redesign)', () => {
  test('is a pure, deterministic function of the payload', () => {
    const p = payload();
    const a = buildWarMap(p);
    const b = buildWarMap(JSON.parse(JSON.stringify(p)));
    expect(a).toEqual(b);
  });

  test('filters unknown BU and stakeholder ids', () => {
    const m = buildWarMap(payload({
      business_units: [{ bu_id: 'pharma', revenue: 1, health: 50 }, { bu_id: 'atlantis_widgets', revenue: 1, health: 50 }],
      stakeholders: [{ agent_id: 'the_regulator', stage: 'dormant' }, { agent_id: 'ghost', stage: 'dormant' }],
    }));
    expect(m.buNodes.map((n) => n.id)).toEqual(['pharma']);
    expect(m.shNodes.map((n) => n.id)).toEqual(['the_regulator']);
  });

  test('crisis is gated by the cohort round AND the backend payload', () => {
    // Round with coordinates + backend-supplied name → marker renders.
    expect(buildWarMap(payload({ cohort_round: 5 })).crisis.name).toMatch(/Extreme Weather/);
    // Round without coordinates (decision round) → no marker, even with a name.
    expect(buildWarMap(payload({ cohort_round: 1 })).crisis).toBeNull();
    // No backend crisis in the payload → no marker; the client must never
    // invent a name (that client-side copy is the drift the audit removed).
    expect(buildWarMap(payload({ cohort_round: 5, crisis: null })).crisis).toBeNull();
  });

  test('all node coordinates stay inside the viewBox', () => {
    const m = buildWarMap(payload());
    for (const n of [...m.buNodes, ...m.shNodes]) {
      expect(n.x).toBeGreaterThan(0); expect(n.x).toBeLessThan(MAP_W);
      expect(n.y).toBeGreaterThan(0); expect(n.y).toBeLessThan(MAP_H);
    }
  });

  test('stakeholder stage drives colour and label', () => {
    const m = buildWarMap(payload());
    const reg = m.shNodes.find((n) => n.id === 'the_regulator');
    expect(reg.color).toBe(STAGE_COLOR.hostile);
    expect(reg.label).toBe(STAGE_LABEL.hostile);
    expect(reg.escalated).toBe(true);
  });

  test('BU health → colour, revenue → radius (monotonic)', () => {
    expect(healthColor(70)).toBe('#2dd4bf');
    expect(healthColor(45)).toBe('#f59e0b');
    expect(healthColor(20)).toBe('#ef4444');
    expect(buRadius(100, 100)).toBeGreaterThan(buRadius(10, 100));
    expect(buRadius(50, 100)).toBe(buRadius(50, 100)); // deterministic
  });

  test('events list leads with the round crisis', () => {
    const m = buildWarMap(payload({ cohort_round: 5, events: [] }));
    expect(m.events[0]).toContain('Round 5');
    expect(m.events[0]).toMatch(/Extreme Weather/);
  });

  test('projection maps lon/lat into the viewBox', () => {
    const p = project(0, 0); // equator / prime meridian → map centre
    expect(p.x).toBeCloseTo(MAP_W / 2);
    expect(p.y).toBeCloseTo(MAP_H / 2);
    expect(Object.keys(BU_META)).toContain('pharma');
    expect(Object.keys(STAKEHOLDER_META)).toContain('the_regulator');
    // Coordinates only — R5 strikes in the Bay of Bengal; names live backend-side.
    expect(CRISIS_COORDS[5]).toEqual({ lon: 90, lat: 15 });
  });
});
