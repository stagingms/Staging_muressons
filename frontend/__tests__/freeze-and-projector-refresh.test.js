/**
 * FLOW-10 / ACC-5 (audit 2026-09-04, Wave 3).
 * A facilitator freeze (503, detail.code "frozen") is not "server busy": no retry,
 * the facilitator's message goes to the waiting overlay. And the projector tab
 * refreshes the facilitator JWT like the console tabs do, so an 8 h cookie does
 * not freeze the room screen late on a long day.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

test('a coded freeze is surfaced as a facilitator lock, before the busy-server retry', () => {
  const src = read('hooks/useSimulation.js');
  const frozenAt = src.indexOf("frozen?.detail?.code === 'frozen'");
  const retryAt = src.indexOf('if (res.status === 429 || res.status === 503) {');
  expect(frozenAt).toBeGreaterThan(-1);
  expect(retryAt).toBeGreaterThan(frozenAt);
  const seg = src.slice(frozenAt, frozenAt + 600);
  expect(seg).toMatch(/setRoundLockReason\(\{ kind: 'facilitator'/);
  expect(seg).toMatch(/setRoundLocked\(true\)/);
  expect(seg).not.toMatch(/commitTurn\(\{ \.\.\.payload, _retryCount/);
});

test('the projector refreshes the facilitator JWT on an interval and on focus', () => {
  const src = read('admin/projector/page.js');
  expect(src).toMatch(/fetch\(`\$\{API\}\/api\/admin\/auth\/refresh`, \{ method: 'POST', credentials: 'include' \}\)/);
  expect(src).toMatch(/setInterval\(doRefresh, 90 \* 60 \* 1000\)/);
  expect(src).toMatch(/window\.addEventListener\('focus', onFocus\)/);
});
