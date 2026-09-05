/**
 * Audit 2026-09-04 F-18(ii, iii) / WP-18 — the free-mode barrier and the
 * pacing chip.
 *
 *  • The commit hook recognises the server's `waiting_for_teams` 403 and
 *    raises the lock overlay with the barrier's copy and tally (not the
 *    "facilitator will unlock" copy).
 *  • DecisionPressureTimer polls the COHORT's pacing (parent_cohort_id), not
 *    the player sub-session's — which had a fresh default and no clock.
 *  • The auto-commit banner tells a Force Advance from a timeout and a
 *    submitted draft from defaults.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

describe('useSimulation commit 403 handling', () => {
  test('waiting_for_teams is distinguished from a facilitator lock', () => {
    const hook = read('hooks/useSimulation.js');
    expect(hook).toMatch(/denied\?\.detail\?\.code === 'waiting_for_teams'/);
    expect(hook).toMatch(/kind: 'teams'/);
    expect(hook).toMatch(/kind: 'facilitator'/);
    expect(hook).toMatch(/roundLockReason,/);
  });
});

describe('lock overlay copy', () => {
  test('says Waiting for Other Teams with the tally under the barrier', () => {
    const page = read('page.js');
    expect(page).toMatch(/sim\.roundLockReason\?\.kind === 'teams' \? 'Waiting for Other Teams' : 'Waiting for Facilitator'/);
    expect(page).toMatch(/teams committed/);
  });

  test('the auto-commit banner names the cause and the source', () => {
    const page = read('page.js');
    expect(page).not.toMatch(/Time expired — your turn was auto-committed with default choices/);
    expect(page).toMatch(/auto_committed_source === 'draft'/);
    expect(page).toMatch(/The facilitator advanced the round/);
    expect(page).toMatch(/your saved draft was submitted for you/);
  });
});

describe('DecisionPressureTimer scope', () => {
  test('polls the cohort resolved from session-info / parent_cohort_id', () => {
    const src = read('components/DecisionPressureTimer.js');
    expect(src).toMatch(/\/session-info/);
    expect(src).toMatch(/parent_cohort_id/);
    expect(src).toMatch(/\/api\/admin\/sessions\/\$\{encodeURIComponent\(cohortId\)\}\/pacing/);
    expect(src).not.toMatch(/\/api\/admin\/sessions\/\$\{encodeURIComponent\(sessionId\)\}\/pacing/);
  });
});
