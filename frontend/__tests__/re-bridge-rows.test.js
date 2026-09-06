/**
 * FIN-07 (audit 2026-09-04, Wave 3) — the statement names Retained Earnings as
 * the closing residual that balances it and prints the RE bridge residual
 * (RE − [opening + NI − dividends]) beside it, on the cockpit statement, the
 * history table and the modal. Before, "Retained Earnings" sat next to "Net
 * Income" as if one rolled forward from the other.
 */
const fs = require('fs');
const path = require('path');
const read = (rel) => fs.readFileSync(path.join(__dirname, '..', 'app', 'components', rel), 'utf8');

describe('the retained-earnings plug is named and bridged on every statement surface', () => {
  test('the cockpit statement and its history table', () => {
    const src = read('SustainabilityBalancedScorecard.js');
    expect(src).toMatch(/lineRow\('Retained Earnings \(closing residual\)'/);
    expect(src).toMatch(/balanceSheet\.re_bridge && lineRow\('RE bridge residual/);
    expect(src).toMatch(/balanceSheet\.re_bridge\.residual/);
    expect(src).toMatch(/label: 'Retained Earnings \(closing residual\)', get: s => s\.retained_earnings/);
    expect(src).toMatch(/label: 'RE bridge residual[^']*', get: s => s\.re_bridge_residual/);
    expect(src).not.toMatch(/lineRow\('Retained Earnings',/);
  });

  test('the balance-sheet modal', () => {
    const src = read('BalanceSheetModal.js');
    expect(src).toMatch(/lineRow\('Retained Earnings \(closing residual\)'/);
    expect(src).toMatch(/balanceSheet\.re_bridge && lineRow\('RE bridge residual/);
    expect(src).not.toMatch(/lineRow\('Retained Earnings',/);
  });
});
