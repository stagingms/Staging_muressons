/**
 * design-token-drift.test.js — UX audit #20, the tripwire.
 *
 * WHY A TRIPWIRE AND NOT A SWEEP
 *   The audit measured real drift across `components/*.module.css`: ~1,242 raw
 *   hex values, ~4,887 raw px, 1,762 font-size declarations across 108 distinct
 *   values, 363 box-shadows across 293 distinct values, and a z-index scale
 *   documented as topping out at 9000 while component CSS reaches 21500 and
 *   inline JS reaches 2147483647.
 *
 *   It ALSO said not to fix that with a blind regex pass — and this repo has
 *   the scar tissue to prove the point: `globals.css` carries a whole
 *   "Light Mode — Inline Style Color Compatibility Shim" section that exists
 *   because a previous sweep serialized colours into inline styles. CLAUDE.md
 *   states the rule directly: hue decisions happen on a real screen, never in
 *   a blind regex.
 *
 *   So the mechanism is a RATCHET, modelled on the existing drift tripwires in
 *   this repo (test_role_hierarchy_sync.py, shockwave-catalog.test.js):
 *
 *     • Today's counts are recorded as BASELINES below.
 *     • The suite fails if any count goes UP — new drift is blocked at review
 *       time, when someone can still make the hue decision on a real screen.
 *     • When you migrate a file to tokens, the count drops and you lower the
 *       baseline in the same commit. The number only ever goes one way.
 *
 *   That converts an 80k-line cleanup from a risky big-bang into a boundary
 *   that holds while the codebase is improved file by file.
 *
 * TWO SHARPER RULES, ratcheted by FILE rather than by count
 *   1. Semantic colour as a raw hex. danger/success/caution have tokens
 *      (--kpi-danger / --kpi-good / --kpi-warn) whose light-mode values were
 *      corrected for WCAG on 2026-08-02; a raw hex bypasses that fix silently
 *      and reintroduces a contrast failure on a product with a CONTRACTUAL
 *      accessibility requirement. The 18 files that predate the fix are listed
 *      explicitly; a NEW file using one of those hexes fails immediately.
 *   2. z-index above the documented top tier (--z-top: 9000). The 2147483647
 *      found in the audit is not a stacking decision, it is a surrender. The 12
 *      files already above the ceiling are listed; new ones fail.
 *
 *   Both lists may only SHRINK. A separate test fails if a listed file has been
 *   migrated but left on the list, so the boundary tightens automatically
 *   instead of quietly rotting.
 */

const fs = require('fs');
const path = require('path');

const APP_DIR = path.join(__dirname, '..', 'app');

function walk(dir, filterFn, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue;
      walk(full, filterFn, acc);
    } else if (filterFn(full)) {
      acc.push(full);
    }
  }
  return acc;
}

const cssFiles = walk(APP_DIR, (f) => f.endsWith('.module.css'));

/** Strip comments so a documented "was #059669" note never counts as drift. */
function stripComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, '');
}

function countMatches(src, re) {
  return (src.match(re) || []).length;
}

// ── Ratcheted baselines ────────────────────────────────────────────────────
// Recorded 2026-08-02. LOWER these when you migrate a file; never raise them.
// A failure here is not "the test is wrong", it is "you added drift".
const BASELINE = {
  rawHex: 1240,
  rawPx: 5034,
  boxShadow: 395,
  fontSize: 1805,
};
// Headroom absorbs formatting-only churn (e.g. the LF/CRLF renormalisation this
// repo went through) without letting real drift in. Keep it small.
const TOLERANCE = 0.02;

describe('design token drift (UX audit #20 ratchet)', () => {
  const all = cssFiles.map((f) => stripComments(fs.readFileSync(f, 'utf8'))).join('\n');

  const counts = {
    rawHex: countMatches(all, /#[0-9a-fA-F]{3,8}\b/g),
    rawPx: countMatches(all, /\b\d+(?:\.\d+)?px\b/g),
    boxShadow: countMatches(all, /box-shadow\s*:/g),
    fontSize: countMatches(all, /font-size\s*:/g),
  };

  for (const [key, baseline] of Object.entries(BASELINE)) {
    test(`${key} does not increase (baseline ${baseline})`, () => {
      const ceiling = Math.ceil(baseline * (1 + TOLERANCE));
      if (counts[key] > ceiling) {
        throw new Error(
          `Design-token drift: ${key} is now ${counts[key]}, above the ${baseline} baseline ` +
          `(ceiling ${ceiling}).\n\n` +
          `You added a raw value where a token exists. Use app/styles/tokens.css.\n` +
          `If this increase is deliberate and reviewed ON A REAL SCREEN, raise the ` +
          `baseline in this file in the SAME commit and say why in the message.`
        );
      }
      expect(counts[key]).toBeLessThanOrEqual(ceiling);
    });
  }

  test('reports current counts (informational)', () => {
    // Visible in verbose output so a migration's progress is legible.
    expect(Object.keys(counts).sort()).toEqual(['boxShadow', 'fontSize', 'rawHex', 'rawPx']);
  });
});

// ── Hard rules ─────────────────────────────────────────────────────────────

describe('semantic colour tokens are not bypassed (UX audit #11 + #20)', () => {
  // The exact light-mode values corrected for WCAG AA on 2026-08-02. A raw hex
  // silently bypasses that correction and reintroduces a contrast failure on a
  // product with a CONTRACTUAL accessibility requirement.
  //
  // These files predate the fix. The list is a RATCHET: a file may be removed
  // when it is migrated to tokens, and may never be added to. A NEW file using
  // one of these hexes fails immediately — which is the point.
  const BANNED_SEMANTIC_HEX = {
    '#059669': {
      why: '--kpi-good / --gauge-green (old value: 3.44:1 on #f1f5f9, FAILS AA)',
      // 2026-08-02 migration: DebriefReport, MasterVariableEditor,
      // PlayerAnalytics, ResourceSidebar and SimulationReference came off —
      // every occurrence in them was `color:` on text. The six left each keep
      // ONE occurrence, and it is a gradient stop paired with the token
      // (`linear-gradient(135deg, var(--kpi-good), #059669)`) — decorative
      // depth on a filled button, not a text/background contrast pair.
      legacy: [
        'components/BoardroomShowdown.module.css',
        'components/DecisionModal.module.css',
        'components/ExecutiveCockpit.module.css',
        'components/FacilitatorManager.module.css',
        'components/RoundPacingControl.module.css',
        'components/SustainabilityBalancedScorecard.module.css',
      ],
    },
    '#d97706': {
      why: '--kpi-warn / --gauge-yellow / --accent-gold (old: 2.91:1, FAILS AA)',
      // 2026-08-02 migration: LeaderboardMatrix (.bronze -> --medal-bronze,
      // a NEW token: mapping bronze onto --kpi-warn/--accent-gold would have
      // made 3rd place identical to 1st) and ResourceSidebar came off. The
      // four left keep gradient stops only.
      legacy: [
        'components/CrisisAlerts.module.css',
        'components/CrisisTriggerConfig.module.css',
        'components/PedagogicalScaffolding.module.css',
        'components/RoundPacingControl.module.css',
      ],
    },
    '#0891b2': {
      why: '--accent-cyan (old: 3.36:1, FAILS AA)',
      legacy: ['components/PedagogicalScaffolding.module.css'],
    },
  };

  for (const [hex, { why, legacy }] of Object.entries(BANNED_SEMANTIC_HEX)) {
    test(`no NEW file uses ${hex}`, () => {
      const offenders = cssFiles
        .filter((f) => stripComments(fs.readFileSync(f, 'utf8')).toLowerCase().includes(hex))
        .map((f) => path.relative(APP_DIR, f).split(path.sep).join('/'))
        .filter((rel) => !legacy.includes(rel));
      if (offenders.length) {
        throw new Error(
          `${hex} appeared in a file not on the legacy list:\n  ${offenders.join('\n  ')}\n\n` +
          `That is ${why}. Use the token — its light-mode value was corrected for ` +
          `contrast, and a raw hex bypasses the fix silently.`
        );
      }
      expect(offenders).toEqual([]);
    });
  }
});

describe('z-index stays inside the documented scale (UX audit #20)', () => {
  // globals.css documents a 9-tier scale topping out at --z-top: 9000.
  const Z_CEILING = 9000;

  // EMPTY as of 2026-08-02: all twelve files were migrated to the scale.
  // globals.css grew an "above-takeover" band (--z-modal-under-gate 9100 …
  // --z-portal 9700) because the scale genuinely had no tier above a
  // full-screen takeover, which is why those files had invented 9500…21500.
  // Relative order was preserved exactly; nothing was collapsed onto a tier it
  // has to out-stack (the drawer/scrim +1 adjacency survives as 9500/9501).
  //
  // Still open, and deliberately NOT hidden by this list: inline JS z-indexes
  // (ConfirmModal 25000, ShockwaveOverlay 99999, plus 9998/9999/12000/20000
  // literals in component JS) sit above the whole CSS band. This rule only
  // governs *.module.css. Do not re-add files here to work around that.
  const LEGACY_Z_FILES = [];

  test('no NEW file exceeds --z-top (9000)', () => {
    const offenders = [];
    for (const f of cssFiles) {
      const rel = path.relative(APP_DIR, f).split(path.sep).join('/');
      if (LEGACY_Z_FILES.includes(rel)) continue;
      const src = stripComments(fs.readFileSync(f, 'utf8'));
      const re = /z-index\s*:\s*(\d+)/g;
      let m;
      while ((m = re.exec(src)) !== null) {
        const v = parseInt(m[1], 10);
        if (v > Z_CEILING) offenders.push(`${rel}: z-index ${v}`);
      }
    }
    if (offenders.length) {
      throw new Error(
        `z-index above the documented ceiling (${Z_CEILING}) in a non-legacy file:\n  ` +
        `${offenders.join('\n  ')}\n\nPick a tier from the scale in globals.css ` +
        `(--z-base … --z-top). A number larger than everything else is not a ` +
        `stacking decision.`
      );
    }
    expect(offenders).toEqual([]);
  });

  test('the legacy z-index list only ever shrinks', () => {
    // If a listed file no longer exceeds the ceiling, it has been migrated —
    // remove it from LEGACY_Z_FILES so the boundary tightens permanently.
    const stillOffending = LEGACY_Z_FILES.filter((rel) => {
      const full = path.join(APP_DIR, ...rel.split('/'));
      if (!fs.existsSync(full)) return false;
      const src = stripComments(fs.readFileSync(full, 'utf8'));
      const re = /z-index\s*:\s*(\d+)/g;
      let m;
      while ((m = re.exec(src)) !== null) if (parseInt(m[1], 10) > Z_CEILING) return true;
      return false;
    });
    const migrated = LEGACY_Z_FILES.filter((r) => !stillOffending.includes(r));
    if (migrated.length) {
      throw new Error(
        `These files no longer exceed the z-index ceiling — remove them from ` +
        `LEGACY_Z_FILES so the ratchet tightens:\n  ${migrated.join('\n  ')}`
      );
    }
    expect(migrated).toEqual([]);
  });
});
