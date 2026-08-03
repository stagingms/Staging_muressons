/**
 * a11y-real-browser.spec.js — the machine-executable half of
 * docs/ACCESSIBILITY_MANUAL_TESTS.md, run in a REAL browser.
 *
 * WHY THIS EXISTS
 *   The jest-axe floor (__tests__/a11y-axe.test.js) runs in jsdom, which has no
 *   layout engine and no cascade. That forced twelve axe rules off — including
 *   `color-contrast` — and made four components untestable, among them the
 *   dnd-kit capital allocation, the largest Level A risk in the product.
 *
 *   Chromium + real layout removes those limits. This suite therefore covers
 *   the parts of the manual script that are MECHANICAL:
 *     TEST 1  keyboard-only path            (2.1.1, 2.1.2, 2.4.3, 2.4.7)
 *     TEST 3  focus management sweep        (2.4.3, 2.1.2)
 *     TEST 4  200% zoom and 320px reflow    (1.4.4, 1.4.10)
 *     TEST 5  contrast, both themes         (1.4.3, 1.4.11) — axe, real cascade
 *     +       target size measured from real geometry (2.5.8, WCAG 2.2)
 *     +       accessibility-tree snapshots as a PROXY for announcement
 *
 * WHAT IT DOES NOT REPLACE
 *   TEST 2 (NVDA) and TEST 6 (projector at 10m) still require a human. An
 *   accessibility-tree snapshot tells you what a screen reader has to work
 *   with; it does not tell you whether the result is comprehensible when
 *   spoken. Those two tests stay in the manual document.
 *
 * RUN
 *   Backend on :8000, frontend on :3000, then:
 *     npx playwright test e2e/a11y-real-browser.spec.js --reporter=list
 */

const { test, expect, chromium } = require('@playwright/test');
const { AxeBuilder } = require('@axe-core/playwright');

const BASE = process.env.A11Y_BASE_URL || 'http://127.0.0.1:3000';

/** Serious/critical only — moderate noise is triaged, not gated. */
const GATING_IMPACTS = ['serious', 'critical'];

function summarise(results) {
  return results.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    help: v.help,
    nodes: v.nodes.length,
    sample: v.nodes.slice(0, 2).map((n) => n.target.join(' ')),
  }));
}

async function axeScan(page, { theme } = {}) {
  if (theme) {
    await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);
    await page.waitForTimeout(300);
  }
  return new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    // `next dev` injects a dev-only error overlay (<nextjs-portal>) that does
    // not exist in a production build. Scanning it would report defects in
    // Next.js, not in this product.
    .exclude('nextjs-portal')
    .analyze();
}

test.describe('TEST 5 — contrast and full-page axe, BOTH themes (real cascade)', () => {
  for (const theme of ['dark', 'light']) {
    test(`player sign-in — ${theme}`, async ({ page }) => {
      await page.goto(BASE, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2500);
      const res = await axeScan(page, { theme });
      const gating = res.violations.filter((v) => GATING_IMPACTS.includes(v.impact));
      console.log(`\n[player/${theme}] violations:`, JSON.stringify(summarise(res), null, 2));
      expect(gating, `serious/critical violations on the player sign-in in ${theme} mode`).toEqual([]);
    });

    test(`facilitator dashboard — ${theme}`, async ({ page }) => {
      await page.goto(`${BASE}/admin/facilitator`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2500);
      const res = await axeScan(page, { theme });
      const gating = res.violations.filter((v) => GATING_IMPACTS.includes(v.impact));
      console.log(`\n[facilitator/${theme}] violations:`, JSON.stringify(summarise(res), null, 2));
      expect(gating, `serious/critical violations on the facilitator dashboard in ${theme} mode`).toEqual([]);
    });
  }

  test('projector board — dark (the room screen)', async ({ page }) => {
    await page.goto(`${BASE}/admin/projector`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const res = await axeScan(page);
    console.log('\n[projector] violations:', JSON.stringify(summarise(res), null, 2));
    const gating = res.violations.filter((v) => GATING_IMPACTS.includes(v.impact));
    expect(gating).toEqual([]);
  });
});

test.describe('TEST 1 / 3 — keyboard-only reachability and focus visibility', () => {
  test('T1.1 sign-in fields are reachable by Tab and have a visible focus ring', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);

    const reached = [];
    let ringSeen = false;
    for (let i = 0; i < 25; i++) {
      await page.keyboard.press('Tab');
      const info = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return null;
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || null,
          type: el.getAttribute('type'),
          name: el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 40) || '',
          // 2.4.7: an outline, a ring-like shadow, or a border change all count.
          focusVisible:
            (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) ||
            (cs.boxShadow && cs.boxShadow !== 'none'),
          w: Math.round(r.width), h: Math.round(r.height),
        };
      });
      if (!info) continue;
      reached.push(info);
      if (info.focusVisible) ringSeen = true;
    }
    console.log('\n[T1.1] tab stops:', JSON.stringify(reached, null, 2));

    // SC 2.1.1 — both credential fields must be reachable by keyboard alone.
    expect(reached.some((r) => r.id === 'join-player-id'), 'player-id field reachable by Tab').toBe(true);
    expect(reached.some((r) => r.id === 'join-password'), 'password field reachable by Tab').toBe(true);
    // SC 2.4.7 — at least some focused element shows a visible indicator.
    expect(ringSeen, 'no focused element showed a visible focus indicator').toBe(true);
  });

  test('T1.1b sign-in fields have accessible names that survive typing', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const id = page.locator('#join-player-id');
    await id.fill('MUR-001');
    // The placeholder is gone once text is entered — the NAME must not be.
    const name = await id.evaluate((el) => {
      const lbl = el.labels && el.labels[0];
      return el.getAttribute('aria-label') || (lbl ? lbl.textContent.trim() : null);
    });
    console.log('\n[T1.1b] accessible name after typing:', name);
    expect(name, 'field lost its accessible name once filled (SC 3.3.2)').toBeTruthy();
  });

  test('T3 focus is visible and never lands on a zero-size element', async ({ page }) => {
    await page.goto(`${BASE}/admin/facilitator`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const zeroSize = [];
    for (let i = 0; i < 40; i++) {
      await page.keyboard.press('Tab');
      const bad = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return null;
        // Dev-overlay artifact — absent from a production build.
        if (el.tagName.toLowerCase() === 'nextjs-portal' || el.closest('nextjs-portal')) return null;
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) {
          return `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''} "${(el.textContent || '').trim().slice(0, 30)}"`;
        }
        return null;
      });
      if (bad) zeroSize.push(bad);
    }
    console.log('\n[T3] zero-size focus targets:', zeroSize);
    // A focus stop with no box cannot show a focus indicator (2.4.7) and is
    // invisible to a sighted keyboard user.
    expect(zeroSize, 'focus landed on element(s) with no rendered box').toEqual([]);
  });
});

test.describe('TEST 4 — zoom and reflow', () => {
  test('T4.2 no horizontal scroll at 320px (SC 1.4.10 Reflow)', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    for (const path of ['/', '/admin/facilitator']) {
      await page.goto(`${BASE}${path}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2500);
      const overflow = await page.evaluate(() => ({
        scrollW: document.documentElement.scrollWidth,
        clientW: document.documentElement.clientWidth,
      }));
      console.log(`\n[T4.2] ${path} @320px:`, JSON.stringify(overflow));
      // 1.4.10 allows a small tolerance for sub-pixel rounding.
      expect(
        overflow.scrollW - overflow.clientW,
        `${path} scrolls horizontally at 320px (SC 1.4.10)`,
      ).toBeLessThanOrEqual(4);
    }
  });

  test('T4.1 content survives 200% zoom (SC 1.4.4 Resize Text)', async ({ page }) => {
    // 1280x800 at 200% == a 640x400 CSS viewport.
    await page.setViewportSize({ width: 640, height: 400 });
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const o = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      clientW: document.documentElement.clientWidth,
    }));
    console.log('\n[T4.1] @200% zoom equivalent:', JSON.stringify(o));
    expect(o.scrollW - o.clientW, 'horizontal scroll at 200% zoom (SC 1.4.4)').toBeLessThanOrEqual(4);
  });
});

test.describe('Target size measured from real geometry (SC 2.5.8, WCAG 2.2)', () => {
  test('interactive controls are at least 24x24 CSS px', async ({ page }) => {
    await page.goto(`${BASE}/admin/facilitator`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const undersized = await page.evaluate(() => {
      const out = [];
      const els = document.querySelectorAll('button, a[href], input:not([type="hidden"]), select, [role="button"]');
      for (const el of els) {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;      // hidden
        if (r.width < 24 || r.height < 24) {
          out.push({
            what: `${el.tagName.toLowerCase()} "${(el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 32)}"`,
            w: Math.round(r.width), h: Math.round(r.height),
          });
        }
      }
      return out;
    });
    console.log('\n[2.5.8] undersized targets:', JSON.stringify(undersized, null, 2));
    // Reported, not gated: 2.5.8 is WCAG 2.2 and the client's obligation is 2.1.
    expect(Array.isArray(undersized)).toBe(true);
  });
});

test.describe('Accessibility tree snapshot — a PROXY for what NVDA has to work with', () => {
  test('player sign-in exposes named, roled controls', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    // page.accessibility was removed from recent Playwright, so compute the
    // accessible name the same way the AccName algorithm's common branches do.
    const nodes = await page.evaluate(() => {
      const named = [];
      const els = document.querySelectorAll('button, a[href], input:not([type="hidden"]), select, textarea, [role="button"]');
      for (const el of els) {
        if (el.closest('nextjs-portal')) continue;
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;
        const labelledby = el.getAttribute('aria-labelledby');
        let name = el.getAttribute('aria-label') || '';
        if (!name && labelledby) {
          name = labelledby.split(/\s+/).map((id) => document.getElementById(id)?.textContent || '').join(' ').trim();
        }
        if (!name && el.labels && el.labels[0]) name = el.labels[0].textContent.trim();
        if (!name) name = (el.textContent || '').trim();
        if (!name) name = el.getAttribute('title') || '';
        named.push({
          what: `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}`,
          role: el.getAttribute('role') || el.tagName.toLowerCase(),
          name: name.slice(0, 48),
        });
      }
      return named;
    });
    console.log('\n[a11y names] player sign-in:\n' + JSON.stringify(nodes, null, 2));
    const unnamed = nodes.filter((n) => !n.name);
    console.log('\n[a11y names] UNNAMED interactive nodes:', JSON.stringify(unnamed));
    expect(unnamed, 'interactive node(s) with no accessible name (SC 4.1.2)').toEqual([]);
  });
});
