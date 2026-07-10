/**
 * warMapModel.js — W-E (W7)
 *
 * Pure, deterministic helpers behind the Region War-Map projector.
 * Everything derives from the existing read-only /api/admin/leaderboard
 * payload (region_id, active_flags, terminal_value, group_reputation,
 * round_number). No fetches, no state writes, no randomness.
 */

export const MAP_W = 1000;
export const MAP_H = 520;

// Equirectangular projection into the map viewBox.
export const project = (lon, lat) => ({
  x: ((lon + 180) / 360) * MAP_W,
  y: ((90 - lat) / 180) * MAP_H,
});

// Region anchors — the stakeholder-config regions the sim ships with,
// plus the Global HQ fallback for sessions without a region_id.
export const REGIONS = {
  europe: { label: 'EUROPE', lon: 8.5, lat: 47.4 },        // Zurich
  africa: { label: 'AFRICA', lon: 36.8, lat: -1.3 },       // Nairobi
  south_asia: { label: 'SOUTH ASIA', lon: 77.2, lat: 21.0 }, // Deccan
  asean: { label: 'ASEAN', lon: 103.8, lat: 1.35 },        // Singapore
  '': { label: 'GLOBAL HQ', lon: -74.0, lat: 40.7 },       // New York
};

export function regionAnchor(regionId) {
  const key = Object.prototype.hasOwnProperty.call(REGIONS, regionId || '') ? (regionId || '') : '';
  const r = REGIONS[key];
  return { ...project(r.lon, r.lat), label: r.label, key };
}

// Deterministic ring spread for multiple nodes sharing a region.
export function spreadPosition(anchor, idx, count) {
  if (count <= 1) return { x: anchor.x, y: anchor.y };
  const angle = (2 * Math.PI * idx) / count - Math.PI / 2;
  const radius = 22 + 6 * Math.floor(idx / 8);
  return { x: anchor.x + radius * Math.cos(angle), y: anchor.y + radius * Math.sin(angle) };
}

// Crisis detection over the leaderboard's active_flags name list.
export const CRISIS_PATTERNS = ['crisis', 'black_swan', 'strike', 'scandal', 'breach', 'recall', 'shockwave', 'cyclone', 'greenwashing'];

export function crisisFlags(activeFlags) {
  return (activeFlags || []).filter((f) => CRISIS_PATTERNS.some((p) => String(f).toLowerCase().includes(p)));
}

export const isBlackSwan = (activeFlags) =>
  (activeFlags || []).some((f) => String(f).toLowerCase().includes('black_swan'));

export const nodeColor = (rep) => (rep >= 55 ? '#2dd4bf' : rep >= 40 ? '#f59e0b' : '#ef4444');

export function nodeRadius(tv, maxTv) {
  const t = Math.sqrt(Math.max(0, tv) / Math.max(1, maxTv));
  return Math.round((8 + t * 14) * 10) / 10;
}

export const prettyFlag = (f) => String(f).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

/**
 * Build the full map model from a leaderboard payload. Same row filter as
 * the Trading Floor board. Deterministic: rows are sorted by session_id
 * within each region before spreading, so node positions are stable
 * across polls regardless of payload order.
 */
export function buildMapModel(leaderboard) {
  const rows = (leaderboard || []).filter((x) => x.player_name || x.parent_cohort_id);
  const maxTv = Math.max(1, ...rows.map((r) => r.terminal_value || 0));
  const byRegion = {};
  for (const r of rows) {
    const key = regionAnchor(r.region_id).key;
    (byRegion[key] = byRegion[key] || []).push(r);
  }
  const nodes = [];
  for (const key of Object.keys(byRegion).sort()) {
    const anchor = regionAnchor(key);
    const group = byRegion[key].slice().sort((a, b) => String(a.session_id).localeCompare(String(b.session_id)));
    group.forEach((r, i) => {
      const pos = spreadPosition(anchor, i, group.length);
      const crises = crisisFlags(r.active_flags);
      nodes.push({
        id: r.session_id,
        name: r.player_name || r.cohort_name || 'Team',
        region: anchor.label,
        x: Math.round(pos.x * 10) / 10,
        y: Math.round(pos.y * 10) / 10,
        radius: nodeRadius(r.terminal_value || 0, maxTv),
        color: nodeColor(r.group_reputation ?? 50),
        round: r.round_number || 1,
        crises,
        blackSwan: isBlackSwan(r.active_flags),
        tv: r.terminal_value || 0,
      });
    });
  }
  const maxRound = Math.max(1, ...rows.map((r) => r.round_number || 1));
  // R5 is the cyclone round — the storm crosses the Bay of Bengal while any
  // visible team is playing it.
  const cycloneActive = rows.some((r) => (r.round_number || 1) === 5);
  const events = nodes
    .filter((n) => n.crises.length > 0)
    .flatMap((n) => n.crises.map((f) => `${n.name} · ${prettyFlag(f)} · ${n.region}`));
  return { nodes, maxRound, cycloneActive, events };
}
