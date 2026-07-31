/**
 * The CSRD matrix must never present a fresh assessment after completion.
 *
 * Reported (third round of this family): "the problem of CSRD matrix looping
 * again continues. especially when there is a CFO override."
 *
 * Server-side was exonerated by live drills on BOTH backends (memory and real
 * Postgres): bad Q1 → 400 CFO memo → Force Override → 200, csrd_completed
 * persists, a duplicate submit replays the committed result, and completion
 * survives the round-2 commit into round 3. The remaining loop vector is the
 * CLIENT: any remount of DoubleMaterialityMatrix reset showOnboarding(true)
 * and wiped every placement — intro modal again, empty quadrants: "the loop".
 * The override flow (submit → memo → decide) holds the player inside the
 * panel longest, so churn windows (paradigm re-poll, r2 refetch, dashboard
 * refresh) were most likely to strike then — "especially" with an override.
 *
 * Three defence layers pinned here:
 *   1. the intro is latched per session (and skipped entirely once submitted);
 *   2. an already-submitted session cannot resubmit from the client;
 *   3. the mount guard latches — churn can never unmount an open matrix
 *      (pinned in materiality-no-restart.test.js alongside its siblings).
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const matrix = fs.readFileSync(path.join(APP, 'components', 'DoubleMaterialityMatrix.js'), 'utf8');
const page = fs.readFileSync(path.join(APP, 'page.js'), 'utf8');

describe('csrd matrix loop — layer 1: the intro cannot replay', () => {
  test('dismissal is latched in localStorage, keyed by session', () => {
    expect(matrix).toMatch(/localStorage\.getItem\(`mur_dmm_intro_\$\{sessionId \|\| 'solo'\}`\)/);
    expect(matrix).toMatch(/localStorage\.setItem\(`mur_dmm_intro_\$\{sessionId \|\| 'solo'\}`, '1'\)/);
  });

  test('the overlay dismiss goes through the latching handler', () => {
    expect(matrix).toMatch(/<OnboardingOverlay onDismiss=\{dismissOnboarding\}/);
    expect(matrix).not.toMatch(/onDismiss=\{\(\) => setShowOnboarding\(false\)\}/);
  });

  test('a submitted session never sees the intro at all', () => {
    const i = matrix.indexOf('const [showOnboarding, setShowOnboarding] = useState(');
    expect(i).toBeGreaterThan(-1);
    expect(matrix.slice(i, i + 400)).toMatch(/if \(alreadySubmitted\) return false/);
  });
});

describe('csrd matrix loop — layer 2: no client resubmission after commit', () => {
  test('handleSubmit refuses before calling onSubmit when already submitted', () => {
    const i = matrix.indexOf('const handleSubmit = async (forceOverride = false)');
    expect(i).toBeGreaterThan(-1);
    const body = matrix.slice(i, i + 900);
    const guard = body.indexOf('if (alreadySubmitted)');
    const submitting = body.indexOf('setIsSubmitting(true)');
    expect(guard).toBeGreaterThan(-1);
    expect(guard).toBeLessThan(submitting);
    // and the refusal is NOT overridable — an override affordance on a
    // committed submission is precisely the loop.
    expect(body.slice(guard, guard + 400)).toMatch(/overridable: false/);
  });

  test('the submit button is disabled and says so', () => {
    expect(matrix).toMatch(/disabled=\{alreadySubmitted \|\| isSubmitting/);
    expect(matrix).toMatch(/Submitted — CFO has your matrix/);
  });

  test('page.js feeds the flag from the same gate the cockpit uses', () => {
    expect(page).toMatch(/alreadySubmitted=\{hasSubmittedMatrix\}/);
  });
});
