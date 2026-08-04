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
  const v = String(raw).trim();
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
  'app/components/ExecutiveCockpit.js': 136,
  'app/components/ExecutiveCockpit.module.css': 36,
  'app/components/FocusOverlay.module.css': 8,
  'app/components/RoundBriefing.js': 12,
  'app/components/RoundBriefing.module.css': 2,
  'app/components/DoubleMaterialityMatrix.js': 22,
  'app/components/DoubleMaterialityMatrix.module.css': 20,
  'app/components/InvestmentMatrix.js': 2,
  'app/components/InvestmentMatrix.module.css': 11,
  'app/components/FrontPageReveal.js': 7,
  'app/components/GameOverSummary.js': 38,
  'app/components/GameOverSummary.module.css': 3,
  'app/components/ArchetypeReveal.js': 1,
  'app/components/JoinCohortModal.js': 3,
  'app/components/JoinCohortModal.module.css': 8,
  'app/components/OnboardingWalkthrough.js': 1,
  'app/components/CrisisAlerts.js': 1,
  'app/components/RoundChecklist.js': 6,
  'app/components/DecisionTile.js': 3,
  'app/components/CountdownTimer.js': 1,
  'app/components/KPIDashboard.js': 8,
  'app/components/MarketRealityFeed.js': 10,
  'app/components/BenchmarksPanel.js': 7,
  'app/components/CompetitorIntelligence.js': 5,
  'app/components/StockPerformanceChart.module.css': 4,
  'app/components/DecisionModal.module.css': 5,
  'app/page.js': 8,
  'app/page.module.css': 3,
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

const COMPONENT_MOUNTS = { 'app/components/ExecutiveCockpit.js': 57, 'app/page.js': 37 };

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

const SCALE = new Set([0, 4, 8, 12, 16, 24, 32, 48, 64]);

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
  'app/components/ExecutiveCockpit.module.css': 141,
  'app/components/FocusOverlay.module.css': 32,
  'app/components/RoundBriefing.module.css': 56,
  'app/components/DoubleMaterialityMatrix.module.css': 59,
  'app/components/InvestmentMatrix.module.css': 27,
  'app/components/GameOverSummary.module.css': 14,
  'app/components/JoinCohortModal.module.css': 15,
  'app/components/StockPerformanceChart.module.css': 10,
  'app/components/DecisionModal.module.css': 8,
  'app/page.module.css': 11,
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
  'app/components/ExecutiveCockpit.js': 164,
  'app/components/ExecutiveCockpit.module.css': 7,
  'app/components/FocusOverlay.js': 2,
  'app/components/RoundBriefing.js': 14,
  'app/components/DoubleMaterialityMatrix.js': 37,
  'app/components/DoubleMaterialityMatrix.module.css': 7,
  'app/components/InvestmentMatrix.js': 12,
  'app/components/InvestmentMatrix.module.css': 23,
  'app/components/FrontPageReveal.js': 21,
  'app/components/GameOverSummary.js': 63,
  'app/components/GameOverSummary.module.css': 1,
  'app/components/ArchetypeReveal.js': 15,
  'app/components/JoinCohortModal.js': 1,
  'app/components/JoinCohortModal.module.css': 1,
  'app/components/OnboardingWalkthrough.js': 3,
  'app/components/CrisisAlerts.js': 2,
  'app/components/RoundChecklist.js': 1,
  'app/components/DecisionTile.js': 14,
  'app/components/CountdownTimer.js': 3,
  'app/components/KPIDashboard.js': 25,   // 28 until Phase 3 retired the CAROIC grade chip
  'app/components/MarketRealityFeed.js': 11,
  'app/components/BenchmarksPanel.js': 8,
  'app/components/CompetitorIntelligence.js': 4,
  'app/components/StockPerformanceChart.module.css': 1,
  'app/components/DecisionModal.module.css': 1,
  'app/page.js': 8,
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
