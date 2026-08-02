/**
 * "Start Solo Session" is OPT-IN, controlled by a lead facilitator / super
 * admin. Default OFF (2026-08-01). Pieces that must stay wired together:
 *   1. the login screen (JoinCohortModal) reads solo_mode_enabled from the
 *      PUBLIC settings payload and shows the button ONLY when it is true,
 *      failing CLOSED (start hidden; a fetch error keeps it hidden);
 *   2. the God Mode switchboard exposes the pill (super-admin path);
 *   3. the facilitator dashboard exposes a lead-facilitator toggle wired to
 *      the dedicated /api/admin/solo-mode endpoint;
 *   4. the server refuses /solo-start when off and FAILS CLOSED by default.
 *
 * Property anchors with \s* tolerance — the stale-anchor lesson.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const modal = fs.readFileSync(path.join(APP, 'components', 'JoinCohortModal.js'), 'utf8');
const god = fs.readFileSync(path.join(APP, 'components', 'GodModeStatus.js'), 'utf8');
const facPage = fs.readFileSync(path.join(APP, 'admin', 'facilitator', 'page.js'), 'utf8');
const backend = fs.readFileSync(
  path.join(__dirname, '..', '..', 'backend', 'admin_router.py'), 'utf8');
const router = fs.readFileSync(
  path.join(__dirname, '..', '..', 'backend', 'router.py'), 'utf8');

describe('solo-session toggle (opt-in)', () => {
  test('the login screen shows the button ONLY when the flag is true', () => {
    expect(modal).toMatch(/\/api\/admin\/global-settings/);
    expect(modal).toMatch(/setSoloEnabled\(s\?\.solo_mode_enabled === true\)/);
    expect(modal).toMatch(/\{soloEnabled && \(/);
    const i = modal.indexOf('START SOLO SESSION');
    const guard = modal.lastIndexOf('{soloEnabled && (', i);
    expect(guard).toBeGreaterThan(-1);
    expect(i - guard).toBeLessThan(800);
  });

  test('the login screen fails CLOSED (default hidden, error keeps hidden)', () => {
    expect(modal).toMatch(/useState\(false\);?\s*\n?\s*useEffect/);
    expect(modal).toMatch(/\.catch\(\(\) => setSoloEnabled\(false\)\)/);
  });

  test('the backend public payload defaults the flag OFF', () => {
    expect(backend).toMatch(/"solo_mode_enabled":\s*s\.get\("solo_mode_enabled",\s*False\)/);
  });

  test('there is a dedicated solo-mode endpoint gated at lead facilitator', () => {
    // GET + PATCH both require_lead_facilitator
    expect(backend).toMatch(/@admin_router\.patch\("\/solo-mode"[\s\S]{0,400}?Depends\(require_lead_facilitator\)/);
    expect(backend).toMatch(/@admin_router\.get\("\/solo-mode"[\s\S]{0,200}?Depends\(require_lead_facilitator\)/);
  });

  test('the facilitator dashboard renders the lead-facilitator toggle', () => {
    expect(facPage).toMatch(/function SoloModeToggle\(/);
    expect(facPage).toMatch(/\/api\/admin\/solo-mode/);
    expect(facPage).toMatch(/<SoloModeToggle \/>/);
  });

  test('the god-mode switchboard pill treats missing as OFF', () => {
    const i = god.indexOf("key: 'solo_mode_enabled'");
    expect(i).toBeGreaterThan(-1);
    expect(god.slice(i, i + 1600)).toMatch(/togglePill\(t\)/);
    // default false + strict === true (no more !== false anywhere for this key)
    expect(god).toMatch(/key: 'solo_mode_enabled', label: '🎮 Solo Sessions', default: false/);
  });

  test('the server refuses /solo-start when off and fails closed', () => {
    const i = router.indexOf('async def solo_start_simulation');
    expect(i).toBeGreaterThan(-1);
    const body = router.slice(i, i + 2500);
    expect(body).toMatch(/solo_mode_enabled/);
    expect(body).toMatch(/HTTP_403_FORBIDDEN/);
    // default False in the gate read, and the except denies (fail closed)
    expect(body).toMatch(/_gms\.get\("solo_mode_enabled",\s*False\)/);
    expect(body).toMatch(/except Exception:\s*\n\s*_solo_enabled = False/);
  });
});
