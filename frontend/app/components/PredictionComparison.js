'use client';
import React, { useMemo } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * PredictionComparison — Phase 3.4
 * Compares player's pre-commit predictions (from PredictionGate)
 * with actual outcomes after results are in.
 *
 * Shows a split-column view: "What You Predicted" vs "What Actually Happened"
 * with a calibration score indicating metacognitive accuracy.
 *
 * Appears in the results overlay only when predictions were submitted.
 *
 * Props:
 *   - predictions:    array of { round, prediction, choice_selected }
 *   - roundNumber:    current round
 *   - commitResults:  results from the committed turn
 *   - globalState:    current global state  
 */

export default function PredictionComparison({
  predictions,
  roundNumber,
  commitResults,
  globalState,
}) {
  const comparison = useMemo(() => {
    if (!predictions?.length || !commitResults) return null;

    // Find the prediction for this round
    const pred = predictions.find(p => p.round === roundNumber);
    if (!pred?.prediction) return null;

    // Build the "actual" summary from commit results
    const ev = commitResults.events || {};
    const gs = commitResults.globalState || {};
    const actualParts = [];

    if (gs.corporate_treasury !== undefined && globalState?.corporate_treasury !== undefined) {
      const delta = gs.corporate_treasury - globalState.corporate_treasury;
      actualParts.push(`Treasury ${delta >= 0 ? '+' : ''}$${(delta / 1e6).toFixed(1)}M`);
    }
    if (gs.group_reputation !== undefined && globalState?.group_reputation !== undefined) {
      const delta = gs.group_reputation - globalState.group_reputation;
      actualParts.push(`Reputation ${delta >= 0 ? '+' : ''}${delta.toFixed(0)}`);
    }
    if (ev.summary || ev.narrative_summary) {
      actualParts.push(ev.summary || ev.narrative_summary);
    }

    const actualText = actualParts.join('. ') || 'Results processed — see KPI changes above.';

    // Simple calibration: compare prediction sentiment with outcome direction
    const predLower = pred.prediction.toLowerCase();
    const isOptimistic = predLower.includes('increase') || predLower.includes('improve') || predLower.includes('gain') || predLower.includes('positive');
    const isPessimistic = predLower.includes('decrease') || predLower.includes('worse') || predLower.includes('lose') || predLower.includes('negative') || predLower.includes('risk');
    
    const treasuryDelta = (gs.corporate_treasury || 0) - (globalState?.corporate_treasury || 0);
    const repDelta = (gs.group_reputation || 0) - (globalState?.group_reputation || 0);
    const outcomePositive = treasuryDelta > 0 && repDelta >= 0;
    const outcomeNegative = treasuryDelta < -500000 || repDelta < -3;

    let calibration = 'medium';
    if ((isOptimistic && outcomePositive) || (isPessimistic && outcomeNegative)) {
      calibration = 'high';
    } else if ((isOptimistic && outcomeNegative) || (isPessimistic && outcomePositive)) {
      calibration = 'low';
    }

    return {
      prediction: pred.prediction,
      actual: actualText,
      calibration,
      calibrationLabel: calibration === 'high' ? '✅ Well Calibrated' : calibration === 'low' ? '❌ Miscalibrated' : '⚖️ Partially Aligned',
    };
  }, [predictions, roundNumber, commitResults, globalState]);

  if (!comparison) return null;

  return (
    <div className={styles.predictionComparison}>
      <div className={styles.predictionComparisonTitle}>
        <span>🔮</span>
        <span>PREDICTION vs. REALITY</span>
      </div>

      <div className={styles.predictionColumns}>
        <div className={`${styles.predictionColumn} ${styles.predictionColumnPredicted}`}>
          <div className={styles.predictionColumnLabel}>📝 What You Predicted</div>
          {comparison.prediction}
        </div>
        <div className={`${styles.predictionColumn} ${styles.predictionColumnActual}`}>
          <div className={styles.predictionColumnLabel}>📊 What Actually Happened</div>
          {comparison.actual}
        </div>
      </div>

      <div className={`${styles.calibrationScore} ${
        comparison.calibration === 'high' ? styles.calibrationHigh :
        comparison.calibration === 'low' ? styles.calibrationLow :
        styles.calibrationMedium
      }`}>
        {comparison.calibrationLabel}
      </div>
    </div>
  );
}
