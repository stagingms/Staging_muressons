/**
 * The always-visible Logout control must never paint over a screen's own
 * top-right content.
 *
 * REPORTED: on the Year-5 reveal the Logout button sat on top of the
 * "BANKRUPT · Grade F" pill in the status bar, clipping the grade the whole
 * screen exists to deliver.
 *
 * CAUSE: the button is `position: fixed` (top 12 / right 16) so it stays
 * reachable while the screen scrolls — which means it participates in NO host
 * layout. The status bar laid its pill flush right, straight underneath.
 *
 * FIX: one shared geometry module (logoutChrome.js). Hosts with right-edge
 * content reserve LOGOUT_GUTTER; hosts whose header is centred need nothing.
 * The pins below exist because the two numbers — the button's footprint and
 * the space reserved for it — are only correct while they agree.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const read = (...p) => fs.readFileSync(path.join(APP, ...p), 'utf8');

const {
  LOGOUT_TOP,
  LOGOUT_RIGHT,
  LOGOUT_MIN_WIDTH,
  LOGOUT_CLEARANCE,
  LOGOUT_GUTTER,
  logoutAnchorStyle,
} = require('../app/components/logoutChrome');

/** Every screen that pins a Logout control to the viewport corner. */
const HOSTS = ['ArchetypeReveal', 'BoardroomShowdown', 'CrisisAlerts', 'RoundBriefing'];

describe('logout geometry', () => {
  test('the gutter covers the button footprint with clearance to spare', () => {
    expect(LOGOUT_GUTTER).toBe(LOGOUT_RIGHT + LOGOUT_MIN_WIDTH + LOGOUT_CLEARANCE);
    expect(LOGOUT_GUTTER).toBeGreaterThan(LOGOUT_RIGHT + LOGOUT_MIN_WIDTH);
  });

  test('the button is wide enough for its widest label', () => {
    // Measured in-browser at the real font (700 11.52px DM Sans, padding
    // 6px 14px): "🚪 Logout" = 86px, "⚠️ Confirm Logout?" = 140px. The button
    // must not grow past the reserved space when it flips to confirm.
    expect(LOGOUT_MIN_WIDTH).toBeGreaterThanOrEqual(140);
  });

  test('the anchor pins position, size and nowrap', () => {
    const s = logoutAnchorStyle(9000);
    expect(s).toMatchObject({
      position: 'fixed',
      top: LOGOUT_TOP,
      right: LOGOUT_RIGHT,
      zIndex: 9000,
      minWidth: LOGOUT_MIN_WIDTH,
      whiteSpace: 'nowrap',   // a wrapped label would grow taller, not wider
    });
  });
});

describe('every logout host uses the shared anchor', () => {
  test.each(HOSTS)('%s does not hardcode its own corner offsets', (host) => {
    const src = read('components', `${host}.js`);
    expect(src).toMatch(/import \{[^}]*logoutAnchorStyle[^}]*\} from '\.\/logoutChrome'/);
    expect(src).toMatch(/\.\.\.logoutAnchorStyle\(\d+\)/);
    // The literal that caused the overlap — four copies of it, none reserving
    // any space. If it comes back, the gutter silently stops applying.
    expect(src).not.toMatch(/position: 'fixed', top: 12, right: 16/);
  });

  test.each(HOSTS)('%s keeps display:flex after the spread, not before', (host) => {
    // The anchor carries justifyContent; a `display` set BEFORE the spread
    // would still work, but a `justifyContent` set after would silently win.
    const src = read('components', `${host}.js`);
    const i = src.indexOf('...logoutAnchorStyle(');
    const after = src.slice(i, i + 220);
    expect(after).toMatch(/display: 'flex'/);
    expect(after).not.toMatch(/justifyContent:/);
  });
});

describe('the reveal status bar reserves room for the button', () => {
  const reveal = read('components', 'ArchetypeReveal.js');
  const css = read('components', 'ArchetypeReveal.module.css');

  test('the status bar applies the shared gutter', () => {
    expect(reveal).toMatch(/import \{[^}]*LOGOUT_GUTTER[^}]*\} from '\.\/logoutChrome'/);
    expect(reveal).toMatch(/className=\{styles\.statusBar\}\s*\n\s*style=\{\{ paddingRight: LOGOUT_GUTTER \}\}/);
  });

  test('the grade pill is still the right-most laid-out element', () => {
    // If the pill stopped being flush-right the gutter would be pointless —
    // but so would removing it, so pin the arrangement the fix assumes.
    expect(reveal).toMatch(/className=\{styles\.statusRight\}/);
    expect(reveal).toMatch(/className=\{styles\.statusPill\}/);
    expect(css).toMatch(/\.statusLabel \{[^}]*flex: 1;/);
  });

  test('the gutter is inline so the mobile padding rule cannot drop it', () => {
    // .statusBar's <=640px rule resets `padding`, which would wipe a
    // padding-right declared in the module. Inline style survives it.
    expect(css).toMatch(/@media[^{]*\{[\s\S]*?\.statusBar \{\s*padding: 0\.6rem 1rem;/);
    expect(css).not.toMatch(/\.statusBar \{[^}]*padding-right/);
  });
});
