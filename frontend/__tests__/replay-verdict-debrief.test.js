/**
 * RNG-4 (audit 2026-09-04, Wave 3) — the replay verifier has a door: the facilitator's
 * Round Debrief offers "Verify reproducibility", which calls the read-only
 * GET /api/admin/sessions/{id}/replay and shows the verdict with its scope.
 */
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'DebriefReport.js'), 'utf8');

test('the debrief calls the replay endpoint with credentials and renders the verdict and scope', () => {
  expect(src).toMatch(/fetch\(`\$\{API\}\/api\/admin\/sessions\/\$\{sessionId\}\/replay`, \{ credentials: 'include' \}\)/);
  expect(src).toMatch(/data-testid="replay-verify"/);
  expect(src).toMatch(/Replay verdict: \{replay\.verdict\}/);
  expect(src).toMatch(/replay\.scope/);
  expect(src).toMatch(/replay\.reading_guide/);
  // GET only — the verifier never mutates
  const seg = src.slice(src.indexOf('const runReplay'), src.indexOf('const runReplay') + 600);
  expect(seg).not.toMatch(/method:\s*'POST'/);
});
