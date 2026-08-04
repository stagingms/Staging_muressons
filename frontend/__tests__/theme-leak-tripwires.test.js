/**
 * theme-leak-tripwires.test.js
 *
 * Pins the seven defects found by the 2026-08-02 real-browser pass on a
 * SIGNED-IN player cockpit (A11Y-F12 … F20). Every one of them was invisible
 * to the two floors this repo already had:
 *
 *   jest-axe (jsdom)  — no cascade, no geometry, `color-contrast` forced off.
 *   design-token-drift — counts raw hex, so it cannot see that a token
 *                        resolves to the wrong VALUE, or that a declaration
 *                        never wins the cascade at all.
 *
 * These are source-shape tripwires, not contrast assertions: a browser is the
 * only place a ratio can be measured, and this file is the cheap thing that
 * stops the same class of regression landing between browser passes.
 *
 * WHAT THE CLASS IS
 *   Every one of F12–F19 is the same shape — a SURFACE and the TEXT on it
 *   decided by two different mechanisms that disagree about the theme. Light
 *   text on a light surface, or dark on dark. The specific mechanisms differ
 *   (a losing cascade, an undefined token, a hard-coded hex, a class default
 *   meant for a background an inline style replaced), which is why no single
 *   lint catches them and why each gets its own tripwire below.
 */

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');

const COCKPIT_CSS = 'app/components/ExecutiveCockpit.module.css';
const COCKPIT_JS = 'app/components/ExecutiveCockpit.js';
const TICKER_JS = 'app/components/MarketTicker.js';
const CHECKLIST_JS = 'app/components/RoundChecklist.js';
const GLOBALS = 'app/globals.css';
const GATES = ['app/components/StakeholderMapModal.js', 'app/components/DoubleMaterialityMatrix.js'];

// ── F12: the cockpit's light surface tokens must be declared where they win ──

describe('A11Y-F12 — cockpit --ck-surface-* light overrides', () => {
  test('are declared on .cockpit itself, not only on <html>', () => {
    const css = read(COCKPIT_CSS);
    const light = css.slice(css.indexOf(':global([data-theme="light"]) .cockpit'));
    expect(light).toMatch(/--ck-surface-0:/);
    expect(light).toMatch(/--ck-surface-1:/);
  });

  test('globals.css still carries the same values, so the two cannot drift apart', () => {
    // globals.css's [data-theme="light"] block was where these lived and lost.
    // It stays — it is right for anything outside the cockpit — but the values
    // must agree or a component picks up whichever selector happens to win.
    const g = read(GLOBALS);
    expect(g).toMatch(/--ck-surface-0:\s*#f8fafc/);
    expect(g).toMatch(/--ck-surface-1:\s*#f1f5f9/);
    const css = read(COCKPIT_CSS);
    const light = css.slice(css.indexOf(':global([data-theme="light"]) .cockpit'));
    expect(light).toMatch(/--ck-surface-0:\s*#f8fafc/);
    expect(light).toMatch(/--ck-surface-1:\s*#f1f5f9/);
  });
});

// ── F13: no hard-coded dark surface the light shim does not know about ──────

test('A11Y-F13 — the left-rail guides panel uses the surface token, not #0a0e1a', () => {
  const js = read(COCKPIT_JS);
  const panel = js.slice(js.indexOf('id="tour-player-guides-target"'), js.indexOf('id="tour-player-guides-target"') + 600);
  expect(panel).toMatch(/background:\s*'var\(--ck-surface-0/);
  expect(panel).not.toMatch(/background:\s*'#0a0e1a'/);
});

// ── F14: a button that overrides its background must state its foreground ───

describe('A11Y-F14 — commit button states carry their own colour', () => {
  const js = () => read(COCKPIT_JS);

  test('every btnStyle branch sets both background and color', () => {
    const src = js();
    const start = src.indexOf('const btnStyle = commitResults');
    expect(start).toBeGreaterThan(-1);
    const block = src.slice(start, src.indexOf(';', src.indexOf('borderColor: \'#475569\' }', start)));
    const backgrounds = block.match(/background:/g) || [];
    const colors = block.match(/color: '#/g) || [];
    expect(backgrounds.length).toBeGreaterThanOrEqual(5);
    expect(colors.length).toBe(backgrounds.length);
  });

  test('the three early-return commit states do too', () => {
    const src = js();
    for (const bg of ["background: '#1e293b', color:", "background: '#3730a3', color:"]) {
      expect(src).toContain(bg);
    }
    // The bare form is what regressed: a slate background with no foreground.
    expect(src).not.toMatch(/background: '#1e293b', border:/);
  });

  test('globals.css pairs its light-surface rewrites with a foreground', () => {
    const g = read(GLOBALS);
    expect(g).toMatch(/\[style\*="background: rgb\(30, 41, 59\)"\]:not\(\[style\*="color"\]\)/);
  });
});

// ── F15: a theme-invariant surface needs a theme-invariant palette ──────────

describe('A11Y-F15 — the market ticker', () => {
  const js = () => read(TICKER_JS);

  test('is still unconditionally black — the premise of the fix', () => {
    expect(js()).toMatch(/const bg = '#000000';/);
  });

  test('draws no text colour from a theme token or an inline hex', () => {
    const src = js();
    // Either form re-opens the bug: a token follows a theme this strip does
    // not have, and an inline hex is what the globals.css shim rewrites.
    expect(src).not.toMatch(/color: 'var\(--/);
    expect(src).not.toMatch(/color: '#[0-9a-f]{3,6}'/i);
  });

  test('declares its palette as classes in its own style block', () => {
    const src = js();
    for (const cls of ['.tkSym', '.tkPrice', '.tkUp', '.tkDown']) expect(src).toContain(cls);
  });
});

// ── F17: an undefined token silently falls back to a hard-coded light ───────

test('A11Y-F17 — nothing consumes the undefined --bg-sidebar token', () => {
  // `--bg-sidebar` is declared NOWHERE in this codebase, so `var(--bg-sidebar,
  // #ffffff)` was a hard-coded white wearing a token's clothes — the rail's
  // tab strip stayed white in dark mode and nobody noticed for a release.
  // The assertion is on USE, not on the string: the name still appears in the
  // comment that explains this.
  const files = ['app/globals.css', COCKPIT_CSS, COCKPIT_JS, TICKER_JS, CHECKLIST_JS];
  for (const f of files) expect(read(f)).not.toMatch(/var\(--bg-sidebar/);
  // and the token used instead must actually be defined for both themes
  expect(read(COCKPIT_CSS)).toMatch(/--ck-surface-1:\s*#0e1222/);
});

test('A11Y-F17 — every rail tab carries a colour for each theme', () => {
  const js = read(COCKPIT_JS);
  for (const id of ['mailbox', 'decisions', 'engines', 'climate']) {
    const row = js.slice(js.indexOf(`{ id: '${id}', vis:`));
    const line = row.slice(0, row.indexOf('\n'));
    expect(line).toMatch(/onDark: '#/);
    expect(line).toMatch(/onLight: '#/);
  }
});

// ── F18: never animate the opacity of something that carries a glyph ────────

describe('A11Y-F18 — the unread badge', () => {
  test('uses badgePulse, not the opacity-dipping pulse', () => {
    const js = read(COCKPIT_JS);
    expect(js).toContain('badgePulse');
    expect(js).not.toContain("'pulse 1.5s ease-in-out infinite'");
  });

  test('badgePulse exists, animates box-shadow only, and yields to reduced motion', () => {
    const g = read(GLOBALS);
    const kf = g.slice(g.indexOf('@keyframes badgePulse'), g.indexOf('@keyframes badgePulse') + 260);
    expect(kf).toMatch(/box-shadow/);
    expect(kf).not.toMatch(/opacity/);
    expect(g).toMatch(/prefers-reduced-motion[\s\S]{0,200}badgePulse/);
  });

  test('sits on a red that carries white text', () => {
    // #f87171 + #fff is 2.68:1; #dc2626 + #fff is 4.83:1.
    const js = read(COCKPIT_JS);
    expect(js).not.toMatch(/tab\.badge === 'number' \? '#f87171'/);
    expect(js).toMatch(/tab\.badge === 'number' \? '#dc2626'/);
  });
});

// ── F19: a deliberately light card needs values chosen for white ────────────

test('A11Y-F19 — the round checklist has no light-card leak left to fix', () => {
  // WAS: the checklist was a rgba(255,255,255,0.98) slab in a dark cockpit, so
  // every colour inside it had to be picked for white rather than for the
  // theme -- and the "2/5" counter had been picked for neither, at 2.56:1.
  // F19 fixed that counter to #475569 and this test pinned the literal.
  //
  // The card is GONE. The checklist is a row of words on the action bar's own
  // surface, so it inherits the theme like everything else and there is no
  // white to work against. The assertion inverts: nothing in here may
  // hard-code a colour at all.
  // Strip comments first: this file's docblock QUOTES the white it removed,
  // and an assertion that reads prose is an assertion about prose.
  const js = read(CHECKLIST_JS).replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  expect(js).not.toMatch(/rgba\(255\s*,\s*255\s*,\s*255/);
  expect(js).not.toMatch(/#[0-9a-fA-F]{6}\b/);
  expect(js).toMatch(/var\(--positive-text\)/);
  expect(js).toMatch(/var\(--text-muted\)/);
});

test('A11Y-F19b — step state is not carried by colour alone', () => {
  // done / current / not-started were green / grey / grey, which is a
  // colour-only encoding for two of the three. Each step now carries visually
  // hidden text saying which it is, and the current one carries aria-current.
  const js = read(CHECKLIST_JS);
  expect(js).toMatch(/aria-current=/);
  for (const phrase of ['done', 'current step', 'not started']) {
    expect(js).toContain(phrase);
  }
});

// ── F20: keyboard drag must move between zones, not by 25px ─────────────────

describe('A11Y-F20 — both dnd-kit gates snap between droppables', () => {
  test.each(GATES)('%s passes a coordinateGetter to KeyboardSensor', (file) => {
    const src = read(file);
    expect(src).toMatch(/useSensor\(KeyboardSensor,\s*\{\s*coordinateGetter: droppableKeyboardCoordinates\s*\}\)/);
    expect(src).toContain("from '../lib/dndDroppableKeyboardCoordinates'");
  });

  test('the getter handles all four arrows and preserves the drop contract', () => {
    const src = read('app/lib/dndDroppableKeyboardCoordinates.js');
    for (const k of ['Right', 'Left', 'Down', 'Up']) expect(src).toContain(`KeyboardCode.${k}`);
    // It must return absolute coordinates, not a delta — dnd-kit treats the
    // return value as the new translate, so a delta would rebase every press.
    expect(src).toMatch(/currentCoordinates\.x \+/);
    expect(src).toMatch(/currentCoordinates\.y \+/);
  });
});

/* ════════════════════════════════════════════════════════════════════════
   MAILBOX — A11Y-M1 … M5

   The rail is where the game TALKS to the player: board briefings, crisis
   messages, rival press, the ESG rating. Measured on a signed-in cockpit it
   had **18 failing nodes in dark mode**, and the failures were not chrome —
   they were the message subjects at 1.02:1 and the previews at 1.68:1. Every
   briefing in the game, unreadable, in the theme the product ships as its
   default.

   The cause is the mirror image of F9. That shim rewrites DARK values found
   on light surfaces; nothing rewrites LIGHT values found on dark ones, and
   this whole subtree was authored in light-theme near-blacks. A shim can only
   ever cover the direction someone thought of.
   ════════════════════════════════════════════════════════════════════════ */

const MAILBOX_FILES = {
  personas: 'app/components/BoardPersonas.js',
  intel: 'app/components/MarketIntelCards.js',
  rival: 'app/components/rivalIntel.js',
  archive: 'app/components/ArchiveAccordion.js',
};

describe('A11Y-M1 — mailbox message subject and preview follow the theme', () => {
  test('neither is a hard-coded light-theme near-black any more', () => {
    const js = read(COCKPIT_JS);
    const start = js.indexOf('{currentMessages.map((msg, idx)');
    expect(start).toBeGreaterThan(-1);
    const block = js.slice(start, js.indexOf('{currentMessages.length === 0', start));
    expect(block).toMatch(/<strong style=\{\{ fontSize: '0\.68rem', color: 'var\(--text-primary\)' \}\}/);
    expect(block).toMatch(/color: 'var\(--text-secondary\)' \}\}>\{msg\.body/);
    // The exact pair that measured 1.02:1 and 1.68:1 on #151929.
    expect(block).not.toMatch(/color: '#0f172a'/);
    expect(block).not.toMatch(/color: '#334155'/);
  });

  test('personas expose a text-tier colour and keep the raw hue for borders', () => {
    const src = read(MAILBOX_FILES.personas);
    for (const t of ['--accent-text', '--positive-text', '--caution-text', '--danger-text', '--text-muted']) {
      expect(src).toContain(`textColor: 'var(${t})'`);
    }
    // ShadowBoardAudit.js concatenates `${persona.color}40` for a border —
    // a var() cannot take an alpha suffix, so `color` must survive.
    expect(src).toMatch(/color: '#6366f1'/);
    expect(read('app/components/ShadowBoardAudit.js')).toContain('${persona.color}40');
  });

  test('the mailbox item consumes textColor, not the border hue', () => {
    expect(read(COCKPIT_JS)).toContain('color: persona.textColor || persona.color');
  });
});

describe('A11Y-M2 — the Market Intelligence cards', () => {
  test('carry no light-theme near-blacks', () => {
    const src = read(MAILBOX_FILES.intel);
    for (const hex of ["'#0f172a'", "'#334155'", "'#b6c2d1'"]) expect(src).not.toContain(`color: ${hex}`);
  });

  test('the MARKET NEWS chip is no longer painted in its own background', () => {
    // #64748b text on rgba(100,116,139,0.12) — the same hue as the backdrop.
    // 1:1 in BOTH themes: not a theme bug, an authoring one.
    const src = read(MAILBOX_FILES.intel);
    const chip = src.slice(src.indexOf('MARKET NEWS') - 400, src.indexOf('MARKET NEWS'));
    expect(chip).toMatch(/color: 'var\(--text-secondary\)'/);
    expect(chip).not.toMatch(/color: '#64748b'/);
  });

  test('rating directions and sources expose a text-tier colour', () => {
    const src = read(MAILBOX_FILES.intel);
    for (const t of ['--positive-text', '--danger-text', '--text-muted', '--accent-text']) {
      expect(src).toContain(`textColor: 'var(${t})'`);
    }
    const rival = read(MAILBOX_FILES.rival);
    expect(rival).toMatch(/RIVAL = \{[^}]*textColor: 'var\(--text-muted\)'/);
    expect(rival).toMatch(/AGENCY = \{[^}]*textColor: 'var\(--accent-text\)'/);
  });
});

test('A11Y-M3 — the mailbox badge does not use a TEXT token as a surface', () => {
  const css = read(COCKPIT_CSS);
  const badge = css.slice(css.indexOf('.mailboxBadge {'), css.indexOf('.mailboxBadge {') + 220);
  // --danger-text is #f87171 in dark: white on it is 2.77:1.
  expect(badge).not.toMatch(/background: var\(--danger-text\)/);
  expect(badge).toMatch(/background: #dc2626/);
});

test('A11Y-M4 — the archive accordion is theme-aware, like the list it archives', () => {
  const src = read(MAILBOX_FILES.archive);
  // Assert on USE, not on the string — the values still appear in the comment
  // that records what they measured.
  const code = src.replace(/\/\*[\s\S]*?\*\//g, '');
  for (const hex of ['#f7f8fc', '#eef4ff', '#fafbff', '#eef0f6', '#6b7a8d', '#3b5998']) {
    expect(code).not.toContain(hex);
  }
  expect(src).toMatch(/var\(--ck-surface-2/);
  expect(src).toMatch(/var\(--text-primary\)/);
  expect(src).toMatch(/var\(--accent-text\)/);
});

test('A11Y-M5 — "read" is not signalled by an opacity that costs AA', () => {
  // 0.6 composited the preview body to 3.8:1 on the dark card, and read is
  // the state a message holds for the rest of the game.
  expect(read(COCKPIT_JS)).toContain("opacity: msg.read ? 0.85 : 1");
  expect(read(MAILBOX_FILES.archive)).toContain('opacity: msg.read ? 0.85 : 1');
  expect(read(COCKPIT_JS)).not.toContain('opacity: msg.read ? 0.6 : 1');
});

/* ════════════════════════════════════════════════════════════════════════
   A11Y-F21 / F22 — the shim's own answers

   The light-mode shim exists to make dark-theme pastels readable on white.
   TEN of its sixteen replacement values did not themselves reach AA on the
   surfaces it exists to fix, landing between 2.91:1 and 4.47:1 — and this
   same file had already measured and corrected the identical hues in its
   light TOKEN block under "A11Y-1 (UX audit #11)". The tokens were fixed;
   the shim was not. One palette, two copies, one of them stale.

   With that closed and the 500-weight families added, the signed-in cockpit
   and mailbox measure **zero failing text nodes in both themes**.
   ════════════════════════════════════════════════════════════════════════ */

describe('A11Y-F21 — every shim replacement clears AA on a light surface', () => {
  // #ffffff, #f8fafc, #f1f5f9 — the three light surfaces these land on.
  const SURFACES = ['#ffffff', '#f8fafc', '#f1f5f9'];
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (h) => {
    const n = h.replace('#', '');
    const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16));
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  };
  const ratio = (a, b) => {
    const [l1, l2] = [lum(a), lum(b)];
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };

  test('the arithmetic helper agrees with the values measured in Chromium', () => {
    // Guard the guard: if this drifts, every assertion below is meaningless.
    expect(ratio('#16a34a', '#ffffff')).toBeCloseTo(3.30, 1);
    expect(ratio('#15803d', '#ffffff')).toBeCloseTo(5.02, 1);
  });

  test('no [data-theme="light"] colour rule resolves below 4.5:1', () => {
    const g = read(GLOBALS);
    const rules = [...g.matchAll(/\[data-theme="light"\] \[style\*="color: rgb\([^)]+\)"\][^{]*\{\s*color:\s*(#[0-9a-f]{6})/gi)];
    expect(rules.length).toBeGreaterThanOrEqual(20);
    const bad = [];
    for (const m of rules) {
      const hex = m[1].toLowerCase();
      for (const s of SURFACES) {
        const r = ratio(hex, s);
        if (r < 4.5) bad.push(`${hex} on ${s} = ${r.toFixed(2)}`);
      }
    }
    expect(bad).toEqual([]);
  });

  test('the 500 weights are covered, not just the 300s and 400s', () => {
    const g = read(GLOBALS);
    // The weight a component reaches for when it wants a colour to read as
    // the colour itself — a status dot, a stage badge, a negative number.
    for (const rgb of [
      'rgb(16, 185, 129)',  // emerald-500
      'rgb(34, 197, 94)',   // green-500
      'rgb(239, 68, 68)',   // red-500
      'rgb(249, 115, 22)',  // orange-500
      'rgb(139, 92, 246)',  // violet-500
    ]) {
      expect(g).toContain(`[style*="color: ${rgb}"]`);
    }
  });
});

test('A11Y-F21 — chrome tokens are not used as text where a text tier exists', () => {
  const css = read(COCKPIT_CSS);
  // --brand is #0d9488, the chrome teal: 3.41:1 as text on the light rail.
  // --brand-text is the same identity in the tier meant for text.
  expect(css).toMatch(/\.buTickerName \{ color: var\(--brand-text\); \}/);
  expect(css).toMatch(/\.resourcesPillArrow \{\s*color: var\(--brand-text\);/);
  expect(css).toMatch(/\.roundContextTier \{[^}]*color: var\(--brand-text\); \}/);
});

test('A11Y-F22 — no keyframe animates the opacity of something carrying text', () => {
  // Four instances were found: the shared `pulse`, the rail badge, ci-pulse,
  // and criticalPulse. Each dipped a glyph below its measured contrast for
  // half of every cycle.
  for (const [file, name] of [
    ['app/components/CompetitorIntelligence.js', 'ci-pulse'],
    ['app/components/StakeholderAgentPanel.module.css', 'criticalPulse'],
  ]) {
    // Strip comments first: each fix quotes the keyframe it replaced, so a
    // naive indexOf finds the OLD definition inside the explanation.
    const src = read(file).replace(/\/\*[\s\S]*?\*\//g, '');
    const i = src.indexOf(`@keyframes ${name}`);
    expect(i).toBeGreaterThan(-1);
    const open = src.indexOf('{', i);
    let depth = 0, end = open;
    for (let j = open; j < src.length; j++) {
      if (src[j] === '{') depth++;
      else if (src[j] === '}' && --depth === 0) { end = j + 1; break; }
    }
    const kf = src.slice(i, end);
    expect(kf).toMatch(/box-shadow/);
    expect(kf).not.toMatch(/opacity/);
    expect(read(file)).toMatch(/prefers-reduced-motion/);
  }
});

test('A11Y-F21 — no light-theme neutral is left as a literal in dark-mode code', () => {
  // #64748b and #475569 are the LIGHT tier. The shim rewrites them in light
  // mode, so they look correct there and fail in dark, where no shim runs —
  // which is exactly how the KPI unit suffixes sat at 2.35:1 through three
  // audits. Assert on use, not on the string: both still appear in comments.
  for (const f of [COCKPIT_JS, 'app/components/BenchmarksPanel.js', 'app/components/StakeholderAgentPanel.js']) {
    const code = read(f).replace(/\/\*[\s\S]*?\*\//g, '').replace(/\{\/\*[\s\S]*?\*\/\}/g, '');
    expect(code).not.toMatch(/color: '#475569'/);
    expect(code).not.toMatch(/color: '#64748b'/);
  }
});
