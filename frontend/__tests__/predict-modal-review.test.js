/**
 * Predict-Before-You-Commit modal — review contract.
 *
 * History this test exists to stop repeating:
 *   17111b0 retired the separate 'Review Your Decisions' modal, folding its
 *   two unique elements into the Predict screen: the per-BU allocation
 *   breakdown and the 'Go back' action (close WITHOUT committing).
 *
 *   UX audit 7.4 (2026-08-02) renamed these: the escape hatch and an
 *   irreversible commit shared a visual class AND the word 'Skip', which is a
 *   misclick trap on the highest-stakes click in the product. Labels are now
 *   'Go back' / 'Commit without predicting' / 'Commit decisions' — the two
 *   commit actions name the SAME verb so neither reads as a dismissal.
 *   1ef5c98 (a squashed session commit) then dropped both during a rewrite of
 *   the modal, leaving players with only the two commit actions —
 *   i.e. no way to review details or back out to change decisions. That is
 *   exactly the regression 17111b0's own commit message promised would not
 *   happen, and it shipped invisibly because nothing pinned the contract.
 *
 * Source-level pins (not render tests) because the deletion happened at the
 * source level and a render test's fixtures can mask a missing prop.
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'ExecutiveCockpit.js'),
  'utf8'
);

// Isolate the prediction modal block so pins can't be satisfied by unrelated code.
const modalStart = src.indexOf('PRE-COMMIT PREDICTION MODAL');
const modalEnd = src.indexOf('COMMIT RESULTS OVERLAY');

describe('Predict-Before-You-Commit modal', () => {
  const modal = src.slice(modalStart, modalEnd);

  test('the modal block itself is locatable', () => {
    expect(modalStart).toBeGreaterThan(-1);
    expect(modalEnd).toBeGreaterThan(modalStart);
  });

  test('offers Go Back & Edit — closing WITHOUT committing', () => {
    // Anchor on the BUTTON LABEL (with the arrow), not the phrase — comments
    // also mention 'Go Back & Edit' and must not satisfy this pin.
    const label = modal.indexOf('← Go back');
    expect(label).toBeGreaterThan(-1);
    // The button's onClick precedes its label inside the JSX: it must close
    // the modal and must NOT call onCommit (that is Skip & Commit's job).
    const handlerWindow = modal.slice(label - 400, label);
    expect(handlerWindow).toContain('setShowPredictionModal(false)');
    expect(handlerWindow).not.toContain('onCommit');
  });

  test('still offers both commit paths', () => {
    expect(modal).toContain('Commit without predicting');
    expect(modal).toContain('Confirm & Commit');
  });

  test('carries the per-BU allocation breakdown from the retired Review modal', () => {
    expect(modal).toContain('Object.entries(allocations');
    expect(modal).toMatch(/businessUnits.*find/);
  });

  test('all three actions live inside predictionActions', () => {
    const actions = modal.slice(modal.indexOf('predictionActions'));
    for (const label of ['Go back', 'Commit without predicting', 'Commit decisions']) {
      expect(actions).toContain(label);
    }
  });
});
