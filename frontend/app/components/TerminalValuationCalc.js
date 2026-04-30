'use client';
import React, { useMemo } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * TerminalValuationCalc — Phase 3.7
 * Live R10 Terminal Valuation calculator showing real-time
 * enterprise value projections based on current trajectory.
 *
 * Only appears in Round 9-10 (Finale tier) when the student
 * needs to see how their cumulative decisions translate into
 * a final terminal value / M_R score.
 *
 * Props:
 *   - globalState:   current global state
 *   - businessUnits: current BUs
 *   - roundNumber:   current round
 *   - history:       round history array
 *   - fmtCurrency:   currency formatter
 */

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

    // M_R components (simplified estimation)
    const baseMR = 0.6;
    const synergyBonus = Math.max(0, (synergy - 0.8) * 0.5);
    const reputationBonus = reputation > 60 ? (reputation - 60) * 0.005 : -(60 - reputation) * 0.008;
    const burnoutPenalty = avgBurnout > 40 ? (avgBurnout - 40) * 0.003 : 0;
    const sloPenalty = avgSLO < 50 ? (50 - avgSLO) * 0.006 : 0;
    const wrBonus = wr > 60 ? (wr - 60) * 0.003 : 0;

    const estimatedMR = Math.max(0.3, Math.min(2.5,
      baseMR + synergyBonus + reputationBonus - burnoutPenalty - sloPenalty + wrBonus
    ));

    // Terminal value = EBITDA × M_R × 8 (simplified EV/EBITDA multiple)
    const evMultiple = 8;
    const terminalValue = ebitda * estimatedMR * evMultiple;

    return {
      ebitda,
      synergy,
      reputation,
      treasury,
      avgSLO: avgSLO.toFixed(0),
      avgBurnout: avgBurnout.toFixed(0),
      wr: wr.toFixed(0),
      estimatedMR: estimatedMR.toFixed(2),
      terminalValue,
      components: [
        { label: 'EBITDA', value: fmtCurrency(ebitda), positive: ebitda > 0 },
        { label: 'Synergy ×', value: synergy.toFixed(2), positive: synergy >= 1.0 },
        { label: 'Reputation', value: `${reputation.toFixed(0)}/100`, positive: reputation >= 50 },
        { label: 'Burnout Risk', value: `${avgBurnout.toFixed(0)}%`, positive: avgBurnout < 40 },
        { label: 'Social License', value: avgSLO, positive: parseFloat(avgSLO) >= 50 },
        { label: 'Workforce', value: `${wr.toFixed(0)}%`, positive: wr >= 50 },
      ],
    };
  }, [globalState, businessUnits, roundNumber, fmtCurrency]);

  if (!calc) return null;

  return (
    <div className={styles.terminalCalc}>
      <div className={styles.terminalCalcTitle}>
        <span>🏦</span>
        <span>LIVE TERMINAL VALUATION — Round {roundNumber}</span>
      </div>

      {/* Formula Display */}
      <div className={styles.terminalFormula}>
        TV = EBITDA × M<sub>R</sub> × EV Multiple
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

      {/* Total Terminal Value */}
      <div className={styles.terminalTotal}>
        <span className={styles.terminalTotalLabel}>📊 Est. Terminal Value</span>
        <span className={styles.terminalTotalValue}>
          {fmtCurrency(calc.terminalValue)}
        </span>
      </div>
    </div>
  );
}
