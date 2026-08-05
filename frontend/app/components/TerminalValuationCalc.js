'use client';
import React, { useMemo } from 'react';
import styles from './ExecutiveCockpit.module.css';
import { currencySymbol } from '../utils/format';

/**
 * TerminalValuationCalc — Phase 3.7 (STRAT-010 update)
 * Live R10 Terminal Valuation calculator showing real-time
 * enterprise value projections based on current trajectory.
 *
 * STRAT-010 improvements:
 *  - Dynamic exit multiple derived from cost_of_capital (WACC → Gordon Growth)
 *  - Equity bridge: EV − estimated net debt = equity value → price per share
 *  - Shows both Enterprise Value and Share Price
 *
 * Only appears in Round 9-10 (Finale tier) when the student
 * needs to see how their cumulative decisions translate into
 * a final terminal value / M_R score.
 */

const SHARES_OUTSTANDING = 100_000_000;   // 100M shares (matches backend constant)
const IPO_PRICE = 50.0;                   // Opening price
const LONG_RUN_GROWTH = 0.02;             // 2% terminal growth
const EXIT_FLOOR = 6.0;
const EXIT_CEILING = 18.0;
const BASELINE_REVOLVING_CREDIT = 50_000_000;   // Seed debt from balance_sheet.py (~$12.5M/BU × 4)

/**
 * Gordon Growth Model exit multiple: (1+g) / (WACC−g)
 */
function dynamicExitMultiple(wacc) {
  if (wacc <= LONG_RUN_GROWTH) return EXIT_CEILING;
  const raw = (1 + LONG_RUN_GROWTH) / (wacc - LONG_RUN_GROWTH);
  return Math.max(EXIT_FLOOR, Math.min(EXIT_CEILING, raw));
}

export default function TerminalValuationCalc({
  globalState,
  businessUnits,
  roundNumber,
  history,
  fmtCurrency,
}) {
  const calc = useMemo(() => {
    if (roundNumber < 9) return null;
    if (!globalState || !businessUnits?.length) return null;

    const ebitda = businessUnits.reduce((acc, bu) =>
      acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0);
    const synergy = globalState.synergy_multiplier || 1.0;
    const reputation = globalState.group_reputation || 50;
    const treasury = globalState.corporate_treasury || 0;

    // Simplified M_R estimate (matching backend logic direction)
    const avgSLO = businessUnits.reduce((acc, bu) =>
      acc + (bu.social_license_score || 50), 0) / businessUnits.length;
    const avgBurnout = businessUnits.reduce((acc, bu) =>
      acc + (bu.staff_burnout_index || 0), 0) / businessUnits.length;
    const wr = globalState.workforce_readiness || 50;

    // M_R components (STRAT-010: synergy +0.15 not +0.30)
    const baseMR = 0.6;
    const synergyBonus = Math.max(0, (synergy - 0.8) * 0.375);  // Scaled for 0.15 max
    const reputationBonus = reputation > 60 ? (reputation - 60) * 0.005 : -(60 - reputation) * 0.008;
    const burnoutPenalty = avgBurnout > 40 ? (avgBurnout - 40) * 0.003 : 0;
    const sloPenalty = avgSLO < 50 ? (50 - avgSLO) * 0.006 : 0;
    const wrBonus = wr > 60 ? (wr - 60) * 0.003 : 0;

    const estimatedMR = Math.max(0.3, Math.min(2.5,
      baseMR + synergyBonus + reputationBonus - burnoutPenalty - sloPenalty + wrBonus
    ));

    // STRAT-010: Dynamic exit multiple from WACC
    const wacc = globalState.cost_of_capital || 0.08;
    const evMultiple = dynamicExitMultiple(wacc);
    const enterpriseValue = ebitda * estimatedMR * evMultiple;

    // STRAT-010: Equity bridge
    // Estimated net debt = seed revolving credit − treasury (simplified proxy)
    const estimatedDebt = BASELINE_REVOLVING_CREDIT;
    const netDebt = estimatedDebt - treasury;
    const equityValue = enterpriseValue - netDebt;
    const pricePerShare = equityValue / SHARES_OUTSTANDING;
    const spChangePct = ((pricePerShare - IPO_PRICE) / IPO_PRICE * 100).toFixed(1);

    return {
      ebitda,
      synergy,
      reputation,
      treasury,
      avgSLO: avgSLO.toFixed(0),
      avgBurnout: avgBurnout.toFixed(0),
      wr: wr.toFixed(0),
      estimatedMR: estimatedMR.toFixed(2),
      wacc: (wacc * 100).toFixed(1),
      evMultiple: evMultiple.toFixed(1),
      enterpriseValue,
      netDebt,
      equityValue,
      pricePerShare,
      spChangePct,
      components: [
        { label: 'EBITDA', value: fmtCurrency(ebitda), positive: ebitda > 0 },
        { label: 'Synergy ×', value: synergy.toFixed(2), positive: synergy >= 1.0 },
        { label: 'Reputation', value: `${reputation.toFixed(0)}/100`, positive: reputation >= 50 },
        { label: 'Burnout Risk', value: `${avgBurnout.toFixed(0)}%`, positive: avgBurnout < 40 },
        { label: 'Social License', value: avgSLO, positive: parseFloat(avgSLO) >= 50 },
        { label: 'Workforce', value: `${wr.toFixed(0)}%`, positive: wr >= 50 },
        { label: 'WACC', value: `${(wacc * 100).toFixed(1)}%`, positive: wacc <= 0.09 },
      ],
    };
  }, [globalState, businessUnits, roundNumber, fmtCurrency]);

  if (!calc) return null;

  const spColor = calc.pricePerShare >= IPO_PRICE ? '#10b981'
    : calc.pricePerShare >= IPO_PRICE * 0.6 ? '#f59e0b' : '#ef4444';

  return (
    <div className={styles.terminalCalc}>
      <div className={styles.terminalCalcTitle}>
        <span>🏦</span>
        <span>LIVE TERMINAL VALUATION — Round {roundNumber}</span>
      </div>

      {/* Formula Display */}
      <div className={styles.terminalFormula}>
        EV = EBITDA × M<sub>R</sub> × {calc.evMultiple}× ({calc.wacc}% WACC)
      </div>

      {/* Component Grid */}
      <div className={styles.terminalComponents}>
        {calc.components.map((c) => (
          <div key={c.label} className={styles.terminalComponent}>
            <span className={styles.terminalComponentLabel}>{c.label}</span>
            <span className={`${styles.terminalComponentValue} ${
              c.positive ? styles.terminalComponentPositive : styles.terminalComponentNegative
            }`}>
              {c.value}
            </span>
          </div>
        ))}
      </div>

      {/* Estimated M_R */}
      <div className={styles.terminalComponent} style={{ marginTop: 6 }}>
        <span className={styles.terminalComponentLabel}>Est. M<sub>R</sub></span>
        <span className={`${styles.terminalComponentValue} ${styles.terminalComponentNeutral}`}>
          {calc.estimatedMR}×
        </span>
      </div>

      {/* Enterprise Value */}
      <div className={styles.terminalTotal} style={{ marginTop: 8 }}>
        <span className={styles.terminalTotalLabel}>📊 Est. Enterprise Value</span>
        <span className={styles.terminalTotalValue}>
          {fmtCurrency(calc.enterpriseValue)}
        </span>
      </div>

      {/* Equity Bridge divider */}
      <div style={{ fontSize: 'var(--type-caption)', color: '#475569', margin: '6px 0 2px', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 700 }}>
        Equity Bridge (EV − Net Debt)
      </div>
      <div className={styles.terminalComponent}>
        <span className={styles.terminalComponentLabel}>Est. Net Debt</span>
        <span className={`${styles.terminalComponentValue} ${styles.terminalComponentNegative}`}>
          {fmtCurrency(Math.max(0, calc.netDebt))}
        </span>
      </div>
      <div className={styles.terminalComponent}>
        <span className={styles.terminalComponentLabel}>Equity Value</span>
        <span className={styles.terminalComponentValue} style={{ color: calc.equityValue > 0 ? '#10b981' : '#ef4444' }}>
          {fmtCurrency(calc.equityValue)}
        </span>
      </div>

      {/* Share Price — hero stat */}
      <div style={{
        marginTop: 10,
        padding: '10px 12px',
        background: `${spColor}18`,
        borderRadius: 8,
        border: `1px solid ${spColor}50`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#94a3b8' }}>
          📈 Est. Share Price
          <br />
          <span style={{ fontSize: 'var(--type-caption)', color: '#475569' }}>
            vs IPO $50.00 ({calc.spChangePct > 0 ? '+' : ''}{calc.spChangePct}%)
          </span>
        </span>
        <span style={{ fontSize: '1.5rem', fontWeight: 900, color: spColor, fontFamily: "'JetBrains Mono', monospace" }}>
         {currencySymbol()}{calc.pricePerShare.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
