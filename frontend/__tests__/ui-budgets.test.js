/**
 * ui-budgets.test.js — Phase 2 guardrails.
 *
 * WHY THIS FILE EXISTS
 *   The player cockpit did not arrive dense. It accreted: six feature waves,
 *   each shipping one more always-visible panel, one more accent tint, one more
 *   0.6rem label, one more perpetual pulse. Every individual addition was
 *   defensible. The sum is ~46 elements on a screen a driver looks at for
 *   30–60 minutes. CLAUDE.md's V-D slotting rule already forbids this in prose;
 *   this file is the part that fails a build.
 *
 * WHAT IT IS
 *   A DEBT LEDGER, not a standard. Every budget below is frozen at what the
 *   codebase actually carries today, not at what it should carry. The tests
 *   fail in BOTH directions:
 *
 *     - grows  → you added debt. Fix it, or argue for a raised baseline in
 *                review, where someone can say no.
 *     - shrinks → you paid debt down. Lower the baseline in this file so the
 *                new floor is the one that holds. This is the ratchet; without
 *                it the number creeps back the week after a cleanup phase.
 *
 *   Both directions matter. A one-way tripwire is a suggestion.
 *
 * WHAT IT DELIBERATELY DOES NOT DO
 *   It does not measure contrast, spacing rhythm, or hierarchy — a browser is
 *   the only place those can be judged, and theme-leak-tripwires.test.js
 *   already explains why. These are source-shape counts: cheap, exact, and
 *   they catch the specific regressions that keep happening here.
 *
 * NOTE ON stylelint
 *   .stylelintrc.json carries a spacing/hex rule set that has never run —
 *   stylelint is not installed and its own header says so ("Requires: npm i -D
 *   stylelint"). The spacing budget below covers the same ground from inside
 *   the suite that actually runs, so the rule is enforced rather than aspired
 *   to. If stylelint is ever installed, that config can take over and this
 *   budget can be deleted.
 */

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const exists = (p) => fs.existsSync(path.join(root, p));

/* Every surface a player can see. Adding a player-facing file here is part of
   shipping it — an unlisted file is unguarded. */
const PLAYER_FILES = [
  'app/components/ExecutiveCockpit.js', 'app/components/ExecutiveCockpit.module.css',
  'app/components/FocusOverlay.js', 'app/components/FocusOverlay.module.css',
  'app/components/RoundBriefing.js', 'app/components/RoundBriefing.module.css',
  'app/components/DoubleMaterialityMatrix.js', 'app/components/DoubleMaterialityMatrix.module.css',
  'app/components/InvestmentMatrix.js', 'app/components/InvestmentMatrix.module.css',
  'app/components/FrontPageReveal.js',
  'app/components/GameOverSummary.js', 'app/components/GameOverSummary.module.css',
  'app/components/ArchetypeReveal.js',
  'app/components/JoinCohortModal.js', 'app/components/JoinCohortModal.module.css',
  'app/components/OnboardingWalkthrough.js', 'app/components/CrisisAlerts.js',
  'app/components/RoundChecklist.js', 'app/components/DecisionTile.js',
  'app/components/CountdownTimer.js', 'app/components/KPIDashboard.js',
  'app/components/MarketRealityFeed.js', 'app/components/BenchmarksPanel.js',
  'app/components/CompetitorIntelligence.js',
  'app/components/StockPerformanceChart.js', 'app/components/StockPerformanceChart.module.css',
  'app/components/DecisionModal.module.css',
  'app/page.js', 'app/page.module.css',
].filter(exists);

const toPx = (raw) => {
  /* Strip `!important` before parsing. Without this the ratchet was blind to
     any declaration that carried it — `font-size: 0.62rem !important` failed
     /^[\d.]+rem$/ and returned null, so it counted as "not a literal" and was
     silently exempt from the type floor. One such declaration existed in the
     tree; it is now on the scale. */
  const v = String(raw).trim().replace(/\s*!important$/i, '');
  if (/^[\d.]+px$/.test(v)) return parseFloat(v);
  if (/^[\d.]+rem$/.test(v)) return parseFloat(v) * 16;   // 16px root
  return null;                                            // clamp(), var(), % — not a literal
};

const sum = (o) => Object.values(o).reduce((a, b) => a + b, 0);

/* Report both directions with a message that says what to do about it. */
function ratchet(label, actual, baseline, howToFix) {
  if (actual > baseline) {
    throw new Error(
      `${label}: ${actual}, baseline ${baseline}. You added ${actual - baseline}. ` +
      `${howToFix} If the addition is genuinely right, raise the baseline in ` +
      `__tests__/ui-budgets.test.js in the same commit, so a human sees it in review.`
    );
  }
  if (actual < baseline) {
    throw new Error(
      `${label}: ${actual}, baseline ${baseline}. You paid down ${baseline - actual} — ` +
      `thank you. Now lower the baseline in __tests__/ui-budgets.test.js to ${actual} ` +
      `so the new floor is the one that holds.`
    );
  }
}

// ── 2.1 TYPE FLOOR ──────────────────────────────────────────────────────────
// tokens.css sets --type-caption at 12px and calls it the smallest step.
// globals.css runs a competing --fs-* clamp scale whose floor is 11.52px, and
// the player surfaces carry literals down to 7.68px. In a 30–60 minute round
// these are sustained-reading conditions, not glance conditions.

function subTwelve(file) {
  const s = read(file);
  const hits = [];
  for (const m of s.matchAll(/font-size:\s*([^;{}]+);/g)) {
    const px = toPx(m[1]); if (px !== null && px < 12) hits.push(m[1].trim());
  }
  for (const m of s.matchAll(/fontSize:\s*['"]([^'"]+)['"]/g)) {
    const px = toPx(m[1]); if (px !== null && px < 12) hits.push(m[1]);
  }
  return hits;
}

const TYPE_FLOOR_DEBT = {
  'app/components/ExecutiveCockpit.js': 103,   // SEAM-16 (Wave 3): the Cost of Capital label moved to the 12px floor; retired resultsOverlay
  'app/components/ExecutiveCockpit.module.css': 0,
  'app/components/FocusOverlay.module.css': 0,
  'app/components/RoundBriefing.js': 12,
  'app/components/RoundBriefing.module.css': 2,
  'app/components/DoubleMaterialityMatrix.js': 0,
  'app/components/DoubleMaterialityMatrix.module.css': 0,
  'app/components/InvestmentMatrix.js': 0,
  'app/components/InvestmentMatrix.module.css': 0,
  'app/components/FrontPageReveal.js': 7,
  'app/components/GameOverSummary.js': 38,
  'app/components/GameOverSummary.module.css': 3,
  'app/components/ArchetypeReveal.js': 1,
  'app/components/JoinCohortModal.js': 0,
  'app/components/JoinCohortModal.module.css': 0,
  'app/components/OnboardingWalkthrough.js': 0,
  'app/components/CrisisAlerts.js': 0,
  'app/components/RoundChecklist.js': 1,
  'app/components/DecisionTile.js': 0,
  'app/components/CountdownTimer.js': 0,
  'app/components/KPIDashboard.js': 8,
  'app/components/MarketRealityFeed.js': 10,
  'app/components/BenchmarksPanel.js': 7,
  'app/components/CompetitorIntelligence.js': 5,
  'app/components/StockPerformanceChart.module.css': 4,
  'app/components/DecisionModal.module.css': 5,
  'app/page.js': 7,
  'app/page.module.css': 2,
};

describe('type floor (12px)', () => {
  test('no file grows its sub-12px count', () => {
    for (const f of PLAYER_FILES) {
      const n = subTwelve(f).length;
      const base = TYPE_FLOOR_DEBT[f] || 0;
      expect(`${f}: ${n}`).toBe(`${f}: ${base}`);
    }
  });

  test('the whole-tree total is the number that has to fall', () => {
    const total = PLAYER_FILES.reduce((a, f) => a + subTwelve(f).length, 0);
    ratchet('sub-12px font sizes across the player tree', total, sum(TYPE_FLOOR_DEBT),
      'Phase 6 unifies the type scale and takes this to zero.');
  });

  test('a file with no debt today may never acquire any', () => {
    const clean = PLAYER_FILES.filter((f) => !TYPE_FLOOR_DEBT[f]);
    for (const f of clean) expect({ [f]: subTwelve(f) }).toEqual({ [f]: [] });
  });
});

// ── 2.2 SLOT BUDGET ─────────────────────────────────────────────────────────
// CLAUDE.md V-D: "A feature that ships as a new always-visible panel is a
// review defect, not a style choice." Two counts, because a panel can arrive
// either as a new direct child of a column or as a component mounted deeper in
// one. Both are the same defect.

function directChildren(marker) {
  const s = read('app/components/ExecutiveCockpit.js');
  const at = s.indexOf(`styles.${marker}`);
  if (at === -1) throw new Error(`column marker styles.${marker} not found`);
  // walk forward from the opening tag, counting children at depth 1
  let i = s.indexOf('>', at) + 1, depth = 0, n = 0;
  while (i < s.length) {
    if (s.startsWith('</', i) && depth === 0) break;
    if (s[i] === '<' && /[A-Za-z]/.test(s[i + 1])) { if (depth === 0) n++; depth++; }
    else if (s.startsWith('</', i)) depth--;
    else if (s.startsWith('/>', i)) depth--;
    i++;
  }
  return n;
}

/* 57 -> 58: <Dialog>. Raised deliberately, and this is the case for it.
   The slot budget exists to stop a new always-visible PANEL arriving without
   an occupant being displaced. Dialog is not a panel and occupies no slot: it
   is the accessibility wrapper that three hand-rolled overlays in this file
   (keyboard help, expanded message, pre-commit prediction) now go through
   instead of each rolling their own scrim + stopPropagation pair. The number
   of things a player can see is unchanged; the number of DISTINCT component
   identifiers went up by one because three copies of the same pattern were
   replaced by one import.

   Net effect on this file: seven non-button click targets removed, three
   modals gained a focus trap, focus restore and topmost-only Escape.

   page.js 37 -> 38: <ChangePasswordModal> (audit 2026-09-04 F-01, P0). Not a
   panel either: an architectural early return rendered INSTEAD of the whole
   tree while a fresh participant is still on the issued password — the
   server refuses every write until then, and the only other renderer
   (JoinCohortModal) is unmounted once a session exists. Nothing is added to
   the board a playing participant sees. */
const COMPONENT_MOUNTS = { 'app/components/ExecutiveCockpit.js': 41, 'app/page.js': 38 };

describe('slot budget', () => {
  test('no new component mounts in the player tree', () => {
    for (const [f, base] of Object.entries(COMPONENT_MOUNTS)) {
      const mounts = new Set([...read(f).matchAll(/<([A-Z][A-Za-z0-9_]*)[\s/>]/g)].map((m) => m[1]));
      ratchet(`distinct component mounts in ${f}`, mounts.size, base,
        'A new player-facing component needs a slot, and a slot has an occupant already.');
    }
  });

  test('the visibility registry does not grow', () => {
    const reg = read('app/config/playerVisibilityRegistry.js');
    const keys = [...reg.matchAll(/\{\s*key:\s*'([a-z0-9_]+)'/g)].length;
    ratchet('player visibility registry entries', keys, 64,
      'Every entry is a surface a player can be shown.');
  });
});

// ── 2.3 MOTION BUDGET ───────────────────────────────────────────────────────
// A 2-second pulse repeats 900–1,800 times in one round. The two survivors in
// the cockpit stylesheet are a skeleton shimmer and a border rotate; both stop
// when the thing they describe stops.

function loops(file) {
  const s = read(file);
  return (s.match(/animation[^;{}\n]*\binfinite\b/g) || []).length
       + (s.match(/repeat:\s*Infinity/g) || []).length;
}

const MOTION_DEBT = {
  'app/components/ExecutiveCockpit.js': 4,
  'app/components/ExecutiveCockpit.module.css': 2,
  'app/components/FocusOverlay.module.css': 1,
  'app/components/RoundBriefing.module.css': 1,
  'app/components/DoubleMaterialityMatrix.module.css': 3,
  'app/components/InvestmentMatrix.module.css': 4,
  'app/components/ArchetypeReveal.js': 1,
  'app/components/JoinCohortModal.module.css': 1,
  'app/components/CompetitorIntelligence.js': 1,
  'app/page.js': 1,
  'app/page.module.css': 2,
};

describe('motion budget', () => {
  test('no file grows its looping-animation count', () => {
    for (const f of PLAYER_FILES) {
      const n = loops(f);
      expect(`${f}: ${n}`).toBe(`${f}: ${MOTION_DEBT[f] || 0}`);
    }
  });

  test('the tree total is the number that has to fall', () => {
    const total = PLAYER_FILES.reduce((a, f) => a + loops(f), 0);
    ratchet('perpetual animations across the player tree', total, sum(MOTION_DEBT),
      'Only two loops earn their place: an in-flight skeleton, and the countdown inside its final minute.');
  });
});

// ── 2.4 SPACING SCALE ───────────────────────────────────────────────────────
// The most-used spacing value in the cockpit stylesheet is 6px — a value on no
// 4px or 8px scale. It is not a scale, it is a habit of typing 6px.

/* PHASE 6.2 adds 2 — the hairline step. tokens.css records the reasoning; the
   short version is that 53 declarations sat below the old 4px floor doing
   optical work beside 1px borders, and a scale with no step for that forces
   either a visible 4px jump or the deletion of the adjustment. 2 is the
   measured centre of that cluster. Note this set still has no 6 and no 10:
   those were the two biggest off-scale populations (55 and 56) and they went
   UP to 8 and 12 rather than being legitimised. */
const SCALE = new Set([0, 2, 4, 8, 12, 16, 24, 32, 48, 64]);

function offScale(file) {
  if (!file.endsWith('.css')) return 0;
  const s = read(file);
  let n = 0;
  const re = /(?:^|[\s;{])(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left))?:\s*([^;{}]+);/g;
  for (const m of s.matchAll(re)) {
    for (const v of m[1].split(/\s+/)) {
      const px = toPx(v);
      if (px !== null && !SCALE.has(px)) n++;
    }
  }
  return n;
}

const SPACING_DEBT = {
  'app/components/ExecutiveCockpit.module.css': 0,
  'app/components/FocusOverlay.module.css': 0,
  'app/components/RoundBriefing.module.css': 0,
  'app/components/DoubleMaterialityMatrix.module.css': 0,
  'app/components/InvestmentMatrix.module.css': 0,
  'app/components/GameOverSummary.module.css': 0,
  'app/components/JoinCohortModal.module.css': 0,
  'app/components/StockPerformanceChart.module.css': 0,
  'app/components/DecisionModal.module.css': 0,
  'app/page.module.css': 0,
};

describe('spacing scale', () => {
  test('no stylesheet grows its off-scale spacing count', () => {
    for (const f of PLAYER_FILES.filter((f) => f.endsWith('.css'))) {
      const n = offScale(f);
      expect(`${f}: ${n}`).toBe(`${f}: ${SPACING_DEBT[f] || 0}`);
    }
  });

  test('the tree total is the number that has to fall', () => {
    const total = PLAYER_FILES.reduce((a, f) => a + offScale(f), 0);
    ratchet('off-scale spacing values across the player stylesheets', total, sum(SPACING_DEBT),
      'Phase 6 adopts the nine-step scale and takes this to zero.');
  });
});

// ── 2.5 SEMANTIC HUE LOCK ───────────────────────────────────────────────────
// This is a sustainability simulation: green means "good ESG outcome" to a
// player more strongly than in almost any other product. tokens.css already
// says these hues are "reserved for meaning (danger/success/caution), never
// decoration". Today they are also business-unit brand colours
// (InvestmentMatrix BU_META), ESRS topic colours (DoubleMaterialityMatrix) and
// player identity themes (ArchetypeReveal) — so when an actual state needs
// red, the hue is already spent and gets hand-mixed a sixth time.

const SEMANTIC_HEX = new RegExp(
  '#(?:' + [
    '10b981', '22c55e', '4ade80', '34d399', '059669', '16a34a', '86efac', '6ee7b7', 'a7f3d0', '0a7d3c', '15803d', '047857',
    'ef4444', 'f87171', 'dc2626', 'b91c1c', 'fca5a5', 'b42318', '450a0a',
    'f59e0b', 'fbbf24', 'fcd34d', 'd97706', 'a16207', 'b45309', '92400e',
  ].join('|') + ')\\b', 'gi');

const HUE_DEBT = {
  'app/components/ExecutiveCockpit.js': 27,
  'app/components/FrontPageReveal.js': 21,
  'app/components/ArchetypeReveal.js': 15,
  'app/components/KPIDashboard.js': 11,
  'app/components/GameOverSummary.js': 6,
  'app/components/ExecutiveCockpit.module.css': 5,
  'app/components/RoundBriefing.js': 5,
  'app/page.js': 5,
  'app/components/DoubleMaterialityMatrix.module.css': 4,
  'app/components/InvestmentMatrix.module.css': 3,
  'app/components/DoubleMaterialityMatrix.js': 2,
  'app/components/InvestmentMatrix.js': 0,
  'app/components/GameOverSummary.module.css': 1,
  'app/components/JoinCohortModal.module.css': 1,
  'app/components/CrisisAlerts.js': 1,
  'app/components/CompetitorIntelligence.js': 1,
};

const rawHues = (f) => (read(f).match(SEMANTIC_HEX) || []).length;

describe('semantic hue lock', () => {
  test('no file grows its raw green/red/amber count', () => {
    for (const f of PLAYER_FILES) {
      const n = rawHues(f);
      expect(`${f}: ${n}`).toBe(`${f}: ${HUE_DEBT[f] || 0}`);
    }
  });

  test('the tree total is the number that has to fall', () => {
    const total = PLAYER_FILES.reduce((a, f) => a + rawHues(f), 0);
    ratchet('raw semantic hex literals across the player tree', total, sum(HUE_DEBT),
      'Use --positive / --caution / --danger and their -soft companions.');
  });

  test('tokens.css remains the only place these hues are declared', () => {
    const t = read('app/styles/tokens.css');
    for (const name of ['--positive:', '--caution:', '--danger:']) expect(t).toContain(name);
  });
});

/* ── 2.6 THE TYPE FLOOR, EVERYWHERE ELSE ────────────────────────────────────
   Phase 6.1 covered the player surface incrementally, file by file, because
   every size change there is something a room of people looks at for an hour.
   The admin surface got one mechanical pass instead: 1,490 declarations across
   172 files, all of them below 12px, all of them now var(--type-caption).

   585 were CSS, 905 were inline `fontSize` in JSX — which is why a stylelint
   rule could never have found them, and why the count was invisible until
   something walked both.

   This budget is ZERO and is meant to stay zero. The player ledger above
   carries real remaining debt and names it per file; there is nothing left to
   carry out here, so the assertion is the simple kind: no file outside the
   player list may contain a sub-12px type literal at all.

   If a genuine exception ever arrives — a dense projector table, a print
   stylesheet — it goes in an allowlist beside this comment with its reason,
   the same way the pointer-only click targets are handled. Not by raising a
   number. */
describe('type floor outside the player surface', () => {
  const walk = (dir, out = []) => {
    for (const e of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const rel = `${dir}/${e.name}`;
      if (e.isDirectory()) { if (e.name !== 'node_modules') walk(rel, out); continue; }
      if (/\.(js|css)$/.test(e.name)) out.push(rel);
    }
    return out;
  };

  const offenders = () => {
    const player = new Set(PLAYER_FILES);
    const hits = [];
    for (const f of walk('app')) {
      if (player.has(f)) continue;
      const s = read(f);
      for (const m of s.matchAll(/font-size:\s*([^;{}]+);/g)) {
        const px = toPx(m[1]);
        if (px !== null && px < 12) hits.push(`${f}  font-size: ${m[1].trim()}`);
      }
      for (const m of s.matchAll(/fontSize:\s*['"]([^'"]+)['"]/g)) {
        const px = toPx(m[1]);
        if (px !== null && px < 12) hits.push(`${f}  fontSize: ${m[1]}`);
      }
    }
    return hits;
  };

  test('no admin or shared file carries a sub-12px type literal', () => {
    const hits = offenders();
    // Show the first few rather than a bare count — a failure here should
    // point at the line, not send someone hunting.
    expect(hits.slice(0, 8)).toEqual([]);
    expect(hits.length).toBe(0);
  });
});

/* ── 2.7 NO DEAD HEX FALLBACKS ──────────────────────────────────────────────
   `var(--success, #4ade80)` was caught by the hue lock during Phase D and is
   the defect this section generalises. A colour fallback inside a var() is
   invisible to a reader — it looks tokenised — and it is exactly what a
   search-and-replace palette migration leaves behind: the token gets renamed,
   the fallback does not, and the two drift silently until a theme change
   reveals that half the tree is still painting from the fallback.

   560 such sites existed. All of them named a token defined at :root or
   [data-theme] scope, which means the fallback could never fire and was pure
   decoration. They are gone.

   THE TEST IS SCOPE-AWARE, and it has to be. A fallback is only dead if the
   token resolves WHEREVER the var() is used. A component-scoped custom
   property (--csrd-border, set on a wrapper) or an inline one (--bu-accent,
   set per element in JSX) is a legitimate fallback: outside that scope there
   really is nothing to resolve to. So this only fails on tokens defined
   globally. */
describe('no dead colour fallbacks', () => {
  const COLOUR = /^(#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\()/;
  const VAR = /var\(\s*(--[a-zA-Z0-9-]+)\s*,\s*([^()]*(?:\([^()]*\))?[^()]*?)\s*\)/g;

  /* Tokens defined at :root / html / body / [data-theme]. Brace-depth scan
     rather than a regex over blocks, because tokens.css and globals.css both
     nest inside @media and a naive block regex silently misses those. */
  const globalTokens = () => {
    const out = new Set();
    for (const f of ['app/styles/tokens.css', 'app/globals.css']) {
      const s = read(f).replace(/\/\*[\s\S]*?\*\//g, '');
      const stack = []; const chunks = [];
      let i = 0, selStart = 0;
      while (i < s.length) {
        const ch = s[i];
        if (ch === '{') { stack.push(s.slice(selStart, i).trim().split(/[\n}]/).pop().trim()); selStart = i + 1; }
        else if (ch === '}') { chunks.push([stack[stack.length - 1] || '', s.slice(selStart, i)]); stack.pop(); selStart = i + 1; }
        i++;
      }
      for (const [sel, body] of chunks) {
        if (!/(^|,)\s*(:root|html|body)\b/.test(sel) && !/\[data-theme/.test(sel)) continue;
        for (const d of body.matchAll(/(--[a-zA-Z0-9-]+)\s*:/g)) out.add(d[1]);
      }
    }
    return out;
  };

  const walk = (dir, out = []) => {
    for (const e of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const rel = `${dir}/${e.name}`;
      if (e.isDirectory()) { if (e.name !== 'node_modules') walk(rel, out); continue; }
      if (/\.(js|css)$/.test(e.name)) out.push(rel);
    }
    return out;
  };

  test('a var() whose token is globally defined carries no colour fallback', () => {
    const G = globalTokens();
    const dead = [];
    for (const f of walk('app')) {
      for (const m of read(f).matchAll(VAR)) {
        if (!COLOUR.test(m[2].trim())) continue;
        if (G.has(m[1])) dead.push(`${f}  var(${m[1]}, ${m[2].trim()})`);
      }
    }
    expect(dead.slice(0, 8)).toEqual([]);
    expect(dead.length).toBe(0);
  });

  test('the global-token scan actually finds tokens, so the test cannot pass vacuously', () => {
    // If the brace scan broke, every fallback would look component-scoped and
    // the assertion above would pass while enforcing nothing.
    const G = globalTokens();
    expect(G.size).toBeGreaterThan(100);
    for (const t of ['--accent', '--danger', '--positive', '--text-muted', '--ck-border']) {
      expect(`${t} found: ${G.has(t)}`).toBe(`${t} found: true`);
    }
  });
});

/* ── 2.8 ONE TYPE SCALE, ONE SET OF NAMES ───────────────────────────────────
   The tree ran two type scales for months. tokens.css called --type-caption
   (12px) the smallest step; globals.css ran a parallel --fs-* clamp family
   whose floor was 11.52px; and ExecutiveCockpit.module.css added a THIRD hop,
   --ck-fs-*, aliasing the second. Phase 6.1 collapsed --fs-* to an alias of
   --type-*; Phase 6.4 deletes it.

   The alias could have stayed harmlessly. It should not have, and this is the
   assertion that keeps it gone: a second name for a scale is a second place to
   add a step, and that is exactly how the two floors came to disagree in the
   first place. Nobody added 11.52px on purpose — they added it to --fs-xs,
   which nobody was reading as "the type scale". */
describe('the type scale has one name', () => {
  const walk = (dir, out = []) => {
    for (const e of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const rel = `${dir}/${e.name}`;
      if (e.isDirectory()) { if (e.name !== 'node_modules') walk(rel, out); continue; }
      if (/\.(js|css)$/.test(e.name)) out.push(rel);
    }
    return out;
  };

  test('no file defines or consumes --fs-* or --ck-fs-*', () => {
    const hits = [];
    for (const f of walk('app')) {
      // Strip comments first: this file's own history is written in them, and
      // three earlier tripwires in this suite were tripped by prose describing
      // the defect they removed.
      const s = read(f).replace(/\/\*[\s\S]*?\*\//g, '');
      for (const m of s.matchAll(/--(?:ck-)?fs-[a-z]+/g)) hits.push(`${f}  ${m[0]}`);
    }
    expect(hits.slice(0, 8)).toEqual([]);
    expect(hits.length).toBe(0);
  });

  test('the scale it replaced is still there, and still has its floor', () => {
    // A deletion test that passes because BOTH scales vanished would be a
    // disaster reported as a success.
    const t = read('app/styles/tokens.css');
    for (const step of ['caption', 'body', 'title', 'display', 'lead', 'hero', 'mega']) {
      expect(`--type-${step} defined: ${new RegExp(`--type-${step}:`).test(t)}`)
        .toBe(`--type-${step} defined: true`);
    }
    expect(t).toMatch(/--type-caption:\s*0\.75rem/);   // 12px, the floor
  });
});
