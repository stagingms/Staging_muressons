/**
 * SEAM-15 (audit 2026-09-04, Wave 3) — the cockpit's carbon-intensity tile is
 * the group's tCO₂e per $M revenue (emissions over revenue), not the mean of
 * the BU intensities; the benchmark panel's backend figure is the same number.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');

test('the cockpit divides emissions by revenue, with the BU mean only as a zero-revenue fallback', () => {
  const src = read('components/ExecutiveCockpit.js');
  expect(src).toMatch(/tco2e \/ \(totalRevenueForCi \/ 1_000_000\)/);
  expect(src).toMatch(/title="Group tCO₂e per \$M revenue \(revenue-weighted\)"/);
  expect(src).not.toMatch(/const avgCarbonIntensity = businessUnits\?\.length\s*\?\s*\(businessUnits\.reduce\(\(acc, bu\) => acc \+ \(bu\.carbon_intensity \|\| 0\), 0\) \/ businessUnits\.length\)/);
});

test('the arithmetic the tile performs matches the backend definition on the audit case', () => {
  const bus = [
    { carbon_intensity: 8.0, revenue_base: 30e6 }, { carbon_intensity: 6.0, revenue_base: 20e6 },
    { carbon_intensity: 4.56, revenue_base: 6.19e6 }, { carbon_intensity: 0, revenue_base: 1e6 },
  ];
  const tco2e = bus.reduce((a, b) => a + (b.carbon_intensity * b.revenue_base) / 1e6, 0);
  const rev = bus.reduce((a, b) => a + b.revenue_base, 0);
  const weighted = tco2e / (rev / 1e6);
  const mean = bus.reduce((a, b) => a + b.carbon_intensity, 0) / bus.length;
  expect(mean).toBeLessThan(5);
  expect(weighted).toBeGreaterThan(6.5);
});
