/**
 * Experience level → default player visibility.
 *
 * The four scenario presets have always ADVERTISED a visibility posture in their
 * own subtitles — Classroom "Foundation Visibility", Workshop "Progressive
 * Disclosure", Executive "Full Visibility + Audit Trail", Chaos "No
 * Scaffolding" — while every cohort in fact received the identical 65-panel
 * cockpit. `default_visibility` did not exist anywhere in the codebase.
 *
 * The schema is deliberately NOT four booleans per key. That would be 260
 * hand-maintained cells, which is the exact shape of every drift bug this area
 * has produced (a 3-key list against a 19-key one; a toggle offered but not
 * persistable; a dropdown offering a value the validator rejects). Instead each
 * card carries ONE `audience` tag and each preset names the tags it shows, so a
 * new surface is one word and lands correctly in all four presets automatically.
 *
 * What these tests protect is that derivation: an untagged card, a preset naming
 * a tag that does not exist, or a hand-written per-key exception all break the
 * property that the profiles cannot drift from the catalogue.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const APP = path.join(__dirname, '..', 'app');

const registrySrc = fs.readFileSync(path.join(APP, 'config', 'playerVisibilityRegistry.js'), 'utf8');
const modalSrc = fs.readFileSync(path.join(APP, 'components', 'CreateCohortModal.js'), 'utf8');
const routerSrc = fs.readFileSync(path.join(ROOT, 'backend', 'admin_router.py'), 'utf8');

const MODES = ['classroom_easy', 'workshop_standard', 'executive_hard', 'chaos_mode'];

function declaredTags() {
  const block = registrySrc.slice(
    registrySrc.indexOf('export const AUDIENCE_TAGS = ['),
    registrySrc.indexOf('];', registrySrc.indexOf('export const AUDIENCE_TAGS = [')));
  return new Set([...block.matchAll(/'([a-z]+)'/g)].map((m) => m[1]));
}

/** key → audience, straight from the card list. */
function cardAudiences() {
  const block = registrySrc.slice(
    registrySrc.indexOf('export const PLAYER_VISIBILITY_CARDS'),
    registrySrc.indexOf('export const PLAYER_VISIBILITY_KEYS'));
  const out = {};
  for (const line of block.split('\n')) {
    const k = line.match(/\{ key: '([a-z0-9_]+)'/);
    if (!k) continue;
    const a = line.match(/audience: '([a-z]+)'/);
    out[k[1]] = a ? a[1] : null;
  }
  return out;
}

/** preset id → { audiences:Set, reveal:number }, from the Python source. */
function presets() {
  const out = {};
  for (const id of MODES) {
    const seg = routerSrc.slice(routerSrc.indexOf(`"id": "${id}"`),
                                routerSrc.indexOf(`"id": "${id}"`) + 3000);
    const tags = seg.match(/"default_audiences": \[([\s\S]*?)\]/);
    const rev = seg.match(/"results_reveal_round": (\d+)/);
    out[id] = {
      audiences: new Set(tags ? [...tags[1].matchAll(/"([a-z]+)"/g)].map((m) => m[1]) : []),
      reveal: rev ? Number(rev[1]) : null,
    };
  }
  return out;
}

const visibleIn = (id, aud) => Object.entries(cardAudiences())
  .filter(([, a]) => presets()[id].audiences.has(a)).map(([k]) => k);

describe('audience tagging', () => {
  test('every card carries a tag, and every tag is declared', () => {
    const tags = declaredTags();
    const cards = cardAudiences();
    const untagged = Object.entries(cards).filter(([, a]) => !a).map(([k]) => k);
    expect(untagged).toEqual([]);           // else it silently vanishes from every preset
    const unknown = [...new Set(Object.values(cards))].filter((a) => !tags.has(a));
    expect(unknown).toEqual([]);
  });

  test('all 64 keys are tagged', () => {
    expect(Object.keys(cardAudiences())).toHaveLength(64); // 65 before market_ticker retired (Phase 1)
  });

  test('the derivation helper exists and is the only mapping', () => {
    expect(registrySrc).toMatch(/export function visibilityForAudiences\(tags\)/);
    // A per-key exception list would reintroduce the 260-cell table by the back door.
    expect(registrySrc).not.toMatch(/AUDIENCE_OVERRIDES|PRESET_VISIBILITY\s*=/);
  });
});

describe('preset profiles', () => {
  test('every preset names only declared tags', () => {
    const tags = declaredTags();
    for (const id of MODES) {
      const bad = [...presets()[id].audiences].filter((a) => !tags.has(a));
      expect({ id, bad }).toEqual({ id, bad: [] });
    }
  });

  test('each preset carries an audience set and a reveal round', () => {
    for (const id of MODES) {
      expect(presets()[id].audiences.size).toBeGreaterThan(0);
      expect(typeof presets()[id].reveal).toBe('number');
    }
  });

  test('the profiles match the agreed design', () => {
    const n = (id) => visibleIn(id).length;
    expect(n('classroom_easy')).toBe(40);
    expect(n('workshop_standard')).toBe(57); // 58 before market_ticker retired (Phase 1)
    expect(n('executive_hard')).toBe(50); // 51 before market_ticker retired (Phase 1)
    expect(n('chaos_mode')).toBe(44); // 45 before market_ticker retired (Phase 1)
  });

  test('Classroom hides finance vocabulary and peer ranking', () => {
    const on = new Set(visibleIn('classroom_easy'));
    for (const k of ['ebitda_waterfall', 'balance_sheet_modal', 'terminal_valuation_calc',
                     'peer_benchmarking', 'competitor_intel']) {
      expect([k, on.has(k)]).toEqual([k, false]);
    }
    // ...while keeping the narrative and every scaffold.
    for (const k of ['ceo_diary', 'briefing_stakeholder_voices', 'ai_advisor',
                     'resources_sidebar', 'briefing_video']) {
      expect([k, on.has(k)]).toEqual([k, true]);
    }
  });

  test('Executive drops coaching and gamification, keeps every instrument', () => {
    const on = new Set(visibleIn('executive_hard'));
    for (const k of ['ai_advisor', 'reflective_prompt', 'achievement_badges',
                     'front_page_reveal', 'briefing_theory_card']) {
      expect([k, on.has(k)]).toEqual([k, false]);
    }
    for (const k of ['terminal_valuation_calc', 'balance_sheet_modal', 'consequence_dna_sankey',
                     'esg_constellation_3d', 'calibration_report']) {
      expect([k, on.has(k)]).toEqual([k, true]);
    }
  });

  test("Workshop's Progressive Disclosure is literal, not decorative", () => {
    // Peer data PRESENT but withheld until round 3 — not simply absent.
    expect(new Set(visibleIn('workshop_standard')).has('peer_benchmarking')).toBe(true);
    expect(presets().workshop_standard.reveal).toBe(3);
    expect(presets().classroom_easy.reveal).toBe(0);
    expect(presets().executive_hard.reveal).toBe(0);
  });

  test('the debrief payoff survives in every mode', () => {
    for (const id of MODES) {
      const on = new Set(visibleIn(id));
      for (const k of ['archetype_reveal', 'boardroom_showdown', 'mirror_debrief']) {
        expect([id, k, on.has(k)]).toEqual([id, k, true]);
      }
    }
  });
});

describe('application at cohort creation', () => {
  test('the profile is applied from ONE place, not on the preset click', () => {
    // The scenario-preset fetch and the global-visibility fetch are independent;
    // seeding on click meant whichever resolved second won, and a preset chosen
    // before the defaults arrived was silently overwritten a moment later.
    expect(modalSrc).toMatch(/visibilityForAudiences\(preset\.default_audiences\)/);
    expect(modalSrc).toMatch(
      /\}, \[selectedExperienceLevel, scenarioPresets, visibilityDefaults, visibilityCustomised\]\);/);
    expect(modalSrc).toMatch(/import \{[^}]*visibilityForAudiences[^}]*\} from '\.\.\/config\/playerVisibilityRegistry'/);
    // The property is that LOAD-TIME seeding happens in exactly one place. The
    // reset button and the count helper also call the deriver, but neither runs
    // on load, so neither can race the fetches. What must stay true is that the
    // preset BUTTON does not seed.
    const clickHandler = modalSrc.slice(
      modalSrc.indexOf('setSelectedExperienceLevel(p.id);'),
      modalSrc.indexOf('style={{', modalSrc.indexOf('setSelectedExperienceLevel(p.id);')));
    expect(clickHandler).not.toMatch(/visibilityForAudiences|setVisibility\(/);
    expect(clickHandler).toMatch(/applied by the effect/);
  });

  test("a facilitator's own edits are never overwritten by a preset", () => {
    expect(modalSrc).toMatch(/if \(visibilityCustomised \|\| !visibilityDefaults\) return;/);
    expect(modalSrc).toMatch(/setVisibilityCustomised\(true\);/);
  });

  test('only PLAYER visibility is presetted, never facilitator', () => {
    // An experience level describes the ROOM; who is in the room says nothing
    // about which analytics the person running it should see.
    const eff = modalSrc.slice(modalSrc.indexOf('useEffect(() => {\n        if (visibilityCustomised'),
                               modalSrc.indexOf('visibilityCustomised]);'));
    expect(eff).toMatch(/player: visibilityForAudiences/);
    expect(eff).not.toMatch(/facilitator:/);
  });

  test('global defaults stay permissive so cohorts in flight are untouched', () => {
    // The preset supplies the opinion; the global default stays the fail-open.
    const analytics = fs.readFileSync(path.join(ROOT, 'backend', 'admin_analytics.py'), 'utf8');
    const start = analytics.indexOf('"player": {');
    const block = analytics.slice(start, analytics.indexOf('\n    },', start));
    const offByDefault = [...block.matchAll(/^\s*"([a-z0-9_]+)":\s*False/gm)].map((m) => m[1]);
    expect(offByDefault.sort()).toEqual(
      ['balanced_scorecard', 'competitor_intel', 'esg_leadership',
       'regret_meter', 'what_if_simulator'].sort());
  });
});

/**
 * Graceful degradation — the cockpit must still look composed when a preset
 * hides a quarter of it.
 *
 * Classroom hides 25 of 65 surfaces. Hiding a panel is easy; keeping the CHROME
 * around it honest is where this breaks. Three failure shapes, all found by
 * auditing the Classroom profile rather than assuming:
 *
 *   1. A tab offered in a bar whose content is gated → a button that opens an
 *      empty panel. (Left panel "Charts" vs kpi_dashboard.)
 *   2. A container whose every child is gated → an empty framed column.
 *      (The right rail, if a cohort permits none of its four tabs.)
 *   3. An active tab never reconciled against the visible set → the hidden
 *      panel keeps rendering underneath a tab bar that no longer offers it.
 *      In PlayerAnalytics that was a VISIBILITY LEAK, not a cosmetic one: `tab`
 *      initialised to 'benchmarking' and stayed there, so a cohort with Peer
 *      Benchmarking off still drew peer data in the body.
 */
describe('graceful degradation', () => {
  const cockpitSrc = fs.readFileSync(path.join(APP, 'components', 'ExecutiveCockpit.js'), 'utf8');
  const analyticsSrc = fs.readFileSync(path.join(APP, 'components', 'PlayerAnalytics.js'), 'utf8');

  test('a tab is never offered when its content is switched off', () => {
    expect(cockpitSrc).toMatch(/\{ id: 'charts', label: '📈 Charts', vis: 'kpi_dashboard' \}/);
    expect(cockpitSrc).toMatch(/\.filter\(tab => !tab\.vis \|\| isPlayerVisible\(tab\.vis\)\)/);
  });

  test('every tabbed surface reconciles its OPEN tab, not just its tab bar', () => {
    // right rail
    expect(cockpitSrc).toMatch(/if \(railTabsVisible\.length && !railTabsVisible\.includes\(rightPanelTab\)\)/);
    // left panel
    expect(cockpitSrc).toMatch(/leftPanelTab === 'charts' && !isPanelVisible\(playerVisibility, 'kpi_dashboard'\)/);
    // my analytics — the one that leaked
    expect(analyticsSrc).toMatch(/if \(!visibleTabs\.some\(t => t\.id === tab\)\) setTab\(visibleTabs\[0\]\.id\)/);
  });

  test('the analytics body cannot draw a hidden panel, even for one frame', () => {
    // The reconciling effect runs AFTER render, so guarding on `tab` alone
    // still paints the hidden panel once on the settings change.
    expect(analyticsSrc).toMatch(
      /const shown = \(id\) => tab === id && visibleTabs\.some\(t => t\.id === id\)/);
    for (const panel of ['benchmarking', 'impact', 'whatif']) {
      expect(analyticsSrc).toMatch(new RegExp(`shown\\('${panel}'\\) &&`));
    }
    expect(analyticsSrc).not.toMatch(/\{tab === 'benchmarking' && </);
  });

  test('containers disappear rather than render empty chrome', () => {
    expect(cockpitSrc).toMatch(/\{railTabsVisible\.length > 0 && \(/);
    expect(analyticsSrc).toMatch(/\) : !visibleTabs\.length \? \(/);
  });

  test('an emptied surface explains itself instead of showing blank chrome', () => {
    expect(analyticsSrc).toMatch(/turned personal analytics off for this cohort/);
  });

  test('the dock can never be empty whatever is hidden', () => {
    // Sound and Log out are unconditional, so the launcher always has content.
    const dock = modalSrcDock();
    expect(dock).toMatch(/label: soundEnabled \? 'Sound on' : 'Muted'/);
    expect(dock).toMatch(/label: 'Log out'/);
  });

  function modalSrcDock() {
    const page = fs.readFileSync(path.join(APP, 'page.js'), 'utf8');
    return page.slice(page.indexOf('<PlayerUtilityDock'), page.indexOf('roundChecklist='));
  }
});

/**
 * The facilitator's experience of the experience level.
 *
 * An experience level silently rewriting a quarter of a 65-switch grid is not a
 * feature, it is a surprise. Three things the form owes the person using it:
 * say what the preset does to the PLAYER cockpit (the summary line previously
 * printed the difficulty string in the slot that promised a visibility tier),
 * make the grid navigable once it is 65 switches long, and leave a way back
 * after hand-edits — applyPreset bails once visibilityCustomised is set, so
 * without a reset, customising was a one-way door.
 */
describe('cohort form — experience level feedback', () => {
  test('the preset summary reports player panels, not the difficulty string', () => {
    expect(modalSrc).toMatch(/\{presetVisibleCount\(sel\)\} of \{PLAYER_ANALYTICS\.length\} player panels/);
    expect(modalSrc).not.toMatch(/Visibility tier \(\{sel\.difficulty_tier\}\)/);
  });

  test('the count is derived from the same helper that applies the profile', () => {
    // A separately-computed number is a number that can disagree with the map.
    const fn = modalSrc.slice(modalSrc.indexOf('const presetVisibleCount'),
                              modalSrc.indexOf('const resetVisibilityToPreset'));
    expect(fn).toMatch(/visibilityForAudiences\(preset\.default_audiences\)/);
  });

  test('the 65 switches are sectioned, not one flat wall', () => {
    // The search box wrapped the call in a filter pipeline, so the call and
    // its .map now sit on separate lines — anchor with \s* rather than
    // pinning the exact old one-liner (the sectioning PROPERTY is the point).
    expect(modalSrc).toMatch(/playerVisibilityGroups\(\)\s*\.map\(\(\{ group, cards \}\)/);
    // Per-group count and a bulk control, so a section is usable at a glance.
    expect(modalSrc).toMatch(/\{on\}\/\{cards\.length\}/);
    expect(modalSrc).toMatch(/\{allOn \? 'none' : 'all'\}/);
  });

  test('the header says where the current state came from', () => {
    expect(modalSrc).toMatch(/from \{preset\.icon\} \{preset\.name\}/);
    expect(modalSrc).toMatch(/⚙ Customised/);
    expect(modalSrc).toMatch(/\{shown\}/);
  });

  test('customising is not a one-way door', () => {
    expect(modalSrc).toMatch(/const resetVisibilityToPreset = \(\) => \{/);
    expect(modalSrc).toMatch(/↺ Reset to \{preset\.name\}/);
    // Reset must clear the flag, or the effect stays disabled and the preset
    // would never apply again for the rest of the session.
    // Anchored to the NEXT function, not to the apply-effect's comment: the
    // effect moved above the isOpen guard (Rules of Hooks fix) and a stale
    // anchor made this slice empty.
    const fn = modalSrc.slice(modalSrc.indexOf('const resetVisibilityToPreset'),
                              modalSrc.indexOf('const hasVisibilityOverrides'));
    expect(fn).toMatch(/setVisibilityCustomised\(false\)/);
  });

  test('every group in the registry is reachable in the form', () => {
    const block = registrySrc.slice(
      registrySrc.indexOf('export const PLAYER_VISIBILITY_CARDS'),
      registrySrc.indexOf('export const PLAYER_VISIBILITY_KEYS'));
    const groups = new Set([...block.matchAll(/group: '([^']+)'/g)].map((m) => m[1]));
    expect(groups.size).toBeGreaterThan(1);
    // playerVisibilityGroups() derives from the same cards, so rendering it
    // covers every group by construction — assert the helper is the one used.
    expect(modalSrc).toMatch(/import \{[^}]*playerVisibilityGroups[^}]*\}/);
  });
});

/**
 * Editing an existing cohort.
 *
 * Two ways this went wrong, both silent:
 *
 *   1. The form always seeded from the GLOBAL visibility defaults. Opening Edit
 *      on a cohort with its own overrides showed settings it did not have, and
 *      saving wrote those globals back over the real ones.
 *   2. Once preset profiles existed, the apply effect saw a non-customised form
 *      and re-profiled the cohort merely because someone opened it — silently
 *      changing a RUNNING cohort's cockpit.
 *
 * Opening must show the truth and change nothing; deliberately switching the
 * experience level must still re-profile, because that is what the change means.
 */
describe('edit mode', () => {
  const panelSrc = fs.readFileSync(path.join(APP, 'components', 'AnalyticsControlPanel.js'), 'utf8');

  test('edit reads the cohort’s own visibility, not the global defaults', () => {
    expect(modalSrc).toMatch(/if \(isEditMode && editSession\?\.session_id\)/);
    expect(modalSrc).toMatch(/cohort\/\$\{editSession\.session_id\}\/analytics-visibility/);
    expect(modalSrc).toMatch(/const eff = \(await r\.json\(\)\)\.effective/);
  });

  test('the global map is still kept, since the PUT decision compares to it', () => {
    // hasVisibilityOverrides() diffs against visibilityDefaults; seeding that
    // from the cohort would make every cohort look override-free.
    expect(modalSrc).toMatch(/setVisibilityDefaults\(data\)/);
  });

  test('opening Edit does not re-profile a running cohort', () => {
    expect(modalSrc).toMatch(
      /if \(isEditMode && selectedExperienceLevel === initialExperienceLevelRef\.current\) return;/);
    expect(modalSrc).toMatch(/initialExperienceLevelRef\.current =/);
  });

  test('the control panel groups its 65 toggles too', () => {
    // It is the surface a facilitator opens MID-RUN to change one thing.
    expect(panelSrc).toMatch(/playerVisibilityGroups\(\)\.map/);
    expect(panelSrc).not.toMatch(/\{PLAYER_ANALYTICS\.map\(a => \(/);
  });
});
