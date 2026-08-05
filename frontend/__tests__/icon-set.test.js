/**
 * icon-set.test.js — the icon vocabulary's contracts.
 *
 * The player tree carries 644 pictographic glyphs. Three things are wrong with
 * emoji for that job, and only the first is cosmetic: they render differently
 * on every platform, a screen reader announces their CLDR name ("balance
 * scale") beside a label that already says it, and they cannot take a colour —
 * which is how ✅/❌/⚠ came to encode state in a way no token can reach.
 *
 * What is asserted here is not that the paths are pretty. It is the three
 * properties that make the set safe to sweep 644 sites onto later.
 */
const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(path.join(__dirname, '..', 'app/components/Icon.js'), 'utf8');
/* Strip comments before asserting. This file's header DESCRIBES the policy it
   enforces — "Decorative by default: aria-hidden, focusable={false}" — so a
   naive count of `aria-hidden` finds the prose as well as the code and reports
   two modes where there is one. Four tripwires in this suite have now been
   tripped by documentation of the defect they removed; stripping first is the
   habit, not the exception. */
const src = raw.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

describe('the icon set is palette-independent', () => {
  test('every stroke is currentColor and nothing is filled', () => {
    /* This is what let the set ship BEFORE 6.3 finished rather than after it.
       An icon takes the colour of the text around it, so whatever --danger,
       --positive and --caution settle on, these follow without being touched
       again. A hard-coded stroke would have to be migrated a second time. */
    expect(src).toMatch(/stroke="currentColor"/);
    expect(src).toMatch(/fill="none"/);
    // No path may carry its own colour.
    const paths = src.slice(src.indexOf('const PATHS'), src.indexOf('export const ICON_NAMES'));
    expect(paths).not.toMatch(/#[0-9a-fA-F]{3,8}/);
    expect(paths).not.toMatch(/\bfill="(?!none)/);
    expect(paths).not.toMatch(/\bstroke="(?!currentColor)/);
  });

  test('it renders at 1em by default, so it tracks the type scale', () => {
    // A fixed pixel size would fight 6.1 — every icon beside a caption would
    // need re-picking when a step moved.
    expect(src).toMatch(/typeof size === 'number' \? `\$\{size\}px` : '1em'/);
  });
});

describe('the accessibility default is decorative, and there are only two modes', () => {
  test('no label means aria-hidden and unfocusable', () => {
    /* The majority case is an icon beside its own label, which is decoration.
       Announcing it there is exactly the emoji defect this replaces. */
    expect(src).toMatch(/'aria-hidden': 'true', focusable: 'false'/);
  });

  test('a label means role="img" with a name', () => {
    expect(src).toMatch(/role: 'img', 'aria-label': label/);
  });

  test('there is no third mode', () => {
    // "Sometimes announced" is how a label gets read twice. The ternary is the
    // whole policy; a <title> child or a conditional aria-hidden would be a
    // second, quieter path.
    expect(src).not.toMatch(/<title>/);
    const modes = src.match(/aria-hidden/g) || [];
    expect(`aria-hidden occurrences in code: ${modes.length}`).toBe('aria-hidden occurrences in code: 1');
  });
});

describe('an unknown name fails quietly rather than convincingly', () => {
  test('it renders nothing — no placeholder box', () => {
    /* A missing icon is a small hole. A placeholder is a small hole that looks
       deliberate, and it ships. */
    expect(src).toMatch(/if \(!d\) return null;/);
  });
});

describe('the set covers what the player surface actually uses', () => {
  const NAMES = (src.match(/^  ([a-zA-Z]+):/gm) || []).map((s) => s.trim().replace(':', ''));

  test('it is a vocabulary, not a library', () => {
    // 20 glyphs cover 60% of the 644 pictographs in the player tree. A set
    // that grows past what is used is a second decoration problem.
    expect(NAMES.length).toBeGreaterThanOrEqual(18);
    expect(NAMES.length).toBeLessThanOrEqual(28);
  });

  test('the highest-frequency meanings all have one', () => {
    // Measured from the player tree, most-used first.
    for (const n of ['warning', 'chart', 'globe', 'trendUp', 'clipboard', 'check',
                     'scales', 'money', 'leaf', 'bolt', 'factory', 'thermometer',
                     'bank', 'lock', 'people', 'shield']) {
      expect(`${n} in set: ${NAMES.includes(n)}`).toBe(`${n} in set: true`);
    }
  });

  test('direction is a pair, not a colour', () => {
    // trendUp/trendDown exist as separate marks so a change of direction does
    // not depend on a hue — which matters in a product where green already
    // means "good ESG outcome" more strongly than in most.
    expect(NAMES).toContain('trendUp');
    expect(NAMES).toContain('trendDown');
  });
});
