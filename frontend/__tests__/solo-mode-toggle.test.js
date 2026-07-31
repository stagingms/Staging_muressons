/**
 * "Start Solo Session" is a facilitator-controlled switch.
 *
 * Three pieces must stay wired together or the toggle silently dies:
 *   1. the login screen (JoinCohortModal) reads solo_mode_enabled from the
 *      PUBLIC global-settings payload and gates the button on it;
 *   2. the God Mode switchboard exposes the pill through the same togglePill
 *      mechanics as every other platform switch (PATCH global-settings);
 *   3. the button's default is VISIBLE — a failed settings fetch must not
 *      strand self-paced learners (the server refuses /solo-start when the
 *      switch is really off, so fail-open here is safe).
 *
 * Property anchors with \s* tolerance — the stale-anchor lesson from the
 * audience-profiles / player-visibility repairs.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const modal = fs.readFileSync(path.join(APP, 'components', 'JoinCohortModal.js'), 'utf8');
const god = fs.readFileSync(path.join(APP, 'components', 'GodModeStatus.js'), 'utf8');
const backend = fs.readFileSync(
  path.join(__dirname, '..', '..', 'backend', 'admin_router.js').replace('admin_router.js', 'admin_router.py'), 'utf8');
const router = fs.readFileSync(
  path.join(__dirname, '..', '..', 'backend', 'router.py'), 'utf8');

describe('solo-session toggle', () => {
  test('the login screen fetches the flag from the public settings payload', () => {
    expect(modal).toMatch(/\/api\/admin\/global-settings/);
    expect(modal).toMatch(/solo_mode_enabled === false[\s\S]{0,40}?setSoloEnabled\(false\)/);
  });

  test('the button renders only when enabled', () => {
    expect(modal).toMatch(/\{soloEnabled && \(/);
    const i = modal.indexOf('START SOLO SESSION');
    expect(i).toBeGreaterThan(-1);
    const guard = modal.lastIndexOf('{soloEnabled && (', i);
    expect(guard).toBeGreaterThan(-1);
    expect(i - guard).toBeLessThan(800);
  });

  test('the default is visible (fail-open), matching the server default', () => {
    expect(modal).toMatch(/useState\(true\);?\s*\n?\s*useEffect/);
    // and the backend's public payload defaults the same way
    expect(backend).toMatch(/"solo_mode_enabled":\s*s\.get\("solo_mode_enabled",\s*True\)/);
  });

  test('the switchboard exposes the pill through togglePill', () => {
    const i = god.indexOf("key: 'solo_mode_enabled'");
    expect(i).toBeGreaterThan(-1);
    // the pill sits inside a block that calls togglePill like every sibling
    expect(god.slice(i, i + 1600)).toMatch(/togglePill\(t\)/);
  });

  test('PATCH accepts the key (it is a declared switchboard field)', () => {
    expect(backend).toMatch(/solo_mode_enabled:\s*bool \| None = None/);
  });

  test('the server refuses /solo-start when off — hiding is not the defence', () => {
    const i = router.indexOf('async def solo_start_simulation');
    expect(i).toBeGreaterThan(-1);
    const body = router.slice(i, i + 2500);
    expect(body).toMatch(/solo_mode_enabled/);
    expect(body).toMatch(/HTTP_403_FORBIDDEN/);
  });
});
