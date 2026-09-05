/**
 * C-1 (owner calibration ruling, 2026-09-05) — the cockpit tells a team,
 * before it commits, whether its allocation backs the option's green claim,
 * measured the way the engine measures it: the TEAM'S share of the CSF pool
 * (or total CapEx at the absolute floor), with the bars served on the round
 * config so advice and check cannot disagree.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', rel), 'utf8');
const { greenClaimAdvice, DEFAULT_GREENWASH_BARS } = require('../app/components/greenClaimAdvice');

const bars = { full: 0.15, moderate: 0.1005, abs_capex_floor: 3_000_000 };

describe('greenClaimAdvice — the team share of the pool, not the BU average', () => {
  test('no claim, no advice', () => {
    expect(greenClaimAdvice({ option: { title: 'Deny & Deflect' }, allocations: { a: 1 }, csfPool: 10e6, bars })).toBeNull();
  });

  test('the archetypal real team (one BU at 50% of the pool, $1 elsewhere) backs a full claim', () => {
    const a = greenClaimAdvice({ option: { green_claim: 'full' }, allocations: { pharma: 5e6, electronics: 1, consumer_goods: 1, software: 1 }, csfPool: 10e6, bars });
    expect(a.backed).toBe(true);
    expect(a.share).toBeCloseTo(0.5, 6);
    expect(a.message).toMatch(/50\.0% of the CSF pool/);
  });

  test('12% of the pool spread over four BUs fails a full claim and clears a moderate one', () => {
    const alloc = { a: 300e3, b: 300e3, c: 300e3, d: 300e3 };
    const full = greenClaimAdvice({ option: { green_claim: 'full' }, allocations: alloc, csfPool: 10e6, bars });
    expect(full.backed).toBe(false);
    expect(full.message).toMatch(/12\.0% of the CSF pool/);
    expect(full.message).toMatch(/≥15\.0% of the pool/);
    expect(full.message).toMatch(/greenwashing/);
    const moderate = greenClaimAdvice({ option: { green_claim: 'moderate' }, allocations: alloc, csfPool: 10e6, bars });
    expect(moderate.backed).toBe(true);
  });

  test('total CapEx at the absolute floor backs any claim, whatever the share', () => {
    const a = greenClaimAdvice({ option: { green_claim: 'full' }, allocations: { a: 1e6, b: 1e6, c: 1e6 }, csfPool: 100e6, bars });
    expect(a.share).toBeCloseTo(0.03, 6);
    expect(a.backed).toBe(true);
  });

  test('falls back to the shipped bars when the round config carries none', () => {
    expect(DEFAULT_GREENWASH_BARS.full).toBe(0.15);
    const a = greenClaimAdvice({ option: { green_claim: 'full' }, allocations: { a: 1.4e6 }, csfPool: 10e6 });
    expect(a.backed).toBe(false);
  });
});

describe('the cockpit renders it and the server serves the bars', () => {
  test('ExecutiveCockpit shows the advice under the allocation, outside pillar mode, before the commit', () => {
    const src = read('components/ExecutiveCockpit.js');
    expect(src).toMatch(/import \{ greenClaimAdvice \} from '\.\/greenClaimAdvice'/);
    expect(src).toMatch(/data-testid="green-claim-advice"/);
    expect(src).toMatch(/!isPillarMode && decisionChoice && !commitResults/);
    expect(src).toMatch(/bars: roundConfig\?\.greenwash_bars/);
  });

  test('/round-config carries greenwash_bars from the engine constants', () => {
    const router = fs.readFileSync(path.join(__dirname, '..', '..', 'backend', 'router.py'), 'utf8');
    expect(router).toMatch(/"greenwash_bars": \{/);
    expect(router).toMatch(/_cfg\.GREENWASH_INVESTMENT_THRESHOLD \* _cfg\.GREENWASH_MODERATE_THRESHOLD_SCALE/);
    expect(router).toMatch(/_cfg\.GREENWASH_ABS_CAPEX_FLOOR/);
  });
});
