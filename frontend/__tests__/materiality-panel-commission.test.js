/**
 * Audit 2026-09-04 F-10 / ACC-2 — the R2 matrix's stakeholder-panel hints.
 *
 * GET /api/admin/materiality-config no longer carries panel_recommendations
 * for a player (the experts column is the answer key). The matrix must fetch
 * a group's hints from the owner-bound commission endpoint when the player
 * commissions that group, and merge them into the per-issue badges. Source
 * pins: a regression here still renders and still parses.
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'DoubleMaterialityMatrix.js'),
  'utf8'
);

describe('DoubleMaterialityMatrix panel commission', () => {
  test('commissioning a group posts to the owner-bound endpoint with the player token', () => {
    const i = src.indexOf('const handleCommissionGroup = async (groupKey)');
    expect(i).toBeGreaterThan(-1);
    const fn = src.slice(i, i + 2200);
    expect(fn).toMatch(/\/api\/simulations\/\$\{sessionId\}\/materiality\/commission-panel/);
    expect(fn).toMatch(/\.\.\.playerIdHeader\(\)/);
    expect(fn).toMatch(/JSON\.stringify\(\{\s*group:\s*groupKey/);
  });

  test('the returned recommendations are merged per issue under the group key', () => {
    const i = src.indexOf('const handleCommissionGroup = async (groupKey)');
    const fn = src.slice(i, i + 2200);
    expect(fn).toMatch(/setPanelRecommendations\(prev =>/);
    expect(fn).toMatch(/\[groupKey\]:\s*quadrant/);
  });

  test('the config fetch still tolerates a body without panel_recommendations', () => {
    expect(src).toMatch(/if \(data\.panel_recommendations\) setPanelRecommendations\(data\.panel_recommendations\)/);
  });

  test('playerIdHeader is imported from the shared hook (not re-implemented)', () => {
    expect(src).toMatch(/import \{ playerIdHeader \} from '\.\.\/hooks\/useSimulation'/);
  });
});
