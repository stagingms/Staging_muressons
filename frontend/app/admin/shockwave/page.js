'use client';
import { useState, useEffect, useCallback } from 'react';

/**
 * Shockwave Control (Feature 6) — facilitator detonation console.
 * Pick a cohort + a crisis, then DETONATE: every team gets an identical
 * black-swan impact and a synchronized full-screen takeover. Gated server-side
 * by the caller's per-profile `shockwave_enabled` capability.
 */

const EVENTS = [
  { id: 'pandemic', label: '🦠 Global Pandemic', hit: '-$6.0M · -6 rep' },
  { id: 'carbon_tax', label: '🏭 Emergency Carbon Tax', hit: '-$5.0M · -3 rep' },
  { id: 'supply_collapse', label: '🚢 Supply-Chain Collapse', hit: '-$4.5M · -4 rep' },
  { id: 'cyber_attack', label: '💻 Coordinated Cyber Attack', hit: '-$4.0M · -7 rep' },
];

export default function ShockwaveControlPage() {
  const [cohorts, setCohorts] = useState([]);
  const [cohort, setCohort] = useState('');
  const [eventId, setEventId] = useState('pandemic');
  const [countdown, setCountdown] = useState(60);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // F-9 (v3): name the remedy — "signed out" and "backend down" are
    // different problems. (Target selection is deliberately untouched here;
    // the auto-select removal + blast-radius confirm are Phase S3 / F-1.)
    fetch('/api/admin/leaderboard', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status === 401 || r.status === 403 ? 'auth' : 'http'))))
      .then((d) => {
        const map = new Map();
        (d.leaderboard || []).forEach((x) => {
          const id = x.parent_cohort_id || (x.player_name ? null : x.session_id);
          if (id && !map.has(id)) map.set(id, x.cohort_name || id);
        });
        const list = [...map.entries()].map(([id, name]) => ({ id, name }));
        setCohorts(list);
        if (list[0]) setCohort(list[0].id);
      })
      .catch((e) => setError(e && e.message === 'auth'
        ? 'Signed out — sign in on the Facilitator Dashboard in another tab, then reload this console.'
        : 'Backend unreachable — cohorts could not be loaded. Check the server, then reload.'));
  }, []);

  const detonate = useCallback(() => {
    if (!cohort) return;
    setError(''); setResult(null);
    fetch(`/api/admin/${encodeURIComponent(cohort)}/shockwave`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_id: eventId, countdown: Number(countdown) || 60 }),
    })
      .then(async (r) => {
        if (r.status === 403) throw new Error('Shockwave is disabled for your facilitator profile.');
        if (!r.ok) throw new Error('Detonation failed.');
        return r.json();
      })
      .then((d) => setResult(d))
      .catch((e) => setError(e.message));
    setConfirming(false);
  }, [cohort, eventId, countdown]);

  return (
    <div style={S.page}>
      <div style={S.brand}>🌊 Shockwave Control</div>
      <div style={S.sub}>Detonate a synchronized crisis across every team in a cohort.</div>

      {error && <div style={S.error}>{error}</div>}
      {result && <div style={S.ok}>💥 Detonated <b>{result.event?.title}</b> — {result.teams_hit} team(s) hit.</div>}

      <label style={S.lbl}>Cohort</label>
      <select value={cohort} onChange={(e) => setCohort(e.target.value)} style={S.input}>
        {cohorts.length === 0 && <option value="">No cohorts found</option>}
        {cohorts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>

      <label style={S.lbl}>Crisis</label>
      <div style={S.grid}>
        {EVENTS.map((ev) => (
          <button key={ev.id} onClick={() => setEventId(ev.id)}
            style={{ ...S.card, ...(eventId === ev.id ? S.cardActive : {}) }}>
            <div style={{ fontWeight: 700 }}>{ev.label}</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>{ev.hit}</div>
          </button>
        ))}
      </div>

      <label style={S.lbl}>Countdown (seconds)</label>
      <input type="number" min="15" max="600" value={countdown}
        onChange={(e) => setCountdown(e.target.value)} style={{ ...S.input, width: 120 }} />

      <div style={{ marginTop: 24 }}>
        {!confirming ? (
          <button style={S.detonate} onClick={() => setConfirming(true)} disabled={!cohort}>🚨 Detonate Shockwave</button>
        ) : (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontWeight: 700 }}>Hit every team in this cohort?</span>
            <button style={S.detonate} onClick={detonate}>Yes — DETONATE</button>
            <button style={S.cancel} onClick={() => setConfirming(false)}>Cancel</button>
          </div>
        )}
      </div>
    </div>
  );
}

const S = {
  page: { maxWidth: 640, margin: '0 auto', padding: '32px 24px', color: 'var(--text-primary, #f1f5f9)', fontFamily: 'var(--font-sans, system-ui, sans-serif)' },
  brand: { fontSize: '1.8rem', fontWeight: 900 },
  sub: { color: 'var(--text-muted, #8899a6)', marginBottom: 24 },
  lbl: { display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted, #8899a6)', margin: '18px 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' },
  input: { width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border-subtle, rgba(148,163,184,0.25))', background: 'var(--bg-card, #161e2e)', color: 'inherit', fontSize: '0.95rem' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  card: { textAlign: 'left', padding: '12px 14px', borderRadius: 10, cursor: 'pointer', background: 'var(--bg-card, #161e2e)', border: '1px solid var(--border-subtle, rgba(148,163,184,0.2))', color: 'inherit' },
  cardActive: { border: '2px solid #ef4444', background: 'rgba(239,68,68,0.08)' },
  detonate: { padding: '14px 28px', fontSize: '1.05rem', fontWeight: 800, borderRadius: 12, border: 'none', cursor: 'pointer', background: 'linear-gradient(135deg, #ef4444, #b91c1c)', color: '#fff', boxShadow: '0 6px 24px rgba(239,68,68,0.4)' },
  cancel: { padding: '14px 20px', fontSize: '0.95rem', fontWeight: 700, borderRadius: 12, border: '1px solid var(--border-subtle, rgba(148,163,184,0.3))', cursor: 'pointer', background: 'transparent', color: 'inherit' },
  error: { padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5', marginBottom: 16, fontSize: '0.9rem' },
  ok: { padding: '10px 14px', borderRadius: 8, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.4)', color: '#6ee7b7', marginBottom: 16, fontSize: '0.9rem' },
};
