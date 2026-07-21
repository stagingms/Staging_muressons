/**
 * Tour-target tripwire.
 *
 * The onboarding wizard spotlights a region of the dashboard for each step by
 * querying a `data-tour` selector. If a sidebar group id is renamed, or an
 * anchor is dropped during a refactor, the selector silently resolves to null
 * and the step falls back to a centred card with nothing highlighted — the
 * exact failure this feature was built to fix, and invisible in code review.
 *
 * This test parses the wizard's declared targets and the anchors the
 * dashboards actually render (literal attributes plus the templated
 * `nav-${group.id}` form expanded over sidebarConfig) and fails on any
 * target that cannot resolve.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const read = (p) => fs.readFileSync(path.join(APP, p), 'utf8');

const wizard = read('components/OnboardingWizard.js');
const facilitator = read('admin/facilitator/page.js');
const godMode = read('admin/god-mode/page.js');
const sidebar = read('config/sidebarConfig.js');

function declaredTargets() {
  return [...wizard.matchAll(/target:\s*'\[data-tour="([^"]+)"\]'/g)].map((m) => m[1]);
}

function renderedAnchors() {
  const literal = [facilitator, godMode].flatMap((src) =>
    [...src.matchAll(/data-tour="([^"]+)"/g)].map((m) => m[1])
  );
  // Templated: data-tour={`nav-${group.id}`} covers every sidebar group id.
  const templated = [facilitator, godMode].some((src) =>
    src.includes('data-tour={`nav-${group.id}`}')
  )
    ? [...sidebar.matchAll(/^\s{4,8}id: '([a-z_]+)',/gm)].map((m) => `nav-${m[1]}`)
    : [];
  return new Set([...literal, ...templated]);
}

describe('onboarding tour targets', () => {
  test('every wizard step target resolves to a rendered data-tour anchor', () => {
    const anchors = renderedAnchors();
    const missing = declaredTargets().filter((t) => !anchors.has(t));
    expect({ missing, available: [...anchors].sort() }).toEqual({
      missing: [],
      available: [...anchors].sort(),
    });
  });

  test('both dashboards render the templated sidebar-group anchor', () => {
    expect(facilitator).toContain('data-tour={`nav-${group.id}`}');
    expect(godMode).toContain('data-tour={`nav-${group.id}`}');
  });

  test('both dashboards defer the tour while a password modal is open', () => {
    // The spotlight works by leaving a HOLE in four shade panels, so anything
    // painting a full-screen backdrop above it destroys the effect: every step
    // renders uniformly dim and the "highlighted" region is not transparent.
    // The password modals are z-index peers (20000) with exactly such a
    // backdrop, so each call site must pass `deferred`.
    for (const [name, src] of [['facilitator', facilitator], ['god-mode', godMode]]) {
      const call = src.slice(src.indexOf('<OnboardingWizard'));
      expect([name, /deferred=\{/.test(call.slice(0, call.indexOf('/>')))]).toEqual([name, true]);
    }
  });

  test('deferring hides the tour without consuming its localStorage key', () => {
    // A deferred tour is owed to the user; if `deferred` short-circuited after
    // the key was written the operator would silently never see the tour.
    const effect = wizard.slice(wizard.indexOf('const seen = localStorage.getItem'));
    const guard = wizard.indexOf('if (deferred)');
    expect(guard).toBeGreaterThan(-1);
    expect(guard).toBeLessThan(wizard.indexOf('const seen = localStorage.getItem'));
    expect(effect.slice(0, effect.indexOf('}'))).not.toContain('setItem');
  });

  test('each tour step declares a target key (null is explicit, not omitted)', () => {
    // Steps intentionally without a spotlight must say `target: null` so an
    // omission reads as an oversight rather than a deliberate full-screen step.
    const stepTitles = [...wizard.matchAll(/title: '([^']+)'/g)].length;
    const targetKeys = [...wizard.matchAll(/target:\s*(null|')/g)].length;
    expect(targetKeys).toBe(stepTitles);
  });
});
