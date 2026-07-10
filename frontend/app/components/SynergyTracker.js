'use client';
import React, { useMemo } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * SynergyTracker — Phase 3.6
 * Persistent widget showing current synergy score vs R10 threshold.
 * Appears from Round 7 onwards (Integration tier) above the commit button.
 *
 * Props:
 *   - globalState:     current global state
 *   - roundNumber:     current round
 *   - workforceReady:  workforce readiness score
 */

const R10_SYNERGY_THRESHOLD = 80;

export default function SynergyTracker({ globalState, roundNumber, workforceReady }) {
  const synergy = useMemo(() => {
    if (roundNumber < 7) return null;
    const score = globalState?.synergy_multiplier || globalState?.synergy_score || 0;
    // Normalize: synergy_multiplier is typically 0.8–1.5, but synergy_score may be 0–100
    const normalizedScore = score > 10 ? score : score * 100;
    const isUnlocked = normalizedScore >= R10_SYNERGY_THRESHOLD;
    const pct = Math.min(100, (normalizedScore / R10_SYNERGY_THRESHOLD) * 100);

    return {
      score: normalizedScore.toFixed(0),
      rawMultiplier: score < 10 ? score.toFixed(2) : (score / 100).toFixed(2),
      isUnlocked,
      pct,
      workforceReady: workforceReady || globalState?.workforce_readiness || 50,
      wrModifier: (workforceReady || globalState?.workforce_readiness || 50) < 40
        ? '⚠️ -30% (readiness < 40)'
        : (workforceReady || globalState?.workforce_readiness || 50) >= 60
          ? '✅ +10% (readiness ≥ 60)'
          : '— (neutral)',
    };
  }, [globalState, roundNumber, workforceReady]);

  if (!synergy) return null;

  return (
    <div className={`${styles.synergyTracker} ${
      synergy.isUnlocked ? styles.synergyTrackerUnlocked : styles.synergyTrackerLocked
    }`}>
      {/* Label */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 80 }}>
        <span className={styles.synergyLabel}>
          {synergy.isUnlocked ? '🔓' : '🔒'} Synergy
        </span>
        <span className={styles.synergyValue} style={{
          color: synergy.isUnlocked ? '#4ade80' : '#f87171',
        }}>
          {synergy.rawMultiplier}×
        </span>
      </div>

      {/* Progress Bar */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
        <div className={styles.synergyBar}>
          <div
            className={styles.synergyBarFill}
            style={{
              width: `${synergy.pct}%`,
              background: synergy.isUnlocked
                ? 'linear-gradient(90deg, #4ade80, #10b981)'
                : 'linear-gradient(90deg, #f87171, #ef4444)',
            }}
          />
          {/* R10 Threshold marker */}
          <div className={styles.synergyBarThreshold} style={{ left: '100%' }}
            title="R10 Threshold"
          />
        </div>
        <div style={{
          fontSize: '0.65rem', color: '#64748b',
          display: 'flex', justifyContent: 'space-between',
        }}>
          <span>WR: {synergy.wrModifier}</span>
          <span>{synergy.isUnlocked ? '✅ R10 Option A unlocked' : `Need ≥ ${R10_SYNERGY_THRESHOLD} for R10 Option A`}</span>
        </div>
      </div>
    </div>
  );
}
