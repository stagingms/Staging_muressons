'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { playerIdHeader } from '../hooks/useSimulation';

/**
 * CalibrationReport — game-over calibration curve + Overconfidence Index
 * (PLAN_Calibration_Analytics Phase 3).
 *
 * Slot: results stage (game-over view, mounted inside GameOverSummary) — V-A:
 * retrospective content only; renders nothing mid-game and nothing at all if
 * the player never submitted a scored prediction.
 *
 * Reads the server-side predictions log (scored post-tick). Confidence buckets
 * 50–60 … 90–100 vs realised hit-rate; the diagonal is perfect calibration.
 * Overconfidence Index = mean confidence − mean hit-rate (positive = cocky,
 * negative = underconfident, |x| ≤ 0.1 ≈ well calibrated).
 */

export default function CalibrationReport({ sessionId }) {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${API}/api/simulations/${sessionId}/predictions`, { headers: { ...playerIdHeader() } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setRecords((d && d.predictions) || []))
      .catch(() => {});
  }, [sessionId]);

  const view = useMemo(() => {
    const scored = records.filter((p) => p.score && p.score.of > 0);
    if (!scored.length) return null;

    const perRound = scored
      .map((p) => ({ round: p.round, hitRate: p.score.hits / p.score.of, conf: typeof p.confidence === 'number' ? p.confidence : null }))
      .sort((a, b) => a.round - b.round);

    const withConf = perRound.filter((r) => r.conf != null);
    let overconfidence = null;
    let buckets = null;
    if (withConf.length >= 2) {
      const meanConf = withConf.reduce((s, r) => s + r.conf, 0) / withConf.length;
      const meanHit = withConf.reduce((s, r) => s + r.hitRate, 0) / withConf.length;
      overconfidence = meanConf - meanHit;
      buckets = [[0.5, 0.6], [0.6, 0.7], [0.7, 0.8], [0.8, 0.9], [0.9, 1.001]].map(([lo, hi]) => {
        const rs = withConf.filter((r) => r.conf >= lo && r.conf < hi);
        return rs.length
          ? { mid: (lo + Math.min(hi, 1)) / 2, hitRate: rs.reduce((s, r) => s + r.hitRate, 0) / rs.length, n: rs.length }
          : null;
      }).filter(Boolean);
    }

    const totalHits = scored.reduce((s, p) => s + p.score.hits, 0);
    const totalOf = scored.reduce((s, p) => s + p.score.of, 0);
    return { perRound, buckets, overconfidence, totalHits, totalOf, rounds: scored.length };
  }, [records]);

  if (!view) return null;

  // ── Calibration curve SVG (only when confidence data exists) ──
  const W = 340, H = 220, padL = 44, padB = 34, padT = 16, padR = 12;
  const iw = W - padL - padR, ih = H - padT - padB;
  const xOf = (c) => padL + ((c - 0.5) / 0.5) * iw;   // confidence 0.5–1.0
  const yOf = (h) => padT + (1 - h) * ih;             // hit rate 0–1

  const ociWord = view.overconfidence == null ? null
    : view.overconfidence > 0.1 ? 'overconfident'
    : view.overconfidence < -0.1 ? 'underconfident'
    : 'well calibrated';
  const ociColor = ociWord === 'well calibrated' ? '#34d399' : ociWord === 'overconfident' ? '#f87171' : '#fbbf24';

  return (
    <div style={{
      marginTop: 16, padding: '16px 18px', borderRadius: 12, textAlign: 'left',
      background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.25)',
    }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#a5b4fc', marginBottom: 4 }}>
        🎯 Your Calibration — did your mental model improve?
      </div>
      <div style={{ fontSize: '0.82rem', color: '#cbd5e1', marginBottom: 10 }}>
        Across {view.rounds} predicted round{view.rounds === 1 ? '' : 's'} you made {view.totalHits} of {view.totalOf} calls correctly
        {view.overconfidence != null && (
          <> · Overconfidence Index <strong style={{ color: ociColor }}>
            {view.overconfidence >= 0 ? '+' : ''}{Math.round(view.overconfidence * 100)} pts ({ociWord})
          </strong></>
        )}.
      </div>

      {view.buckets && view.buckets.length >= 1 && (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: 420, display: 'block' }} aria-label="Calibration curve">
          {/* axes */}
          <line x1={padL} y1={yOf(0)} x2={W - padR} y2={yOf(0)} stroke="rgba(148,163,184,0.4)" />
          <line x1={padL} y1={yOf(0)} x2={padL} y2={padT} stroke="rgba(148,163,184,0.4)" />
          {[0, 0.5, 1].map((h) => (
            <text key={h} x={padL - 6} y={yOf(h) + 3} textAnchor="end" fontSize="9" fill="#8899a6">{Math.round(h * 100)}%</text>
          ))}
          {[0.5, 0.75, 1].map((c) => (
            <text key={c} x={xOf(c)} y={H - padB + 14} textAnchor="middle" fontSize="9" fill="#8899a6">{Math.round(c * 100)}%</text>
          ))}
          <text x={padL + iw / 2} y={H - 6} textAnchor="middle" fontSize="9" fill="#64748b">stated confidence</text>
          <text x={12} y={padT + ih / 2} textAnchor="middle" fontSize="9" fill="#64748b" transform={`rotate(-90 12 ${padT + ih / 2})`}>actual hit-rate</text>
          {/* perfect-calibration diagonal */}
          <line x1={xOf(0.5)} y1={yOf(0.5)} x2={xOf(1)} y2={yOf(1)} stroke="rgba(52,211,153,0.55)" strokeDasharray="4 4" />
          <text x={xOf(0.97)} y={yOf(1) + 12} textAnchor="end" fontSize="8.5" fill="#34d399">perfect calibration</text>
          {/* observed buckets */}
          {view.buckets.length > 1 && (
            <path
              d={view.buckets.map((b, i) => `${i === 0 ? 'M' : 'L'}${xOf(b.mid).toFixed(1)},${yOf(b.hitRate).toFixed(1)}`).join(' ')}
              fill="none" stroke="#a5b4fc" strokeWidth="2"
            />
          )}
          {view.buckets.map((b) => (
            <g key={b.mid}>
              <circle cx={xOf(b.mid)} cy={yOf(b.hitRate)} r="4.5" fill="#a5b4fc" />
              <text x={xOf(b.mid)} y={yOf(b.hitRate) - 8} textAnchor="middle" fontSize="8.5" fill="#cbd5e1">n={b.n}</text>
            </g>
          ))}
        </svg>
      )}

      {/* Round-by-round trend — does the cohort's model sharpen? */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
        {view.perRound.map((r) => (
          <span key={r.round} style={{
            fontSize: '0.68rem', fontWeight: 700, padding: '3px 8px', borderRadius: 999,
            background: r.hitRate === 1 ? 'rgba(52,211,153,0.15)' : r.hitRate === 0 ? 'rgba(248,113,113,0.14)' : 'rgba(251,191,36,0.14)',
            color: r.hitRate === 1 ? '#34d399' : r.hitRate === 0 ? '#f87171' : '#fbbf24',
          }}>
            R{r.round}: {Math.round(r.hitRate * 100)}%{r.conf != null ? ` @ ${Math.round(r.conf * 100)}%` : ''}
          </span>
        ))}
      </div>
      <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: 8, fontStyle: 'italic' }}>
        Calibration — knowing how much to trust your own forecasts — is a leadership skill this simulation measures directly. A well-calibrated pessimist scores as well as a well-calibrated optimist.
      </div>
    </div>
  );
}
