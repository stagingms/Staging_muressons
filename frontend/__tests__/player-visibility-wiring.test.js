/**
 * Player-visibility toggles: catalogue ↔ UI ↔ actual gating.
 *
 * The cohort-formation "PLAYER DASHBOARD" group renders one switch per key in
 * the shared player registry (config/playerVisibilityRegistry.js). It used to
 * read a local PLAYER_ANALYTICS array inside CreateCohortModal, which had drifted
 * from a second copy in AnalyticsControlPanel — 19 keys against 3, with the
 * short list feeding that panel's DEFAULT_VIS, so saving from there wrote a
 * player map missing sixteen keys. Both surfaces now import the registry, and
 * this test reads the registry for the same reason. The backend setter SILENTLY DROPS any key
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

const registrySrc = fs.readFileSync(path.join(APP, 'config', 'playerVisibilityRegistry.js'), 'utf8');
const modalSrc = fs.readFileSync(path.join(APP, 'components', 'CreateCohortModal.js'), 'utf8');
const analyticsSrc = fs.readFileSync(path.join(ROOT, 'backend', 'admin_analytics.py'), 'utf8');

/** Keys rendered as switches in the cohort-formation Player Dashboard group. */
function uiKeys() {
  const block = registrySrc.slice(
    registrySrc.indexOf('export const PLAYER_VISIBILITY_CARDS'),
    registrySrc.indexOf('export const PLAYER_VISIBILITY_KEYS')
  );
  return [...block.matchAll(/\{\s*key:\s*'([a-z0-9_]+)'/g)].map((m) => m[1]);
}

/**
 * The form must actually RENDER the registry rather than keep its own list —
 * otherwise uiKeys() above would be measuring a file nothing displays.
 */
function modalRendersRegistry() {
  // The grid is rendered through playerVisibilityGroups(), which derives from
  // the same cards — so covering every group covers every key by construction.
  // (It used to be a flat PLAYER_ANALYTICS.map; 65 switches in one wall is a
  // search problem, not a control surface.)
  return /PLAYER_ANALYTICS\s*=\s*PLAYER_VISIBILITY_CARDS/.test(modalSrc)
      && /playerVisibilityGroups\(\)\.map/.test(modalSrc);
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
  test('the cohort form renders the shared registry, not its own copy', () => {
    expect(modalRendersRegistry()).toBe(true);
  });

  test('the control panel shares the registry and defaults every key', () => {
    // Its old 3-key list fed DEFAULT_VIS, and this panel PUTs the WHOLE map —
    // so a save from here dropped every key the short list omitted.
    const src = fs.readFileSync(path.join(APP, 'components', 'AnalyticsControlPanel.js'), 'utf8');
    expect(src).toMatch(/PLAYER_ANALYTICS\s*=\s*PLAYER_VISIBILITY_CARDS/);
    expect(src).toMatch(/player:\s*PLAYER_VISIBILITY_DEFAULTS/);
    expect(src).not.toMatch(/key !== 'what_if_simulator'/);
  });

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

/**
 * Player-facing round surfaces that live in the PEDAGOGICAL toggle system
 * rather than the visibility catalogue.
 *
 * These are a separate mechanism (a cohort-settings override read through
 * getPedagogicalToggles, not the analytics-visibility map), and that is fine —
 * but they must still be reachable when a facilitator sets a cohort up. Board
 * Room Moment was not: it existed only in AnalyticsControlPanel.PLAYER_FEATURES,
 * which a facilitator creating a cohort never opens. Reported as "some toggles
 * are missing for the player dashboard visibility".
 *
 * The persistence trap this also pins: save_cohort_pedagogical_settings derives
 * its per-cohort allow-list from pedagogical_engine.DEFAULT_PEDAGOGICAL_TOGGLES,
 * so a key offered in the form but absent from that dict is silently dropped on
 * save — a switch that looks saved and changes nothing. consequence_map_enabled
 * was exactly that.
 */
describe('player-facing pedagogical toggles', () => {
  const pedSrc = fs.readFileSync(
    path.join(ROOT, 'backend', 'pedagogical_engine.py'), 'utf8');

  /** Keys offered in the cohort form's Pedagogical Features group. */
  function formPedKeys() {
    const block = modalSrc.slice(
      modalSrc.indexOf('const PEDAGOGICAL_TOGGLES'),
      modalSrc.indexOf('const ENGINE_MODULE_TOGGLES'),
    );
    return [...block.matchAll(/\{\s*key:\s*'([a-z0-9_]+)'/g)].map((m) => m[1]);
  }

  /** Keys a per-cohort override will actually persist for. */
  function persistableKeys() {
    const start = pedSrc.indexOf('DEFAULT_PEDAGOGICAL_TOGGLES = {');
    const block = pedSrc.slice(start, pedSrc.indexOf('\n}', start));
    return new Set([...block.matchAll(/^\s*"([a-z0-9_]+)":/gm)].map((m) => m[1]));
  }

  test('the player-facing round surfaces are reachable at cohort setup', () => {
    const keys = new Set(formPedKeys());
    expect(keys.has('board_room_moments_enabled')).toBe(true);
    expect(keys.has('consequence_map_enabled')).toBe(true);
  });

  test('every toggle the form offers can actually persist per cohort', () => {
    const persistable = persistableKeys();
    const dropped = formPedKeys().filter(
      (k) => k !== 'self_learning_mode' && !persistable.has(k));
    expect(dropped).toEqual([]); // else the save is a no-op the facilitator trusts
  });

  test('Board Room Moment is not confused with the end-of-game Boardroom', () => {
    // Two different surfaces, two different systems, similar names. The
    // visibility key gates the R10 Boardroom Showdown; the pedagogical key gates
    // the per-round reflection. Both must exist, and separately.
    expect(new Set(uiKeys()).has('boardroom_showdown')).toBe(true);
    expect(new Set(formPedKeys()).has('board_room_moments_enabled')).toBe(true);
  });
});

/**
 * Briefing videos: the switch and the source must BOTH be reachable at setup.
 *
 * The Read | Watch choice on round briefings was ungated — a cohort could not be
 * made read-only — and its URL config lived only in the Analytics Control Panel,
 * the same "control exists but not where a cohort is created" gap that hid Board
 * Room Moment. A switch with no URL behind it does nothing, and a URL with no
 * switch cannot be declined, so both belong in the cohort form.
 */
describe('briefing video configuration', () => {
  const briefingSrc = fs.readFileSync(
    path.join(APP, 'components', 'RoundBriefing.js'), 'utf8');

  test('the Watch option is a cohort switch', () => {
    expect(new Set(uiKeys()).has('briefing_video')).toBe(true);
    expect(new Set(backendKeys()).has('briefing_video')).toBe(true);
    expect(gatedKeys().has('briefing_video')).toBe(true);
  });

  test('one resolution point gates both the toggle and the video pane', () => {
    // Checking the key twice would let the control and the pane disagree — and a
    // player left in watch mode when the switch flips off would get a blank frame
    // instead of the written briefing.
    expect(briefingSrc).toMatch(
      /const briefingEmbed = isPlayerVisible\('briefing_video'\) \? toEmbed\(briefingVideoUrl\) : null;/);
    expect((briefingSrc.match(/isPlayerVisible\('briefing_video'\)/g) || []).length).toBe(1);
  });

  test('the cohort form can set the video URL, and only when one was entered', () => {
    expect(modalSrc).toMatch(/briefingVideoBase/);
    expect(modalSrc).toMatch(/sessions\/\$\{sid\}\/briefing-videos/);
    // Guarded: an empty field must not POST and blank out a value inherited
    // from a cohort template or the global default.
    expect(modalSrc).toMatch(/if \(briefingVideoBase\.trim\(\)\) \{/);
  });

  test('the URL keys are cohort-overridable, or the per-cohort POST is a no-op', () => {
    const shared = fs.readFileSync(
      path.join(ROOT, 'backend', 'admin_shared.py'), 'utf8');
    const start = shared.indexOf('COHORT_OVERRIDABLE_KEYS');
    const block = shared.slice(start, shared.indexOf('}', start));
    expect(block).toMatch(/"briefing_video_base"/);
    expect(block).toMatch(/"briefing_videos"/);
  });
});
