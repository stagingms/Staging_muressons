/**
 * Player-visibility toggles: catalogue ↔ UI ↔ actual gating.
 *
 * The cohort-formation "PLAYER DASHBOARD" group renders one switch per key in
 * CreateCohortModal.PLAYER_ANALYTICS. The backend setter SILENTLY DROPS any key
 * missing from admin_analytics._analytics_visibility["player"], and a toggle
 * that no component reads gates nothing at all. Both failure modes are
 * invisible in review and to the facilitator flipping the switch.
 *
 * Audited 2026-07-20: only `what_if_simulator` was actually wired — the other
 * fourteen switches did nothing. This file:
 *   1. pins UI ↔ backend-catalogue agreement, and
 *   2. RATCHETS the unwired set: newly added keys must gate something, and the
 *      known-unwired list may only shrink.
 *
 * Fixing an entry means adding an isPlayerVisible('key') check at that panel's
 * render site and deleting it from UNWIRED below.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const APP = path.join(__dirname, '..', 'app');

const modalSrc = fs.readFileSync(path.join(APP, 'components', 'CreateCohortModal.js'), 'utf8');
const analyticsSrc = fs.readFileSync(path.join(ROOT, 'backend', 'admin_analytics.py'), 'utf8');

/** Keys rendered as switches in the cohort-formation Player Dashboard group. */
function uiKeys() {
  const block = modalSrc.slice(
    modalSrc.indexOf('const PLAYER_ANALYTICS'),
    modalSrc.indexOf('const PEDAGOGICAL_TOGGLES')
  );
  return [...block.matchAll(/\{\s*key:\s*'([a-z0-9_]+)'/g)].map((m) => m[1]);
}

/** Keys the backend will actually persist. */
function backendKeys() {
  const start = analyticsSrc.indexOf('"player": {');
  const block = analyticsSrc.slice(start, analyticsSrc.indexOf('\n    },', start));
  return [...block.matchAll(/^\s*"([a-z0-9_]+)":\s*(True|False)/gm)].map((m) => m[1]);
}

/**
 * Every key that actually gates rendering.
 *
 * Two legitimate shapes:
 *   a) a literal call — isPlayerVisible('risk_radar')
 *   b) a lookup map consumed by a gating call — the rail tab bar filters on
 *      isPlayerVisible(tab.vis) where tab.vis comes from RAIL_TAB_VIS. Keys
 *      there are genuinely gating, so the scan must see them or it would
 *      report a wired surface as unwired.
 */
function gatedKeys() {
  const found = new Set();
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(p);
      else if (/\.jsx?$/.test(entry.name)) {
        const src = fs.readFileSync(p, 'utf8');
        for (const m of src.matchAll(/isPlayerVisible\(\s*'([a-z0-9_]+)'\s*\)/g)) found.add(m[1]);

        // (b) — only counts if the map is genuinely consumed by a gating call.
        const mapMatch = src.match(/const RAIL_TAB_VIS\s*=\s*\{([\s\S]*?)\};/);
        if (mapMatch && /isPlayerVisible\(\s*tab\.vis\s*\)/.test(src)) {
          for (const m of mapMatch[1].matchAll(/:\s*'([a-z0-9_]+)'/g)) found.add(m[1]);
        }

        // (c) server-driven gating — PlayerAnalytics filters its TABS on the
        // visibility map the analytics endpoint returns. Equally real, just
        // enforced server-side; the payload is cohort-resolved (see
        // admin_analytics.get_player_analytics).
        const tabsMatch = src.match(/const TABS\s*=\s*\[([\s\S]*?)\];/);
        if (tabsMatch && /visibility\[\s*t\.key\s*\]\s*!==\s*false/.test(src)) {
          for (const m of tabsMatch[1].matchAll(/key:\s*'([a-z0-9_]+)'/g)) found.add(m[1]);
        }
      }
    }
  };
  walk(APP);
  return found;
}

// EMPTY as of 2026-07-20 — every player toggle now gates a real surface.
// If this list ever needs an entry again, that is a regression: a switch the
// facilitator can flip which changes nothing the player sees.
const UNWIRED = new Set([]);

describe('player visibility toggles', () => {
  test('every UI switch exists in the backend catalogue', () => {
    const backend = new Set(backendKeys());
    const missing = uiKeys().filter((k) => !backend.has(k));
    expect(missing).toEqual([]); // else the setter silently drops the toggle
  });

  test('every backend key is offered in the UI', () => {
    const ui = new Set(uiKeys());
    const orphans = backendKeys().filter((k) => !ui.has(k));
    expect(orphans).toEqual([]); // else a facilitator can never reach it
  });

  test('the four right-rail surfaces are toggleable', () => {
    const ui = new Set(uiKeys());
    // 'decisions' intentionally reuses decision_history — one surface, one switch.
    for (const k of ['rail_mailbox', 'rail_engines', 'rail_climate', 'market_reality_feed']) {
      expect(ui.has(k)).toBe(true);
    }
    expect(ui.has('decision_history')).toBe(true);
  });

  test('rail surfaces actually gate rendering', () => {
    const gated = gatedKeys();
    for (const k of ['rail_mailbox', 'rail_engines', 'rail_climate',
                     'market_reality_feed', 'decision_history']) {
      expect(gated.has(k)).toBe(true);
    }
  });

  test('the unwired-toggle debt does not grow', () => {
    const gated = gatedKeys();
    const stillUnwired = uiKeys().filter((k) => !gated.has(k));
    const unexpected = stillUnwired.filter((k) => !UNWIRED.has(k));
    expect(unexpected).toEqual([]); // a NEW toggle must gate something
  });

  test('fixed toggles are removed from the debt list', () => {
    const gated = gatedKeys();
    const nowWired = [...UNWIRED].filter((k) => gated.has(k));
    expect(nowWired).toEqual([]); // ratchet: delete it from UNWIRED
  });
});
