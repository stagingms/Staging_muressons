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
  }, [cohort, eventId, countdown]);

  // F-1 (v3): tier-2 impact-preview confirm — cohort NAME, team count, round,
  // and per-team hit, all client-side from data already fetched. The payload
  // detonate() sends is byte-identical to pre-v3; Cancel sends nothing.
  const onDetonate = useCallback(async () => {
    const c = cohorts.find((x) => x.id === cohort);
    const ev = SHOCKWAVE_EVENTS.find((e) => e.id === eventId);
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
  }, [cohorts, cohort, eventId, countdown, confirmAction, detonate]);

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
        {SHOCKWAVE_EVENTS.map((ev) => (
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

      <div style={{ marginTop: 24 }}>
        <button style={{ ...S.detonate, opacity: cohort ? 1 : 0.45, cursor: cohort ? 'pointer' : 'not-allowed' }}
          onClick={onDetonate} disabled={!cohort}
          title={cohort ? undefined : 'Choose a target cohort first'}>
          🚨 Detonate Shockwave…
        </button>
      </div>

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
  cancel: { padding: '14px 20px', fontSize: '0.95rem', fontWeight: 700, borderRadius: 12, border: '1px solid var(--border-subtle, rgba(148,163,184,0.3))', cursor: 'pointer', background: 'transparent', color: 'inherit' },
  error: { padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5', marginBottom: 16, fontSize: '0.9rem' },
  prefillNote: { marginTop: 8, fontSize: '0.78rem', color: '#f59e0b', background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 8, padding: '8px 10px' },
  chooseNote: { marginTop: 8, fontSize: '0.78rem', color: 'var(--text-muted, #8899a6)' },
  ok: { padding: '10px 14px', borderRadius: 8, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.4)', color: '#6ee7b7', marginBottom: 16, fontSize: '0.9rem' },
};
