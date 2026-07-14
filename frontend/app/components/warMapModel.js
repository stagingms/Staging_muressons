/**
 * warMapModel.js — Operations & Stakeholder situation map (redesign).
 *
 * The old model plotted TEAMS by region_id — which defaults to "" for standard
 * cohorts, so every team piled onto one "Global HQ" anchor. This model instead
 * renders the ONE world the simulation actually models: Muressons' Business
 * Units at their operating locations, the five reactive stakeholders at their
 * home regions (coloured by escalation), and the current round's crisis at the
 * place it strikes. All figures are cohort AGGREGATES from /api/admin/war-map.
 */

export const MAP_W = 1000;
export const MAP_H = 520;

export const project = (lon, lat) => ({
  x: ((lon + 180) / 360) * MAP_W,
  y: ((90 - lat) / 180) * MAP_H,
});

// Muressons' four default Business Units, at plausible operating hubs.
export const BU_META = {
  pharma: { label: 'Pharmaceuticals', lon: 8.5, lat: 47.4 },        // Rhine / Basel
  electronics: { label: 'Electronics', lon: 103.8, lat: 1.35 },     // Singapore
  consumer_goods: { label: 'Consumer Goods', lon: 74.0, lat: 18.5 },// Deccan / Pune
  software: { label: 'Software', lon: -74.0, lat: 40.7 },           // New York
};

// The five reactive stakeholders. Positions are curated MAP coordinates
// (0..MAP_W, 0..MAP_H), not real cities: anchoring to Brussels/London/Berlin
// piled three markers onto the Pharma unit in Europe, and the Deccan community
// + Hyderabad journalist onto Consumer Goods. These are spaced so no marker or
// label overlaps a Business Unit or another stakeholder, while staying in the
// right regional neighbourhood.
export const STAKEHOLDER_META = {
  the_regulator: { x: 452, y: 96 },               // EU — upper-left of Pharma
  the_gen_z_employee: { x: 600, y: 86 },          // EU — upper-right of Pharma
  the_institutional_investor: { x: 372, y: 236 }, // financial hub — open mid-Atlantic
  the_journalist: { x: 852, y: 150 },             // South Asia — right, above Electronics
  the_community_activist: { x: 648, y: 306 },     // South Asia — below Consumer Goods
};

// Round → the crisis that fires and where it strikes.
export const ROUND_CRISIS = {
  3: { name: 'Scope 3 supply-chain exposure', lon: 30, lat: 5 },
  4: { name: 'Contagion — the Round 1 reckoning', lon: 15, lat: 25 },
  5: { name: 'Cyclone — physical climate risk', lon: 90, lat: 15 },   // Bay of Bengal
  6: { name: 'AI bias scandal', lon: -95, lat: 40 },
  8: { name: 'Water scarcity (Blue Stress)', lon: 75, lat: 20 },      // Deccan
  9: { name: 'Just transition pressure', lon: 25, lat: -12 },
  10: { name: 'Year-5 activist ultimatum', lon: -52, lat: -14 },  // open South Atlantic
};

export const STAGE_COLOR = {
  dormant: '#2dd4bf', watching: '#2dd4bf', agitated: '#f59e0b', hostile: '#ef4444', triggered: '#ef4444',
};
export const STAGE_LABEL = {
  dormant: 'calm', watching: 'watching', agitated: 'agitated', hostile: 'hostile', triggered: 'on strike',
};

export const healthColor = (h) => (h >= 60 ? '#2dd4bf' : h >= 40 ? '#f59e0b' : '#ef4444');

export function buRadius(rev, maxRev) {
  const t = Math.sqrt(Math.max(0, rev) / Math.max(1, maxRev));
  return Math.round((11 + t * 15) * 10) / 10;
}

/** Turn the /api/admin/war-map aggregate payload into positioned map nodes. */
export function buildWarMap(payload) {
  const bus = (payload && payload.business_units) || [];
  const maxRev = Math.max(1, ...bus.map((b) => b.revenue || 0));
  const buNodes = bus
    .filter((b) => BU_META[b.bu_id])
    .map((b) => {
      const m = BU_META[b.bu_id];
      const p = project(m.lon, m.lat);
      return {
        id: b.bu_id, label: m.label, x: p.x, y: p.y,
        r: buRadius(b.revenue, maxRev), color: healthColor(b.health),
        health: b.health, slo: b.slo, ci: b.carbon_intensity, burn: b.burnout, teams: b.teams,
      };
    });

  const shNodes = ((payload && payload.stakeholders) || [])
    .filter((s) => STAKEHOLDER_META[s.agent_id])
    .map((s) => {
      const m = STAKEHOLDER_META[s.agent_id];
      const stage = s.stage || 'dormant';
      return {
        id: s.agent_id, name: s.name, x: m.x, y: m.y, stage,
        color: STAGE_COLOR[stage] || '#2dd4bf', label: STAGE_LABEL[stage] || stage,
        hostile: s.teams_hostile || 0, escalated: ['agitated', 'hostile', 'triggered'].includes(stage),
      };
    });

  const round = (payload && payload.cohort_round) || 0;
  const c = ROUND_CRISIS[round];
  const crisis = c ? { ...c, ...project(c.lon, c.lat), round } : null;

  const events = ((payload && payload.events) || []).map((e) =>
    e.kind === 'stakeholder'
      ? `${e.name} · ${STAGE_LABEL[e.stage] || e.stage}${e.teams ? ` · ${e.teams} team${e.teams > 1 ? 's' : ''} hostile` : ''}`
      : `${(BU_META[e.bu_id] && BU_META[e.bu_id].label) || e.bu_id} under stress · health ${e.health}`
  );
  if (crisis) events.unshift(`Round ${crisis.round} · ${crisis.name}`);

  return { buNodes, shNodes, crisis, events, round, teamCount: (payload && payload.team_count) || 0 };
}
