/**
 * Audit 2026-09-04 F-20 / WP-15 — the reveal's scale and units.
 *
 *  • The share count the ticker and the calculator divide by matches the
 *    backend config (6.5M — the reveal used to price every solvent team at
 *    $1–3 against a 100M-share, $5B implied IPO cap).
 *  • The NCD row subtracts the finale's MONETISED liability and labels the
 *    index in points; a payload from a game finished before the fix shows
 *    the index as points and subtracts nothing.
 */
import React from 'react';
import { render, act } from '@testing-library/react';
const fs = require('fs');
const path = require('path');

jest.mock('framer-motion', () => {
  const React = require('react');
  const passthrough = (tag) => React.forwardRef(({ children, initial, animate, exit, transition, whileHover, whileTap, variants, ...rest }, ref) =>
    React.createElement(tag, { ...rest, ref }, children));
  return {
    motion: new Proxy({}, { get: (_, tag) => passthrough(typeof tag === 'string' ? tag : 'div') }),
    AnimatePresence: ({ children }) => <>{children}</>,
    useReducedMotion: () => true,
  };
});

const read = (rel) => fs.readFileSync(path.join(__dirname, '..', rel), 'utf8');

describe('share count', () => {
  test('both client copies equal the backend config value', () => {
    const cfg = JSON.parse(read('../simulation_config.json'));
    expect(cfg.terminal_valuation.shares_outstanding).toBe(6500000);
    expect(read('app/components/stockValuationEngine.js')).toMatch(/SHARES_OUTSTANDING = 6_500_000/);
    expect(read('app/components/TerminalValuationCalc.js')).toMatch(/SHARES_OUTSTANDING = 6_500_000/);
  });
});

describe('ArchetypeReveal NCD row', () => {
  let ArchetypeReveal;
  beforeAll(() => {
    jest.useFakeTimers();
    ArchetypeReveal = require('../app/components/ArchetypeReveal').default;
  });
  afterAll(() => jest.useRealTimers());

  test('subtracts the monetised liability and shows the index in points', () => {
    render(<ArchetypeReveal payload={{ final_mr: 1.2, final_treasury: 60_000_000, total_ncd: 47, ncd_liability_usd: 564_000, archetype: 'SAFE_HAVEN' }} onContinue={() => {}} />);
    act(() => { jest.advanceTimersByTime(8000); });
    const src = read('app/components/ArchetypeReveal.js');
    expect(src).toMatch(/const adjustedFinalValue = mrAdjustedValue - ncdLiability;/);
    expect(src).not.toMatch(/mrAdjustedValue - total_ncd/);
    expect(document.body.textContent).toMatch(/47 NCD pts/);
  });

  test('a pre-fix payload shows the index as points and subtracts nothing', () => {
    const src = read('app/components/ArchetypeReveal.js');
    expect(src).toMatch(/formatter=\{\(v\) => `\$\{Math\.round\(v\)\} NCD pts`\}/);
    expect(src).toMatch(/\? Number\(ncd_liability_usd\) : 0/);
  });
});
