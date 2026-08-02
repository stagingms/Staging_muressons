/**
 * The player onboarding tour must not black out the cockpit it is describing.
 *
 * Reported: "briefing and workspace is not transparent". At the Capital
 * Allocation step the whole screen was uniformly dark with NO spotlight ring —
 * the tell that the step's target element was not in the DOM.
 *
 * That absence is normal, not a bug: `tour-capital-target` only renders inside
 * the deep-dive stage, so while the player is still in Foundation the tour
 * legitimately describes a panel that has not mounted yet. The defect was the
 * FALLBACK — with nothing to spotlight it painted the same heavy 0.75 veil
 * over everything, hiding the briefing and workspace for no benefit.
 *
 * Two veils, two jobs, so they are pinned separately:
 *   spotlight branch — must still push context back behind the ring
 *   no-target branch — must be markedly lighter; its only job is to seat the card
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const walkthrough = fs.readFileSync(
  path.join(APP, 'components', 'OnboardingWalkthrough.js'), 'utf8');

/** every `rgba(15, 23, 42, X)` alpha in the file, in source order */
function veilAlphas() {
  return [...walkthrough.matchAll(/rgba\(15,\s*23,\s*42,\s*([\d.]+)\)/g)]
    .map((m) => parseFloat(m[1]));
}

describe('onboarding tour veil', () => {
  test('there are exactly two veils — spotlight and no-target', () => {
    expect(veilAlphas()).toHaveLength(2);
  });

  test('neither veil blacks out the cockpit', () => {
    for (const a of veilAlphas()) {
      expect(a).toBeLessThanOrEqual(0.6);
    }
  });

  test('the no-target veil is markedly lighter than the spotlight veil', () => {
    // Source order: the spotlight box-shadow comes first, the full-screen
    // fallback second.
    const [spotlight, noTarget] = veilAlphas();
    expect(noTarget).toBeLessThan(spotlight);
    expect(spotlight - noTarget).toBeGreaterThanOrEqual(0.1);
  });

  test('the fallback still dims enough to seat the card', () => {
    const [, noTarget] = veilAlphas();
    expect(noTarget).toBeGreaterThan(0.2);
  });

  test('the spotlight ring is still drawn when a target resolves', () => {
    // Without the ring the lighter veil would leave no focal point at all.
    expect(walkthrough).toMatch(/border:\s*'2px dashed #a5b4fc'/);
    expect(walkthrough).toMatch(/boxShadow:\s*'0 0 0 9999px rgba\(15,\s*23,\s*42/);
  });

  test('a step whose element is absent falls back rather than breaking', () => {
    // The reported case: getElementById returns null -> spot stays 0 -> the
    // full-screen branch renders. Pin the zero-reset so a refactor cannot turn
    // a missing target into a crash or a stuck previous spotlight.
    expect(walkthrough).toMatch(/setSpot\(\{\s*x:\s*0,\s*y:\s*0,\s*w:\s*0,\s*h:\s*0\s*\}\)/);
    expect(walkthrough).toMatch(/spot\.w > 0 && spot\.h > 0 \?/);
  });
});
