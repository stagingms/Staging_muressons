/**
 * N4 (EVAL_AuditResponse 2026-09-10, action 10) — the cockpit's ecosystem-
 * services figure is labelled in the unit the engine computes it in.
 *
 * biodiversity_engine.ESV_BASE is "$/round" and "Nature's Invoice" is charged
 * per round; the widget said "/yr" (a round is half a year — WP-23's annual
 * revenue is 2 × Σ revenue_base). The label is pinned to the backend source
 * so the two cannot drift apart silently again.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', rel), 'utf8');

test('the ESV tile says /round, matching the engine unit', () => {
  const widget = read('app/components/SystemEngineMetrics.js');
  expect(widget).toMatch(/ESV: \{fmtCurrency\(bio\.ecosystem_services_value\)\}\/round</);
  expect(widget).not.toMatch(/ecosystem_services_value\)\}\/yr/);

  const engine = read('../backend/biodiversity_engine.py');
  expect(engine).toMatch(/"ecosystem_services_value": ESV_BASE,\s*# \$\/round/);
  expect(engine).toMatch(/Dollar value \(\$\/round\)/);
});
