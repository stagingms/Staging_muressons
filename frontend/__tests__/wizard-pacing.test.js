/**
 * Audit 2026-09-04 F-18(i) / FLOW-02 / FLOW-11 — the cohort wizard's pacing
 * step and the RunBar unlock button.
 *
 *  • The wizard's per-round pickers are <input type="datetime-local">; their
 *    values are naive local wall-clock strings. The server treats a naive time
 *    as UTC, so the wizard must convert to UTC ISO (as RoundPacingControl's
 *    localToIso does) or every scheduled unlock is off by the timezone offset.
 *  • RunBar's "Unlock next round" used to POST with no body: the server's
 *    bare-call path increments, so a double-click or a retried request opened
 *    two rounds. It now names the round (target_round), which the server
 *    treats idempotently.
 *  • RoundPacingControl shows a restored cohort that still carries the
 *    wizard's old ids ("free_play"/"scheduled") as the mode it meant.
 */
const fs = require('fs');
const path = require('path');
const { wizardSchedulesToIso } = require('../app/components/CreateCohortModal');

const COMP = path.join(__dirname, '..', 'app', 'components');
const read = (f) => fs.readFileSync(path.join(COMP, f), 'utf8');

describe('wizardSchedulesToIso', () => {
  test('converts datetime-local values to UTC ISO and drops blanks/junk', () => {
    const out = wizardSchedulesToIso({ 1: '2026-09-07T09:00', 2: '', 3: 'not a date', 4: '2030-01-02T09:00' });
    expect(Object.keys(out)).toEqual(['1', '4']);
    expect(out['1']).toBe(new Date('2026-09-07T09:00').toISOString());
    expect(out['1']).toMatch(/Z$/);
    expect(out['4']).toBe(new Date('2030-01-02T09:00').toISOString());
  });

  test('is total: undefined/null/empty → {}', () => {
    expect(wizardSchedulesToIso()).toEqual({});
    expect(wizardSchedulesToIso(null)).toEqual({});
    expect(wizardSchedulesToIso({})).toEqual({});
  });
});

describe('source pins', () => {
  test('the wizard sends the converted schedule, not the raw picker values', () => {
    const src = read('CreateCohortModal.js');
    const i = src.indexOf("url: `${API}/api/admin/cohort/${sid}/pacing`");
    expect(i).toBeGreaterThan(-1);
    const step = src.slice(i, i + 800);
    expect(step).toMatch(/round_schedules:\s*pacingMode === 'scheduled' \? wizardSchedulesToIso\(roundSchedules\)/);
  });

  test('RunBar names the round it opens (idempotent unlock)', () => {
    const src = read('RunBar.js');
    const i = src.indexOf('/pacing/unlock`');
    expect(i).toBeGreaterThan(-1);
    const call = src.slice(i, i + 400);
    expect(call).toMatch(/body:\s*JSON\.stringify\(\{\s*target_round:\s*nextRound\s*\}\)/);
  });

  test('RoundPacingControl normalises the wizard\'s legacy mode ids', () => {
    const src = read('RoundPacingControl.js');
    expect(src).toMatch(/WIZARD_MODE_IDS\s*=\s*\{\s*free_play:\s*'free',\s*scheduled:\s*'timed'\s*\}/);
    expect(src).toMatch(/WIZARD_MODE_IDS\[data\.mode\]\s*\|\|\s*data\.mode/);
  });
});
