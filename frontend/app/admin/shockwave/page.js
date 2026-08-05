'use client';
import { useState, useEffect, useCallback } from 'react';
import { SHOCKWAVE_EVENTS, fmtHit } from '../../components/shockwaveCatalog';
import { useConfirm } from '../../components/ConfirmModal';

/**
 * Shockwave Control (Feature 6) — facilitator detonation console.
 * Pick a cohort + a crisis, then DETONATE: every team gets an identical
 * black-swan impact and a synchronized full-screen takeover. Gated server-side
 * by the caller's per-profile `shockwave_enabled` capability.
 *
 * F-1 (v3): no target is ever chosen FOR you. The old console silently
 * pre-selected the first cohort the leaderboard returned — the wrong-cohort
 * defect class v1's F2 removed from RoundPacingControl, reborn on the most
 * destructive control. Now: unset until you choose (dashboard selection is
 * offered as a VISIBLE prefill, never a silent one), and detonation goes
 * through the platform's tier-2 impact-preview confirm naming the cohort,
 * its team count, and the per-team hit. The request payload is byte-identical
 * to before; Cancel sends nothing.
 */

export default function ShockwaveControlPage() {
  const [cohorts, setCohorts] = useState([]);       // [{ id, name, teams, round }]
  const [cohort, setCohort] = useState('');
  const [prefilled, setPrefilled] = useState(false); // target came from dashboard selection
  const [eventId, setEventId] = useState('pandemic');
  const [countdown, setCountdown] = useState(60);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [confirmAction, confirmModal] = useConfirm();
  // S4 / F-2 (v3): rehearsal mode — the server-side safety feature (WOW-4E)
  // that was fully dark: no frontend ever sent the documented `rehearsal:true`
  // flag. Same endpoint, one extra body field; the server guarantees NO game
  // state changes and NO student broadcast (proven in the S0 baseline capture:
  // player KPIs byte-identical before/after; audit-logged as
  // `shockwave_rehearsal`). This is the ONLY new request variant in v3.
  const [rehearsal, setRehearsal] = useState(null); // response of a rehearsal run
  const [rehearsing, setRehearsing] = useState(false);
  // G-3 proper (v3/S5): prefer the ENGINE's catalog over the local copy.
  // Feature-detected — on any failure (older backend, network) the local
  // shockwaveCatalog stays in force, itself guarded by the drift-tripwire
  // jest test. Frontend emoji labels are kept by id; unknown ids fall back
  // to the server title.
  const [events, setEvents] = useState(SHOCKWAVE_EVENTS);
  useEffect(() => {
    fetch('/api/admin/shockwave/events', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d || !Array.isArray(d.events) || d.events.length === 0) return;
        setEvents(d.events.map((ev) => ({
          id: ev.id,
          label: SHOCKWAVE_EVENTS.find((x) => x.id === ev.id)?.label || ev.title || ev.id,
          financial_impact: Number(ev.financial_impact) || 0,
          reputation_impact: Number(ev.reputation_impact) || 0,
        })));
      })
      .catch(() => { /* keep the local catalog */ });
  }, []);
  // Keep the selected crisis valid if the server catalog differs.
  useEffect(() => {
    if (events.length && !events.some((e) => e.id === eventId)) setEventId(events[0].id);
  }, [events, eventId]);

  useEffect(() => {
    // F-9 (v3): name the remedy — "signed out" and "backend down" are
    // different problems. (Target selection is deliberately untouched here;
    // the auto-select removal + blast-radius confirm are Phase S3 / F-1.)
    fetch('/api/admin/leaderboard', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status === 401 || r.status === 403 ? 'auth' : 'http'))))
      .then((d) => {
        // F-1: keep team counts and rounds — the confirm's blast radius is
        // computed from the same payload the board already fetched.
        const map = new Map();
        (d.leaderboard || []).forEach((x) => {
          const id = x.parent_cohort_id || (x.player_name ? null : x.session_id);
          if (!id) return;
          if (!map.has(id)) map.set(id, { id, name: x.cohort_name || id, teams: 0, round: 1 });
          const e = map.get(id);
          if (x.cohort_name) e.name = x.cohort_name;
          if (x.parent_cohort_id === id) e.teams += 1;                       // player sub-session
          else if (x.session_id === id) e.round = x.round_number || 1;       // the cohort row itself
        });
        const list = [...map.values()];
        setCohorts(list);
        // F-1: NO auto-select. The dashboard's cohort selection is offered as
        // a visible, labeled prefill; anything else stays "choose a cohort".
        try {
          const sel = localStorage.getItem('fac_selected_session');
          if (sel && map.has(sel)) { setCohort(sel); setPrefilled(true); }
        } catch { /* ignore */ }
      })
      .catch((e) => setError(e && e.message === 'auth'
        ? 'Signed out — sign in on the Facilitator Dashboard in another tab, then reload this console.'
        : 'Backend unreachable — cohorts could not be loaded. Check the server, then reload.'));
  }, []);

  const rehearse = useCallback(() => {
    if (!cohort || rehearsing) return;
    setError(''); setResult(null); setRehearsal(null); setRehearsing(true);
    fetch(`/api/admin/${encodeURIComponent(cohort)}/shockwave`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_id: eventId, countdown: Number(countdown) || 60, rehearsal: true }),
    })
      .then(async (r) => {
        if (r.status === 403) throw new Error('Shockwave is disabled for your facilitator profile.');
        if (!r.ok) throw new Error('Rehearsal failed.');
        return r.json();
      })
      .then((d) => setRehearsal(d))
      .catch((e) => setError(e.message))
      .finally(() => setRehearsing(false));
  }, [cohort, eventId, countdown, rehearsing]);

  const detonate = useCallback(() => {
    if (!cohort) return;
    setError(''); setResult(null); setRehearsal(null);
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
  }, [cohort, eventId, countdown]);

  // F-1 (v3): tier-2 impact-preview confirm — cohort NAME, team count, round,
  // and per-team hit, all client-side from data already fetched. The payload
  // detonate() sends is byte-identical to pre-v3; Cancel sends nothing.
  const onDetonate = useCallback(async () => {
    const c = cohorts.find((x) => x.id === cohort);
    const ev = events.find((e) => e.id === eventId);
    if (!c || !ev) return;
    const ok = await confirmAction({
      title: `🚨 Detonate ${ev.label}`,
      message: `A synchronized black-swan hits every team in "${c.name}" with a full-screen takeover and a ${Number(countdown) || 60}s response countdown. This applies REAL treasury and reputation impact.`,
      impact: c.teams > 0
        ? `${c.name} — ${c.teams} team${c.teams === 1 ? '' : 's'}, currently R${c.round} · ${fmtHit(ev)} each.`
        : `${c.name} — 0 joined teams (currently R${c.round}). The shockwave hits player sub-sessions; with none joined, nothing will be impacted.`,
      confirmLabel: 'DETONATE',
      danger: true,
    });
    if (!ok) return;
    detonate();
  }, [cohorts, cohort, events, eventId, countdown, confirmAction, detonate]);

  return (
    <div style={S.page}>
      <div style={S.brand}>🌊 Shockwave Control</div>
      <div style={S.sub}>Detonate a synchronized crisis across every team in a cohort.</div>

      {error && <div style={S.error}>{error}</div>}
      {result && <div style={S.ok}>💥 Detonated <b>{result.event?.title}</b> — {result.teams_hit} team(s) hit.</div>}

      <label style={S.lbl}>Target cohort</label>
      <select
        value={cohort}
        onChange={(e) => { setCohort(e.target.value); setPrefilled(false); }}
        style={S.input}
      >
        <option value="">{cohorts.length === 0 ? 'No cohorts found' : '— Choose a target cohort —'}</option>
        {cohorts.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name} — {c.teams} team{c.teams === 1 ? '' : 's'} · R{c.round}
          </option>
        ))}
      </select>
      {/* F-1: prefill is visible provenance, never a silent default. */}
      {prefilled && cohort && (
        <div style={S.prefillNote}>
          🎯 Prefilled from your dashboard cohort selection — change it above if this is not the cohort you mean.
        </div>
      )}
      {!cohort && cohorts.length > 0 && (
        <div style={S.chooseNote}>Nothing is targeted yet — the detonate button unlocks once you choose.</div>
      )}

      <label style={S.lbl}>Crisis</label>
      <div style={S.grid}>
        {events.map((ev) => (
          <button key={ev.id} onClick={() => setEventId(ev.id)}
            style={{ ...S.card, ...(eventId === ev.id ? S.cardActive : {}) }}>
            <div style={{ fontWeight: 700 }}>{ev.label}</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>{fmtHit(ev)}</div>
          </button>
        ))}
      </div>

      <label style={S.lbl}>Countdown (seconds)</label>
      <input type="number" min="15" max="600" value={countdown}
        onChange={(e) => setCountdown(e.target.value)} style={{ ...S.input, width: 120 }} />

      <div style={{ marginTop: 24, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* S4 / F-2: rehearse-first is deliberately the left/first action —
            see the crisis exactly as configured, with zero student impact. */}
        <button style={{ ...S.rehearse, opacity: cohort && !rehearsing ? 1 : 0.45, cursor: cohort && !rehearsing ? 'pointer' : 'not-allowed' }}
          onClick={rehearse} disabled={!cohort || rehearsing}
          title={cohort ? 'Preview this crisis on YOUR screen only — no game-state change, no student broadcast. Logged as shockwave_rehearsal.' : 'Choose a target cohort first'}>
          {rehearsing ? '⏳ Rehearsing…' : '🎭 Rehearse (no student impact)'}
        </button>
        <button style={{ ...S.detonate, opacity: cohort ? 1 : 0.45, cursor: cohort ? 'pointer' : 'not-allowed' }}
          onClick={onDetonate} disabled={!cohort}
          title={cohort ? undefined : 'Choose a target cohort first'}>
          🚨 Detonate Shockwave…
        </button>
      </div>

      {/* S4 / F-2: rehearsal preview — rendered from the POST response, which
          the server built without touching any game state. */}
      {rehearsal && (
        <div style={S.rehearsalCard} role="status">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <span style={S.rehearsalBadge}>🎭 REHEARSAL — students NOT affected</span>
            <button onClick={() => setRehearsal(null)} aria-label="Dismiss rehearsal preview"
              style={{ marginLeft: 'auto', background: 'transparent', border: 'none', cursor: 'pointer', color: '#8899a6', fontSize: '0.95rem', fontWeight: 700 }}>✕</button>
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: 4 }}>
            {rehearsal.event?.title}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: 10 }}>
            {rehearsal.event?.narrative}
          </div>
          <div style={{ display: 'flex', gap: 18, fontFamily: 'var(--font-mono, monospace)', fontSize: '0.85rem', marginBottom: 10 }}>
            <span style={{ color: '#f87171' }}>💰 {fmtHit({ financial_impact: rehearsal.event?.financial_impact ?? 0, reputation_impact: rehearsal.event?.reputation_impact ?? 0 }).split(' · ')[0]} treasury / team</span>
            <span style={{ color: '#f87171' }}>📉 {rehearsal.event?.reputation_impact} reputation / team</span>
            <span style={{ color: '#8899a6' }}>⏱ {Number(countdown) || 60}s response countdown</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8899a6', lineHeight: 1.5 }}>
            This is what the detonation applies to every team — nothing was changed and no player saw
            anything ({rehearsal.message || 'rehearsal only'}). The run is attributable: it appears in
            the audit trail as <code>shockwave_rehearsal</code>.
          </div>
        </div>
      )}

      {confirmModal}
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
  rehearse: { padding: '14px 22px', fontSize: '0.95rem', fontWeight: 700, borderRadius: 12, cursor: 'pointer', background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.45)' },
  rehearsalCard: { marginTop: 20, padding: '16px 18px', borderRadius: 12, background: 'linear-gradient(135deg, rgba(30,20,8,0.9), rgba(24,16,10,0.95))', border: '1px dashed rgba(245,158,11,0.5)' },
  rehearsalBadge: { fontSize: 'var(--type-caption)', fontWeight: 900, letterSpacing: '0.1em', color: '#f59e0b', background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.4)', borderRadius: 6, padding: '4px 8px' },
  cancel: { padding: '14px 20px', fontSize: '0.95rem', fontWeight: 700, borderRadius: 12, border: '1px solid var(--border-subtle, rgba(148,163,184,0.3))', cursor: 'pointer', background: 'transparent', color: 'inherit' },
  error: { padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5', marginBottom: 16, fontSize: '0.9rem' },
  prefillNote: { marginTop: 8, fontSize: '0.78rem', color: '#f59e0b', background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 8, padding: '8px 10px' },
  chooseNote: { marginTop: 8, fontSize: '0.78rem', color: 'var(--text-muted, #8899a6)' },
  ok: { padding: '10px 14px', borderRadius: 8, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.4)', color: '#6ee7b7', marginBottom: 16, fontSize: '0.9rem' },
};
