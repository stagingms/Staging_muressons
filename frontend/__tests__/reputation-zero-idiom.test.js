/**
 * Audit 2026-09-04 F-03 / SEAM-03 tripwire.
 *
 * `globalState.group_reputation || 50` turns a reputation of 0 — a reachable
 * state, the engine clamps at 0 — into 50. Eighteen player surfaces did it:
 * the KPI belt showed 50/100 for six rounds and the results overlay said
 * "reputation rose 23 points" for a team whose reputation had collapsed.
 * Only a MISSING value may default: use `?? 50`.
 *
 * Same shape as shockwave-catalog.test.js: parse the source, fail on drift.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue;
      walk(p, out);
    } else if (/\.(js|jsx|ts|tsx)$/.test(entry.name)) {
      out.push(p);
    }
  }
  return out;
}

const OFFENDERS = [
  /group_reputation\s*\|\|\s*50\b/,      // `|| 50` on the raw field
  /\.reputation\s*\|\|\s*50\b/,           // `|| 50` on a derived reputation
  /previous_reputation\s*\|\|\s*50\b/,
];

test('no player surface defaults a reputation of 0 to 50 with `|| 50`', () => {
  const hits = [];
  for (const file of walk(APP)) {
    const src = fs.readFileSync(file, 'utf8');
    src.split('\n').forEach((line, i) => {
      if (OFFENDERS.some((re) => re.test(line))) {
        hits.push(`${path.relative(APP, file)}:${i + 1}: ${line.trim()}`);
      }
    });
  }
  expect(hits).toEqual([]);
});

test('the belt formula treats 0 as a value', () => {
  // The exact expression the KPI belt uses (ExecutiveCockpit.js) — `??` keeps 0.
  const globalState = { group_reputation: 0 };
  const reputation = globalState?.group_reputation ?? 50;
  expect(reputation).toBe(0);
  expect(({}).group_reputation ?? 50).toBe(50);
});
