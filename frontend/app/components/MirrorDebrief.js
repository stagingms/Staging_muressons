/**
 * MirrorDebrief — WOW-3
 *
 * At game-over, shows the player's single highest-impact alternative decision
 * — the one change that would have most improved their terminal value.
 *
 * "Your biggest missed lever: If you had chosen Nature-Based Solutions (B)
 *  in Round 5 instead of Insurance Only (C), your M_R would have been ~X.XX
 *  higher and your terminal value ~$X.XM greater."
 *
 * SAFETY: Pure presentation. Reads existing data from the game-over payload
 * (flags, M_R, decision history) and the existing mrJourney utility.
 * No backend changes required — all computation is client-side using the
 * existing M_R flag dependency data already sent to the client.
 *
 * Props:
 *   mr             — actual regenerative multiple
 *   flags          — active_event_flags from globalState
 *   terminalValue  — actual terminal value in dollars
 *   decisionHistory — array of decision objects from round history
 */
'use client';
import React, { useMemo } from 'react';
import styles from './MirrorDebrief.module.css';
import { currencySymbol } from '../utils/format';

/**
 * M_R component catalog — maps flag keys to their M_R bonus value and
 * the round + option that would have earned them. Pulled from the game
 * design (terminal_valuation.py / SIMULATION_CONTEXT.md).
 */
const MR_OPPORTUNITIES = [
  {
    flag: 'materiality_governance',
    label: 'Materiality Governance',
    bonus: 0.10,
    round: 2,
    option: 'A',
    optionLabel: 'Double Materiality Framework',
    description: 'Establishes governance for tracking both financial and impact materiality',
  },
  {
    flag: 'social_license_rebuilt',
    label: 'Social License Rebuilt',
    bonus: 0.12,
    round: 3,
    option: 'A',
    optionLabel: 'Community Partnership Model',
    description: 'Rebuilds trust with affected communities through genuine partnership',
  },
  {
    flag: 'supply_chain_transparency',
    label: 'Supply Chain Transparency',
    bonus: 0.15,
    round: 4,
    option: 'A',
    optionLabel: 'Full Supply Chain Mapping',
    description: 'Creates complete Scope 3 visibility and supplier accountability',
  },
  {
    flag: 'resilience_investment',
    label: 'Resilience Champion',
    bonus: 0.20,
    round: 5,
    option: 'A',
    optionLabel: 'Hard Engineering Defence',
    description: 'Maximum physical climate resilience through infrastructure investment',
  },
  {
    flag: 'truth_premium',
    label: 'Truth Premium',
    bonus: 0.15,
    round: 6,
    option: 'A',
    optionLabel: 'Integrated Value Reporting',
    description: 'Transparent reporting builds investor trust and reduces risk premium',
  },
  {
    flag: 'just_transition_fund',
    label: 'Just Transition Fund',
    bonus: 0.10,
    round: 7,
    option: 'A',
    optionLabel: 'Worker Reskilling Programme',
    description: 'Funds a comprehensive transition programme for displaced workers',
  },
  {
    flag: 'circular_economy_leader',
    label: 'Circular Economy Leader',
    bonus: 0.12,
    round: 8,
    option: 'A',
    optionLabel: 'Circular Business Model',
    description: 'Transforms waste streams into revenue through circular design',
  },
  {
    flag: 'community_champion',
    label: 'Community Champion',
    bonus: 0.18,
    round: 9,
    option: 'A',
    optionLabel: 'Community Wealth Building',
    description: 'Creates shared prosperity with local communities and indigenous groups',
  },
];

export default function MirrorDebrief({ mr, flags = {}, terminalValue, decisionHistory = [] }) {
  const insight = useMemo(() => {
    if (!flags || typeof mr !== 'number') return null;

    // Find the biggest missed M_R bonus
    let biggestMiss = null;
    let biggestDelta = 0;

    for (const opp of MR_OPPORTUNITIES) {
      const earned = !!flags[opp.flag];
      if (!earned) {
        // This was missed — would it have been the biggest delta?
        if (opp.bonus > biggestDelta) {
          biggestDelta = opp.bonus;
          biggestMiss = opp;
        }
      }
    }

    if (!biggestMiss) return null; // Player earned everything!

    // Calculate what the improved M_R and terminal value would have been
    const improvedMR = mr + biggestMiss.bonus;
    const currentTV = terminalValue || 0;
    // Terminal value scales linearly with M_R (TV = base * M_R)
    const baseValue = mr > 0 ? currentTV / mr : 0;
    const improvedTV = baseValue * improvedMR;
    const tvDelta = improvedTV - currentTV;

    return {
      ...biggestMiss,
      improvedMR,
      currentMR: mr,
      mrDelta: biggestMiss.bonus,
      tvDelta,
      improvedTV,
    };
  }, [mr, flags, terminalValue]);

  if (!insight) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.icon}>🪞</span>
        <span className={styles.title}>The Mirror Debrief</span>
        <span className={styles.subtitle}>Your single biggest missed lever</span>
      </div>

      <div className={styles.card}>
        <div className={styles.roundBadge}>Round {insight.round}</div>

        <div className={styles.insightText}>
          If you had chosen <strong>{insight.optionLabel}</strong> (Option {insight.option})
          in Round {insight.round}, you would have earned the{' '}
          <span className={styles.highlight}>+{insight.bonus.toFixed(2)} {insight.label}</span>{' '}
          M<sub>R</sub> bonus.
        </div>

        <div className={styles.comparison}>
          <div className={styles.compActual}>
            <div className={styles.compLabel}>Your M<sub>R</sub></div>
            <div className={styles.compValue}>{insight.currentMR.toFixed(2)}×</div>
          </div>
          <div className={styles.compArrow}>→</div>
          <div className={styles.compAlternative}>
            <div className={styles.compLabel}>Would have been</div>
            <div className={styles.compValue}>{insight.improvedMR.toFixed(2)}×</div>
            <div className={styles.compDelta}>+{insight.mrDelta.toFixed(2)}</div>
          </div>
        </div>

        {insight.tvDelta > 0 && (
          <div className={styles.tvImpact}>
            Terminal value impact: <strong>+{currencySymbol()}{(insight.tvDelta / 1_000_000).toFixed(1)}M</strong>
          </div>
        )}

        <div className={styles.description}>
          💡 {insight.description}
        </div>
      </div>
    </div>
  );
}
