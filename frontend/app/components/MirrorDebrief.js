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
import { currencySymbol, atRate } from '../utils/format';

// F-15 (audit 2026-09-04): the catalogue used to be a private table of eight
// flag names, none of which is a top-level key for any real player (and four
// of which no writer sets at all), so "your biggest missed lever" was always
// Resilience +0.20 — told to players whose finale had awarded resilience_bonus
// 0.20. The single shared table in utils/mrJourney now decides, reading the
// arbiter's mr_breakdown when the finale has run.
import { computeMrRegret } from '../utils/mrJourney';

export default function MirrorDebrief({ mr, flags = {}, terminalValue, decisionHistory = [] }) {
  const insight = useMemo(() => {
    if (!flags || typeof mr !== 'number') return null;

    // Find the biggest missed M_R component, as the arbiter scores it
    const { missed } = computeMrRegret(flags);
    let biggestMiss = null;
    for (const opp of missed) {
      if (!biggestMiss || opp.nominalMr > biggestMiss.mr) biggestMiss = { ...opp, mr: opp.nominalMr, bonus: opp.nominalMr };
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
            Terminal value impact: <strong>+{currencySymbol()}{atRate(insight.tvDelta / 1_000_000).toFixed(1)}M</strong>
          </div>
        )}

        <div className={styles.description}>
          💡 {insight.description}
        </div>
      </div>
    </div>
  );
}
