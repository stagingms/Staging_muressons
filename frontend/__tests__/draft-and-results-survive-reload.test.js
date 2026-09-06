/**
 * FLOW-05 / FLOW-06 (audit 2026-09-04, Wave 3).
 *
 * FLOW-05: the draft is saved ~2 s after the last change and, keepalive, when
 * the page is hidden or unloaded — not by a 30 s timer every slider reset.
 * FLOW-06: the round-results screen survives a reload (kept in sessionStorage
 * until Advance), and the briefing's "Last Round Summary" is computed from the
 * history rows it actually has.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

function loadSummary() {
  const src = read('components/lastRoundSummary.js').replace(/^export default .*$/m, '').replace(/export /g, '');
  const m = {};
  // eslint-disable-next-line no-new-func
  new Function('module', `${src}\nmodule.lastRoundSummary = lastRoundSummary;`)(m);
  return m.lastRoundSummary;
}
const lastRoundSummary = loadSummary();

describe('FLOW-05 — the draft is saved on change and on unload', () => {
  const page = read('page.js');
  const hook = read('hooks/useSimulation.js');
  test('the 30 s interval is gone; a 2 s debounce on allocations or option replaces it', () => {
    expect(page).not.toMatch(/setInterval\(\(\) => \{\s*handleSaveDecisions\(\);/);
    expect(page).toMatch(/setTimeout\(\(\) => \{\s*saveDraft\(/);
    expect(page).toMatch(/\}, 2_000\);/);
    expect(page).toMatch(/\[hasDraft, saveDraft, allocations, decisionChoice\]/);
  });
  test('an untouched option no longer gates the save — any positive allocation is a draft', () => {
    expect(page).toMatch(/!!decisionChoice \|\| Object\.values\(allocations \|\| \{\}\)\.some\(\(v\) => Number\(v\) > 0\)/);
  });
  test('beforeunload / pagehide / visibilitychange flush the draft with keepalive', () => {
    expect(page).toMatch(/window\.addEventListener\('beforeunload', flush\)/);
    expect(page).toMatch(/window\.addEventListener\('pagehide', flush\)/);
    expect(page).toMatch(/document\.addEventListener\('visibilitychange', onVisibility\)/);
    expect(page).toMatch(/\{ quiet: true, keepalive: true \}/);
    expect(hook).toMatch(/async \(payload, \{ quiet = false, keepalive = false \} = \{\}\)/);
    expect(hook).toMatch(/keepalive,\s*\}/);
    expect(hook).toMatch(/if \(!quiet\) \{ setLoading\(true\); setError\(null\); \}/);
  });
});

describe('FLOW-06 — the results screen survives a reload', () => {
  const hook = read('hooks/useSimulation.js');
  test('the commit response is kept in sessionStorage until Advance', () => {
    expect(hook).toMatch(/writePendingResults\(sessionId, results\)/);
    expect(hook).toMatch(/clearPendingResults\(sessionId\);\s*\/\/ FLOW-06: the player has seen the results/);
    expect(hook).toMatch(/const PENDING_RESULTS_KEY = \(sid\) => `muressons_pending_results_\$\{sid\}`/);
  });
  test('resume restores the committed round under the pending results and skips the next briefing', () => {
    expect(hook).toMatch(/const pending = readPendingResults\(sid\);/);
    expect(hook).toMatch(/data\?\.current_round === pending\.newRoundNumber/);
    expect(hook).toMatch(/setRoundNumber\(pending\.roundCommitted\)/);
    expect(hook).toMatch(/setCommitResults\(pending\);\s*prevRoundRef\.current = pending\.roundCommitted;\s*setRoundChanged\(false\);/);
  });
});

describe('FLOW-06 — Last Round Summary reads the rows it has', () => {
  const history = [
    { round_number: 1, choice_selected: 'option_b', global_state: { corporate_treasury: 50e6, group_reputation: 50 } },
    { round_number: 2, choice_selected: 'option_a', global_state: { corporate_treasury: 62e6, group_reputation: 47, active_event_flags: {} } },
    { round_number: 3, choice_selected: '', global_state: { corporate_treasury: 55.5e6, group_reputation: 44.25, active_event_flags: { strike_triggered: true } } },
  ];
  test('round N summary = choice made in N−1, deltas row N − row N−1, events from the flags entering N', () => {
    const s2 = lastRoundSummary(history, 2);
    expect(s2).toEqual({ round: 1, choice: 'Option B', choice_key: 'option_b', treasury_delta: 12e6, reputation_delta: -3, events: { strike_triggered: false } });
    const s3 = lastRoundSummary(history, 3);
    expect(s3.round).toBe(2);
    expect(s3.choice).toBe('Option A');
    expect(s3.treasury_delta).toBe(-6.5e6);
    expect(s3.reputation_delta).toBe(-2.75);
    expect(s3.events.strike_triggered).toBe(true);
  });
  test('round 1 and missing rows produce no panel rather than an empty one', () => {
    expect(lastRoundSummary(history, 1)).toBeNull();
    expect(lastRoundSummary(history, 9)).toBeNull();
    expect(lastRoundSummary(null, 3)).toBeNull();
  });
  test('the page hands the briefing the computed summary, not a raw history row', () => {
    const page = read('page.js');
    expect(page).toMatch(/prevRoundData=\{lastRoundSummary\(sim\.history, roundNumber\)\}/);
    expect(page).not.toMatch(/prevRoundData=\{sim\.history\?\.\[sim\.history\.length - 1\]\}/);
    const briefing = read('components/RoundBriefing.js');
    expect(briefing).toMatch(/moneyM\(prevRoundData\.treasury_delta\)/);
  });
});
