'use client';
import { useState } from 'react';

/**
 * DryRunSimulator — facilitator pre-flight check (tab: dry_run).
 *
 * "Fly the cohort before the class does": POSTs /api/admin/dry-run, which
 * plays four bot strategies headlessly through the REAL engine from the
 * selected cohort's current state to Round 10 (seeded repetitions, medians),
 * without touching the cohort. Renders the difficulty grade, per-strategy
 * cards with treasury sparklines, the crisis-bite table, and config warnings.
 *
 * Props: sessionId (the currently selected cohort), cohortName.
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';

const GRADE_META = {
  forgiving: { color: '#38bdf8', blurb: 'Even ESG neglect survives comfortably — consider turning the pressure up.' },
  balanced:  { color: '#34d399', blurb: 'Strategies differentiate and most survive — a healthy teaching configuration.' },
  punishing: { color: '#fbbf24', blurb: 'Half or more of the strategies tend to bankrupt — fine for experienced cohorts, harsh for novices.' },
  brutal:    { color: '#f87171', blurb: 'Every strategy tends to bankrupt — expect a demoralised classroom unless that is the lesson.' },
};

const fmtM = (v) => (v == null ? '—' : `${v < 0 ? '−' : ''}$${Math.abs(v / 1e6) >= 100 ? Math.abs(v / 1e6).toFixed(0) : Math.abs(v / 1e6).toFixed(1)}M`);

function Sparkline({ values = [], rounds = [], w = 220, h = 56 }) {
  const pts = values.map((v, i) => ({ v, r: rounds[i] })).filter((p) => p.v != null);
  if (pts.length < 2) return null;
  const min = Math.min(0, ...pts.map((p) => p.v));
  const max = Math.max(0, ...pts.map((p) => p.v));
  const span = max - min || 1;
  const x = (i) => (i / (pts.length - 1)) * (w - 8) + 4;
  const y = (v) => 6 + (1 - (v - min) / span) * (h - 16);
  const zero = y(0);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: h }} aria-label="Median treasury by round">
      <line x1="4" y1={zero} x2={w - 4} y2={zero} stroke="rgba(148,163,184,0.35)" strokeDasharray="3 3" />
      <path
        d={pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join(' ')}
        fill="none" stroke="#818cf8" strokeWidth="2"
      />
      {pts.map((p, i) => (
        <circle key={i} cx={x(i)} cy={y(p.v)} r="2.4" fill={p.v < 0 ? '#f87171' : '#818cf8'}>
          <title>R{p.r}: {fmtM(p.v)}</title>
        </circle>
      ))}
    </svg>
  );
}

export default function DryRunSimulator({ sessionId, cohortName = '' }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reps, setReps] = useState(3);

  const fly = async () => {
    if (!sessionId) { setError('Select a cohort first (top bar), then run the pre-flight.'); return; }
    setLoading(true); setError(''); setReport(null);
    try {
      const r = await fetch(`${API}/api/admin/dry-run`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, n_reps: reps }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `Dry run failed (${r.status})`);
      }
      setReport(await r.json());
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const gm = report ? (GRADE_META[report.difficulty_grade] || GRADE_META.balanced) : null;

  return (
    <div style={{ color: 'var(--text-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 6 }}>
        <span style={{ fontSize: '1.6rem' }}>🛫</span>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.15rem' }}>Dry-Run Simulator</h2>
          <div style={{ fontSize: '0.78rem', color: '#8899a6' }}>
            Four bot boards play {cohortName ? `“${cohortName}”` : 'the selected cohort'} through the real engine to Round 10 —
            your cohort&apos;s actual state is never touched.
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <label style={{ fontSize: 'var(--type-caption)', color: '#8899a6' }}>
            Reps/strategy{' '}
            <select value={reps} onChange={(e) => setReps(Number(e.target.value))}
              style={{ background: 'transparent', color: 'inherit', border: '1px solid rgba(148,163,184,0.3)', borderRadius: 6, padding: '3px 6px' }}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n} style={{ color: '#000' }}>{n}</option>)}
            </select>
          </label>
          <button onClick={fly} disabled={loading}
            style={{ padding: '8px 18px', borderRadius: 8, fontWeight: 800, fontSize: '0.82rem', cursor: 'pointer',
                     border: '1px solid rgba(99,102,241,0.6)', background: 'rgba(99,102,241,0.2)', color: 'inherit' }}>
            {loading ? '⏳ Flying…' : '🛫 Run pre-flight'}
          </button>
        </div>
      </div>

      {error && <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(248,113,113,0.12)', border: '1px solid rgba(248,113,113,0.4)', fontSize: '0.8rem', marginTop: 10 }}>{error}</div>}

      {report && (
        <>
          {/* Grade banner */}
          <div style={{ marginTop: 14, padding: '12px 16px', borderRadius: 10, border: `1px solid ${gm.color}55`, background: `${gm.color}14`, display: 'flex', gap: 12, alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: 900, color: gm.color, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Difficulty: {report.difficulty_grade}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>{gm.blurb}</span>
            <span style={{ marginLeft: 'auto', fontSize: 'var(--type-caption)', color: '#8899a6' }}>
              R{report.start_round}→R{report.end_round} · {report.n_reps} rep{report.n_reps > 1 ? 's' : ''}/strategy · medians
            </span>
          </div>

          {/* Warnings */}
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {report.warnings.map((w, i) => (
              <div key={i} style={{ fontSize: '0.78rem', color: '#fbbf24', padding: '6px 10px', borderRadius: 8, background: 'rgba(251,191,36,0.07)', borderLeft: '3px solid rgba(251,191,36,0.5)' }}>
                ⚠ {w}
              </div>
            ))}
          </div>

          {/* Strategy cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 12, marginTop: 14 }}>
            {Object.entries(report.strategies).map(([sid, s]) => (
              <div key={sid} style={{ padding: '12px 14px', borderRadius: 10, background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.18)' }}>
                <div style={{ fontWeight: 800, fontSize: '0.88rem', marginBottom: 6 }}>{s.label}</div>
                <Sparkline values={s.treasury_by_round} rounds={report.rounds_axis} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 10px', fontSize: 'var(--type-caption)', color: '#cbd5e1', marginTop: 6 }}>
                  <span>Bankruptcy risk</span>
                  <strong style={{ color: s.bankruptcy_risk >= 0.5 ? '#f87171' : s.bankruptcy_risk > 0 ? '#fbbf24' : '#34d399', textAlign: 'right' }}>
                    {Math.round(s.bankruptcy_risk * 100)}%{s.first_bankrupt_round ? ` (≈R${Math.round(s.first_bankrupt_round)})` : ''}
                  </strong>
                  <span>Final treasury</span><strong style={{ textAlign: 'right', color: (s.final_treasury_median || 0) < 0 ? '#f87171' : '#e2e8f0' }}>{fmtM(s.final_treasury_median)}</strong>
                  <span>Final reputation</span><strong style={{ textAlign: 'right' }}>{s.final_reputation_median ?? '—'}/100</strong>
                  <span>Lowest SLO seen</span><strong style={{ textAlign: 'right' }}>{s.min_slo ?? '—'}</strong>
                  <span>Peak stakeholder heat</span>
                  <strong style={{ textAlign: 'right' }}>{['calm', 'watchful', 'concerned', 'critical', 'hostile', 'on strike'][s.escalation_peak] || s.escalation_peak}</strong>
                </div>
              </div>
            ))}
          </div>

          {/* Crisis bite */}
          {report.crisis_bite?.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#8899a6', marginBottom: 6 }}>
                Which rounds bite hardest (median Δ across all bots)
              </div>
              {report.crisis_bite.map((cb) => (
                <div key={cb.round} style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: '0.78rem', padding: '3px 0', color: '#cbd5e1' }}>
                  <span style={{ width: 30, color: '#8899a6' }}>R{cb.round}</span>
                  <span style={{ flex: 1 }}>{cb.name}</span>
                  <span style={{ width: 90, textAlign: 'right', fontWeight: 700, color: (cb.median_treasury_delta || 0) < 0 ? '#f87171' : '#34d399' }}>{fmtM(cb.median_treasury_delta)}</span>
                  <span style={{ width: 60, textAlign: 'right', color: (cb.median_reputation_delta || 0) < 0 ? '#f87171' : '#34d399' }}>
                    {cb.median_reputation_delta > 0 ? '+' : ''}{cb.median_reputation_delta ?? '—'} rep
                  </span>
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: 12, fontSize: 'var(--type-caption)', color: '#64748b', fontStyle: 'italic' }}>
            {report.notes?.map((n, i) => <div key={i}>· {n}</div>)}
          </div>
        </>
      )}

      {!report && !loading && !error && (
        <div style={{ marginTop: 20, fontSize: '0.82rem', color: '#8899a6' }}>
          Select a cohort in the top bar, choose repetitions, and run the pre-flight. Typical run time: under a second.
        </div>
      )}
    </div>
  );
}
