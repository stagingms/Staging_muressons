/**
 * G-3 (v3) drift tripwire — the Shockwave console's catalog vs the engine.
 *
 * The console (admin/shockwave) shows crisis impact numbers from
 * app/components/shockwaveCatalog.js; the engine detonates with
 * backend/admin_router.py::_SHOCKWAVE_EVENTS. This test parses the backend
 * SOURCE, so a backend rebalance that forgets the frontend catalog fails CI
 * instead of silently letting the console lie about a destructive action
 * (the exact drift mechanism behind v1's F5 stale round labels).
 */
import fs from 'fs';
import path from 'path';
import { SHOCKWAVE_EVENTS, fmtHit } from '../app/components/shockwaveCatalog';

const BACKEND = path.join(__dirname, '..', '..', 'backend', 'admin_router.py');

function parseBackendCatalog() {
  const src = fs.readFileSync(BACKEND, 'utf8');
  const m = src.match(/_SHOCKWAVE_EVENTS\s*=\s*\{([\s\S]*?)\n\}/);
  if (!m) throw new Error('_SHOCKWAVE_EVENTS block not found in admin_router.py');
  const entries = {};
  const re = /"([a-z_]+)"\s*:\s*\{[^}]*"financial_impact"\s*:\s*(-?\d+)\s*,\s*"reputation_impact"\s*:\s*(-?\d+)/g;
  let hit;
  while ((hit = re.exec(m[1])) !== null) {
    entries[hit[1]] = { financial_impact: Number(hit[2]), reputation_impact: Number(hit[3]) };
  }
  return entries;
}

describe('Shockwave catalog stays in lockstep with the engine', () => {
  const backend = parseBackendCatalog();

  test('backend catalog parsed (sanity)', () => {
    expect(Object.keys(backend).length).toBeGreaterThanOrEqual(4);
  });

  test('same event ids on both sides', () => {
    expect(SHOCKWAVE_EVENTS.map((e) => e.id).sort()).toEqual(Object.keys(backend).sort());
  });

  test.each(SHOCKWAVE_EVENTS)('$id impact numbers match the engine', (ev) => {
    expect(backend[ev.id]).toBeDefined();
    expect(ev.financial_impact).toBe(backend[ev.id].financial_impact);
    expect(ev.reputation_impact).toBe(backend[ev.id].reputation_impact);
  });

  test('display strings derive from the numbers', () => {
    const pandemic = SHOCKWAVE_EVENTS.find((e) => e.id === 'pandemic');
    expect(fmtHit(pandemic)).toBe('-$6.0M · -6 rep');
  });
});
