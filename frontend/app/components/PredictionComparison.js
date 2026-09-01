'use client';
import React, { useMemo } from 'react';
import { currencySymbol, atRate, localiseAuthored } from '../utils/format';

/**
 * PredictionComparison — calibration chip (PLAN_Calibration_Analytics Phase 3).
 *
 * Slot: results stage (inside the existing commit-results overlay) — V-A:
 * retrospective content renders after the round resolves, never mid-decision.
 *
 * Renders the round's SCORED prediction from the server-side predictions log
 * (predictions_log, scored post-tick by the backend). Replaces the old
 * sessionStorage + keyword-sentiment version. Deterministic band scoring:
 * exact band match = hit; Brier = (confidence − hit)², honest confidence wins.
 *
 * Props:
 *   - predictions: array of server records { round, treasury_band,
 *       reputation_dir, confidence, note, score }
 *   - roundNumber: the round whose results are on screen
 */

/* localiseAuthored rather than moneyM() at each bound: the author wrote the
   range with ONE glyph and a shared suffix ('$1-5M', not '$1M-$5M'), and that
   compact form is what fits the column. The transform preserves it. */
const BAND_LABEL = {
  down_big: '▼▼ >$5M drop', down: '▼ $1–5M drop', flat: '≈ flat',
  up: '▲ $1–5M gain', up_big: '▲▲ >$5M gain',
};
const DIR_LABEL = { down: '▼ falls', flat: '≈ flat', up: '▲ rises' };

export default function PredictionComparison({ predictions, roundNumber }) {
  const view = useMemo(() => {
    const pred = (predictions || []).find((p) => p.round === roundNumber && p.score);
    if (!pred) return null;
    const s = pred.score;
    const rows = [];
    if (pred.treasury_band) {
      rows.push({
        kpi: '💰 Treasury',
        predicted: localiseAuthored(BAND_LABEL[pred.treasury_band] || pred.treasury_band),
        actual: `${localiseAuthored(BAND_LABEL[s.actual_treasury_band] || s.actual_treasury_band)} (${s.treasury_delta >= 0 ? '+' : ''}${currencySymbol()}${atRate(s.treasury_delta / 1e6).toFixed(1)}M)`,
        hit: s.treasury_hit,
      });
    }
    if (pred.reputation_dir) {
      rows.push({
        kpi: '⭐ Reputation',
        predicted: DIR_LABEL[pred.reputation_dir] || pred.reputation_dir,
        actual: `${DIR_LABEL[s.actual_reputation_dir] || s.actual_reputation_dir} (${s.reputation_delta >= 0 ? '+' : ''}${Number(s.reputation_delta).toFixed(1)})`,
        hit: s.reputation_hit,
      });
    }
    if (!rows.length) return null;
    let verdict = `${s.hits} of ${s.of} calls right`;
    const verdictTone = s.hits === s.of ? '#34d399' : s.hits === 0 ? '#f87171' : '#fbbf24';
    let confLine = null;
    if (typeof pred.confidence === 'number' && s.brier != null) {
      const hitRate = s.of ? s.hits / s.of : 0;
      const gap = pred.confidence - hitRate;
      confLine =
        gap > 0.2 ? `You were more confident (${Math.round(pred.confidence * 100)}%) than accurate this round — worth noticing.`
        : gap < -0.2 ? `You were more accurate than your ${Math.round(pred.confidence * 100)}% confidence suggested — trust your model a little more.`
        : `Well calibrated: ${Math.round(pred.confidence * 100)}% confident, ${Math.round(hitRate * 100)}% right.`;
      verdict += ` · Brier ${s.brier.toFixed(2)}`;
    }
    return { rows, verdict, verdictTone, confLine, note: pred.note };
  }, [predictions, roundNumber]);

  if (!view) return null;

  return (
    <div style={{
      marginTop: 12, padding: '12px 14px', borderRadius: 10,
      background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.25)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8, gap: 10, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#a5b4fc' }}>
          🔮 Your Prediction vs Reality
        </span>
        <span style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: view.verdictTone }}>{view.verdict}</span>
      </div>
      {view.rows.map((r) => (
        <div key={r.kpi} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: '0.76rem', color: '#cbd5e1', padding: '3px 0', flexWrap: 'wrap' }}>
          <span style={{ width: 96, flexShrink: 0 }}>{r.kpi}</span>
          <span style={{ color: '#94a3b8' }}>you: <strong style={{ color: '#e2e8f0' }}>{r.predicted}</strong></span>
          <span style={{ color: '#64748b' }}>→</span>
          <span style={{ color: '#94a3b8' }}>actual: <strong style={{ color: '#e2e8f0' }}>{r.actual}</strong></span>
          <span style={{ marginLeft: 'auto' }}>{r.hit ? '✅' : '❌'}</span>
        </div>
      ))}
      {view.confLine && (
        <div style={{ fontSize: 'var(--type-caption)', color: '#a5b4fc', marginTop: 6, fontStyle: 'italic' }}>{view.confLine}</div>
      )}
      {view.note && (
        <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginTop: 6 }}>
          Your reasoning at the time: “{view.note}”
        </div>
      )}
    </div>
  );
}
