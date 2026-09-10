/**
 * F05 (audit AUDIT_Engines_Flow_Classroom50_20260909, P1) — the Strategy
 * Report's Decision Timeline printed "$0" for every round because it read
 * `h.treasury ?? h.corporate_treasury` off dashboard rows that nest the
 * balance under global_state (the audit's export-probe generated the HTML
 * from a $50M row and got `$0`).
 *
 * The rows now come from strategyReportModel (opening = row K, closing =
 * row K+1 or the final state, decision = row K's choice or its pillar set),
 * and the report labels both balances.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

import { strategyReportRows, labelChoice } from '../app/components/strategyReportModel';

const row = (round, choice, treasury, extraFlags = {}) => ({
  round_number: round, choice_selected: choice,
  global_state: { corporate_treasury: treasury, group_reputation: 50, active_event_flags: { ...extraFlags } },
  business_units: [],
});

describe('strategyReportRows — the timeline model', () => {
  test('a schema-valid $50M row is a $50M row, labelled by its real round number', () => {
    const rows = strategyReportRows([row(1, 'option_a', 50_000_000)], { corporate_treasury: 50_000_000 });
    expect(rows).toHaveLength(1);
    expect(rows[0].round).toBe(1);
    expect(rows[0].opening).toBe(50_000_000);
    expect(rows[0].choice).toBe('Option A');
  });
  test('opening is row K, closing is row K+1, the delta chains, and the last round closes on the final state once the game is over', () => {
    const history = [row(1, 'option_a', 50e6), row(2, 'option_b', 62e6), row(3, 'option_c', 55.5e6)];
    const finalState = { corporate_treasury: 70e6, active_event_flags: { profile: 'steward', game_over: true } };
    const rows = strategyReportRows(history, finalState);
    expect(rows.map((r) => [r.round, r.opening, r.closing, r.delta])).toEqual([
      [1, 50e6, 62e6, 12e6],
      [2, 62e6, 55.5e6, -6.5e6],
      [3, 55.5e6, 70e6, 14.5e6],
    ]);
  });
  test('while the game is still in play the last round has no closing balance yet', () => {
    const history = [row(1, 'option_a', 50e6), row(2, 'option_b', 62e6)];
    const rows = strategyReportRows(history, { corporate_treasury: 62e6, active_event_flags: {} });
    expect(rows[1]).toMatchObject({ round: 2, opening: 62e6, closing: null, delta: null });
  });
  test('an is_final row (include_final exports) is the closing state, not a round', () => {
    const history = [row(9, 'option_a', 80e6), row(10, 'option_b', 85e6),
      { ...row(11, '', 91e6), is_final: true }];
    const rows = strategyReportRows(history, null);
    expect(rows.map((r) => r.round)).toEqual([9, 10]);
    expect(rows[1]).toMatchObject({ opening: 85e6, closing: 91e6, delta: 6e6 });
  });
  test('rows are ordered by round whatever order the dashboard sent them in', () => {
    const rows = strategyReportRows([row(2, 'option_b', 60e6), row(1, 'option_a', 50e6)], null);
    expect(rows.map((r) => r.round)).toEqual([1, 2]);
    expect(rows[0].closing).toBe(60e6);
  });
  test('a pillar round is labelled by its selections (from the next row\'s flags), not the proxy letter', () => {
    const r1 = row(1, 'option_b', 50e6);
    const r2 = row(2, '', 53e6, {
      pillar_selections: { energy: { action_key: 'renewable_ppa', title: 'Renewable PPA' }, operations: { action_key: 'lean_process', title: 'Lean Process Optimization' } },
    });
    expect(labelChoice(r1, r2)).toBe('Renewable PPA · Lean Process Optimization');
    expect(labelChoice(r1, undefined)).toBe('Option B');
    expect(labelChoice(row(3, '', 1), undefined)).toBe('—');
  });
});

describe('StudentReportExport — the generated HTML (the audit\'s export probe)', () => {
  test('a $50M row prints $50.00M, never $0, under labelled entering / after columns', () => {
    const modelSrc = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'strategyReportModel.js'), 'utf8')
      .replace(/^export default .*$/m, '').replace(/export /g, '');
    let src = fs.readFileSync(path.join(__dirname, '..', 'app', 'components', 'StudentReportExport.js'), 'utf8');
    src = src.replace(/^import .*;\r?$/mg, '').replace('export default function', 'function');
    src = src.slice(0, src.indexOf('\n  return (')) + '\nreturn generateReport;\n}\nthis.exporter=StudentReportExport;';
    let output = '';
    const ctx = {
      useCallback: (f) => f, currencySymbol: () => '$', atRate: (v) => v, Date,
      Blob: class { constructor(parts) { output = parts.join(''); } },
      URL: { createObjectURL: () => 'blob:isolated', revokeObjectURL: () => {} },
      window: { open: () => {} }, setTimeout: () => 0,
    };
    vm.createContext(ctx);
    vm.runInContext(modelSrc + '\n' + src, ctx);
    ctx.exporter({
      history: [row(1, 'option_a', 50_000_000), row(2, 'option_b', 61_250_000)],
      globalState: { corporate_treasury: 61_250_000, active_event_flags: {} },
    })();
    const tbody = output.match(/<tbody>(.*?)<\/tbody>/s)[1];
    expect(tbody).toContain('$50.00M');
    expect(tbody).toContain('$61.25M');
    expect(tbody).toContain('+$11.25M');
    expect(tbody).not.toMatch(/>\$0</);
    expect(output).toMatch(/<th[^>]*>Treasury entering<\/th>/);
    expect(output).toMatch(/<th[^>]*>Treasury after<\/th>/);
    expect(tbody).toMatch(/>R1<\/td>/);
    expect(tbody).toMatch(/>R2<\/td>/);
  });
});
