'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { playerIdHeader } from '../hooks/useSimulation';
import { currencySymbol } from '../utils/format';

/**
 * NegotiationRoom — Stakeholder Negotiation Rooms, Phase 2 player UI.
 * (SPEC_Stakeholder_Negotiation_Rooms §7.)
 *
 * Slot: OverlayHost (interrupt) — summoned from the stakeholder rail's
 * "Request meeting" action on a hostile agent; never ambient. Always-dark
 * surface with pinned colors (theming convention for overlay modals).
 *
 * All rules live server-side (negotiation.py): this component renders state
 * and forwards intents. Opening an already-open room falls back to resuming
 * it. The room auto-closes server-side on commit; here we just report.
 *
 * Props: sessionId, agentId (agent to open with), onClose(summary|null).
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';

const STAGE_TINT = {
  hostile: '#ef4444', triggered: '#dc2626', agitated: '#f97316',
  watching: '#f59e0b', dormant: '#2dd4bf',
};

const fmtM = (v) => `${currencySymbol()}${(Math.abs(v) / 1e6).toFixed(v % 1e6 ? 2 : 1)}M`.replace('.0M', 'M');
const fmtMoney = (v) => (Math.abs(v) >= 1e6 ? fmtM(v) : `${currencySymbol()}${(v / 1e3).toFixed(0)}K`);

export default function NegotiationRoom({ sessionId, agentId, onClose }) {
  const [room, setRoom] = useState(null);
  const [menu, setMenu] = useState(null);
  const [closedSummary, setClosedSummary] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState('');
  const [confirmId, setConfirmId] = useState(null);
  // Phase 3: the agent's mood + any concession they gestured at. Both are
  // presentation only — accepting still requires the explicit click below.
  const [suggested, setSuggested] = useState(null);
  const logRef = useRef(null);

  const call = useCallback(async (path, body) => {
    const r = await fetch(`${API}/api/simulations/${sessionId}/negotiation${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const detail = data.detail;
      throw Object.assign(new Error(
        typeof detail === 'string' ? detail : (detail?.detail || detail?.error || `Request failed (${r.status})`)
      ), { payload: detail });
    }
    return data;
  }, [sessionId]);

  // Open (or resume) on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await call('/open', { agent_id: agentId });
        if (!cancelled) { setRoom(d.room); setMenu(d.menu); }
      } catch (e) {
        if (cancelled) return;
        if (e.payload?.error === 'room_already_open') {
          try {
            const st = await call('');
            if (!cancelled && st.active) { setRoom(st.active); setMenu(st.menu); return; }
          } catch { /* fall through */ }
        }
        setError(e.payload?.detail || e.message);
      }
    })();
    return () => { cancelled = true; };
  }, [agentId, call]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [room?.turns?.length]);

  const handleResult = (d) => {
    if (d.closed) { setClosedSummary(d.closed); setRoom(null); return; }
    if (d.room) setRoom(d.room);
    if (d.menu) setMenu(d.menu);
    if ('suggested_concession' in d) setSuggested(d.suggested_concession || null);
  };

  const send = async () => {
    if (!text.trim() || busy) return;
    setBusy(true); setError('');
    try { handleResult(await call('/say', { text: text.trim() })); setText(''); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  const accept = async (cid) => {
    setBusy(true); setError(''); setConfirmId(null);
    try { handleResult(await call('/accept', { concession_id: cid })); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  const walkOut = async () => {
    setBusy(true); setError('');
    try { handleResult(await call('/walk-out')); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  const persona = room?.persona;
  const tint = STAGE_TINT[persona?.stage] || '#ef4444';
  const deals = room?.deals || [];

  // ── Pinned always-dark palette (overlay modal convention) ──
  const C = { bg: '#0b1220', panel: '#111a2c', line: 'rgba(148,163,184,0.18)', txt: '#e2e8f0', dim: '#94a3b8', faint: '#64748b' };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 12000, background: 'rgba(2,6,15,0.82)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}
         onClick={() => { if (closedSummary || error) onClose?.(closedSummary); }}>
      <div onClick={(e) => e.stopPropagation()}
           style={{ width: 'min(960px, 96vw)', maxHeight: '92vh', display: 'flex', flexDirection: 'column', borderRadius: 16, overflow: 'hidden', background: C.bg, border: `1px solid ${tint}44`, boxShadow: `0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px ${tint}22`, color: C.txt }}>

        {/* ── Header ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px', background: C.panel, borderBottom: `1px solid ${C.line}` }}>
          <span style={{ fontSize: '2rem' }}>{persona?.avatar || closedSummary?.persona?.avatar || '🤝'}</span>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: '1rem' }}>
              {persona?.name || closedSummary?.persona?.name || 'Negotiation'}
              <span style={{ marginLeft: 10, fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.08em', color: tint, border: `1px solid ${tint}66`, borderRadius: 999, padding: '2px 8px', textTransform: 'uppercase' }}>
                {persona?.stage || closedSummary?.persona?.stage || ''}
              </span>
            </div>
            <div style={{ fontSize: 'var(--type-caption)', color: C.dim }}>
              {persona?.title || closedSummary?.persona?.title || ''}
              {/* Phase 3: live mood read from the agent's last reply */}
              {room?.mood && room.mood !== 'neutral' && (
                <span style={{ marginLeft: 8, fontWeight: 700, color: room.mood === 'softening' ? '#34d399' : '#f87171' }}>
                  · {room.mood === 'softening' ? '▲ softening' : '▼ hardening'}
                </span>
              )}
            </div>
          </div>
          <div style={{ marginLeft: 'auto', fontSize: 'var(--type-caption)', color: C.faint, textAlign: 'right' }}>
            {room && <>Entry fee paid: <strong style={{ color: C.txt }}>{fmtMoney(room.fee_paid)}</strong><br /></>}
            <button onClick={() => onClose?.(closedSummary)} style={{ marginTop: 4, background: 'transparent', border: `1px solid ${C.line}`, color: C.dim, borderRadius: 8, padding: '4px 10px', cursor: 'pointer', fontSize: 'var(--type-caption)' }}>✕ Close</button>
          </div>
        </div>

        {/* ── Error-only state (e.g. not hostile / cap reached) ── */}
        {!room && !closedSummary && (
          <div style={{ padding: 28, textAlign: 'center' }}>
            {error
              ? <><div style={{ fontSize: '1.6rem', marginBottom: 8 }}>🚪</div><div style={{ color: '#fca5a5', fontSize: '0.88rem' }}>{error}</div></>
              : <div style={{ color: C.dim }}>Arranging the meeting…</div>}
          </div>
        )}

        {/* ── Closed summary ── */}
        {closedSummary && (
          <div style={{ padding: 24 }}>
            <div style={{ fontSize: '0.8rem', color: C.dim, marginBottom: 8 }}>
              Meeting ended — {closedSummary.resolution === 'walk_out' ? 'you walked out' : closedSummary.resolution.replace(/_/g, ' ')}.
            </div>
            {closedSummary.deals?.length
              ? closedSummary.deals.map((d, i) => (
                  <div key={i} style={{ fontSize: '0.85rem', padding: '8px 12px', borderRadius: 10, background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.3)', marginBottom: 6 }}>
                    ✅ {d.label} — {fmtMoney(d.cost_paid)} · tolerance {d.tolerance_before} → {d.tolerance_after}
                  </div>
                ))
              : <div style={{ fontSize: '0.85rem', color: '#fbbf24' }}>No deal was struck{closedSummary.resolution === 'walk_out' ? ' — they will remember being stonewalled.' : '.'}</div>}
            <button onClick={() => onClose?.(closedSummary)} style={{ marginTop: 14, padding: '8px 18px', borderRadius: 10, border: `1px solid ${C.line}`, background: C.panel, color: C.txt, fontWeight: 700, cursor: 'pointer' }}>
              Return to the cockpit
            </button>
          </div>
        )}

        {/* ── Live room ── */}
        {room && (
          <div style={{ display: 'flex', minHeight: 0, flex: 1 }}>
            {/* Transcript + composer */}
            <div style={{ flex: '1 1 55%', display: 'flex', flexDirection: 'column', minWidth: 0, borderRight: `1px solid ${C.line}` }}>
              <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 220, maxHeight: '46vh' }}>
                {room.turns.map((t, i) => (
                  <div key={i} style={{ alignSelf: t.who === 'player' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                    <div style={{
                      padding: '8px 12px', borderRadius: 12, fontSize: '0.82rem', lineHeight: 1.5,
                      background: t.who === 'player' ? 'rgba(99,102,241,0.18)' : C.panel,
                      border: `1px solid ${t.who === 'player' ? 'rgba(99,102,241,0.4)' : C.line}`,
                      color: C.txt,
                    }}>{t.text}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: `1px solid ${C.line}` }}>
                <input value={text} onChange={(e) => setText(e.target.value)}
                       onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
                       placeholder="Make your case… (talk is free; concessions are not)"
                       maxLength={500} disabled={busy}
                       style={{ flex: 1, padding: '9px 12px', borderRadius: 10, border: `1px solid ${C.line}`, background: C.bg, color: C.txt, fontSize: '0.82rem' }} />
                <button onClick={send} disabled={busy || !text.trim()}
                        style={{ padding: '9px 16px', borderRadius: 10, border: 'none', background: 'rgba(99,102,241,0.35)', color: C.txt, fontWeight: 800, cursor: 'pointer' }}>Send</button>
              </div>
            </div>

            {/* Concession menu */}
            <div style={{ flex: '1 1 45%', display: 'flex', flexDirection: 'column', minWidth: 280 }}>
              <div style={{ padding: '10px 14px', fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.1em', color: C.dim, borderBottom: `1px solid ${C.line}` }}>
                WHAT THEY WOULD ACCEPT
              </div>
              <div style={{ overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 10, maxHeight: '40vh' }}>
                {(menu || []).map((m) => (
                  <div key={m.id} style={{
                    padding: '10px 12px', borderRadius: 12, background: C.panel,
                    // Phase 3: highlight what they gestured at — still just a
                    // highlight; the click below is what commits anything.
                    border: `1px solid ${suggested === m.id ? 'rgba(52,211,153,0.55)' : C.line}`,
                    boxShadow: suggested === m.id ? '0 0 0 1px rgba(52,211,153,0.25)' : 'none',
                  }}>
                    {suggested === m.id && (
                      <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.06em', color: '#34d399', marginBottom: 4 }}>
                        THEY GESTURED AT THIS
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.82rem' }}>{m.label}</span>
                      <span style={{ fontWeight: 800, fontSize: '0.82rem', color: m.cost > 0 ? '#fbbf24' : '#34d399' }}>
                        {m.cost > 0 ? fmtMoney(m.cost) : 'free'}
                        {m.multiplier > 1 && <span style={{ color: '#f87171', fontSize: 'var(--type-caption)' }}> ×{m.multiplier}</span>}
                      </span>
                    </div>
                    <div style={{ fontSize: 'var(--type-caption)', color: C.dim, marginTop: 4, lineHeight: 1.45 }}>
                      Tolerance +{m.tolerance_gain} (capped — a deal buys calm, not affection).
                      {m.creates_promise && <> <strong style={{ color: '#fbbf24' }}>Commits you</strong>: {String(m.promise_metric).replace(/_/g, ' ')} must improve within 2 rounds — break it and future meetings get pricier.</>}
                      {m.effects?.reputation_delta ? ` Reputation ${m.effects.reputation_delta}.` : ''}
                    </div>
                    {confirmId === m.id ? (
                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button onClick={() => accept(m.id)} disabled={busy}
                                style={{ flex: 1, padding: '6px 0', borderRadius: 8, border: 'none', background: 'rgba(52,211,153,0.3)', color: C.txt, fontWeight: 800, cursor: 'pointer', fontSize: 'var(--type-caption)' }}>✓ Confirm — {m.cost > 0 ? fmtMoney(m.cost) : 'free'}</button>
                        <button onClick={() => setConfirmId(null)} style={{ padding: '6px 12px', borderRadius: 8, border: `1px solid ${C.line}`, background: 'transparent', color: C.dim, cursor: 'pointer', fontSize: 'var(--type-caption)' }}>Cancel</button>
                      </div>
                    ) : (
                      <button onClick={() => setConfirmId(m.id)} disabled={busy}
                              style={{ marginTop: 8, width: '100%', padding: '6px 0', borderRadius: 8, border: `1px solid ${tint}55`, background: `${tint}18`, color: C.txt, fontWeight: 700, cursor: 'pointer', fontSize: 'var(--type-caption)' }}>
                        Offer this
                      </button>
                    )}
                  </div>
                ))}
              </div>
              {deals.length > 0 && (
                <div style={{ padding: '8px 14px', fontSize: 'var(--type-caption)', color: '#34d399', borderTop: `1px solid ${C.line}` }}>
                  ✅ {deals[deals.length - 1].label} agreed — tolerance {deals[deals.length - 1].tolerance_before} → {deals[deals.length - 1].tolerance_after}
                </div>
              )}
              {error && <div style={{ padding: '8px 14px', fontSize: 'var(--type-caption)', color: '#fca5a5' }}>{error}</div>}
              <div style={{ padding: 12, borderTop: `1px solid ${C.line}` }}>
                <button onClick={walkOut} disabled={busy}
                        style={{ width: '100%', padding: '8px 0', borderRadius: 10, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.12)', color: '#fca5a5', fontWeight: 800, cursor: 'pointer', fontSize: '0.78rem' }}>
                  🚪 Walk out {deals.length === 0 ? '(they will remember)' : ''}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
