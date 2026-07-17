'use client';
import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * TurnaroundConsole — Facilitator orchestration surface for the post-completion
 * Turnaround module (P4). SLOT: facilitator admin surface (NOT a player slot).
 *
 * Shows eligibility for a COMPLETED session, opens the 4-round arc, commits each
 * round's recovery lever, and displays the phase ladder + amended result. All
 * calls hit the require_sim_manager admin endpoints; a normal run is never
 * altered — the arc only appends turnaround state.
 */

const PHASES = ['crisis', 'stabilisation', 'recovery', 'exit'];
const PHASE_LABEL = {
    crisis: 'Crisis', stabilisation: 'Stabilisation',
    recovery: 'Recovery', exit: 'Exit',
};
const NEXT_GATE = {
    crisis: 'Treasury > $0  ·  Reputation > 20',
    stabilisation: 'Treasury > $10M  ·  Reputation > 45',
    recovery: 'Treasury > $20M  ·  Reputation > 55',
    exit: 'Comeback complete',
};

export default function TurnaroundConsole({ sessionId }) {
    const [state, setState] = useState(null);
    const [elig, setElig] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');

    const refresh = useCallback(async () => {
        if (!sessionId) return;
        try {
            const [s, e] = await Promise.all([
                fetch(`${API}/api/admin/turnaround/${sessionId}/state`, { credentials: 'include' }).then(r => r.ok ? r.json() : null),
                fetch(`${API}/api/admin/turnaround/${sessionId}/eligibility`, { credentials: 'include' }).then(r => r.ok ? r.json() : null),
            ]);
            setState(s); setElig(e); setError('');
        } catch (err) { setError('Cannot reach API'); }
    }, [sessionId]);

    useEffect(() => { refresh(); }, [refresh]);

    const call = async (path, body) => {
        setBusy(true); setError('');
        try {
            const res = await fetch(`${API}/api/admin/turnaround/${sessionId}/${path}`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: body ? JSON.stringify(body) : undefined,
            });
            if (!res.ok) {
                const d = await res.json().catch(() => ({}));
                throw new Error(d.detail || `Request failed (${res.status})`);
            }
            await refresh();
        } catch (err) { setError(err.message); }
        finally { setBusy(false); }
    };

    const card = {
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-card, 10px)', padding: '1.1rem 1.25rem',
    };
    const btn = (bg) => ({
        padding: '0.5rem 0.9rem', borderRadius: '8px', border: '1px solid var(--border-subtle)',
        background: bg, color: '#fff', cursor: 'pointer', fontWeight: 700, fontSize: '0.8rem',
        opacity: busy ? 0.6 : 1,
    });

    if (!sessionId) return null;

    const active = state?.active;
    const status = state?.status || 'none';
    const phase = state?.phase || 'crisis';
    const amended = state?.amended_report;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.1rem' }}>🔧</span>
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Turnaround Arc
                </h3>
                {status !== 'none' && (
                    <span style={{
                        fontSize: '0.68rem', fontWeight: 700, padding: '2px 8px', borderRadius: '6px',
                        background: 'var(--accent-soft)', color: 'var(--accent)',
                        fontFamily: 'var(--font-mono, monospace)', textTransform: 'uppercase',
                    }}>{status}</span>
                )}
            </div>

            {error && <div style={{ ...card, borderColor: 'var(--danger)', color: 'var(--danger-text)' }}>⚠️ {error}</div>}

            {/* ── Not started: eligibility + open ── */}
            {!active && status !== 'graduated' && status !== 'expired' && (
                <div style={card}>
                    {elig ? (
                        <>
                            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                Terminal M_R: <strong>{elig.current_mr}</strong> (threshold {elig.threshold}) ·
                                {' '}completed: <strong>{String(elig.completed)}</strong> ·
                                {' '}permitted: <strong>{String(elig.caller_permitted)}</strong>
                            </div>
                            <button
                                disabled={!elig.eligible || busy}
                                onClick={() => call('open')}
                                style={{ ...btn('var(--accent)'), marginTop: '0.9rem',
                                    opacity: (!elig.eligible || busy) ? 0.5 : 1,
                                    cursor: (!elig.eligible || busy) ? 'not-allowed' : 'pointer' }}
                            >Open Turnaround Arc (4 rounds)</button>
                            {!elig.eligible && (
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                    Not currently eligible — needs the module enabled, your grant, a completed run, and M_R below {elig.threshold}.
                                </div>
                            )}
                        </>
                    ) : <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Checking eligibility…</div>}
                </div>
            )}

            {/* ── Phase ladder ── */}
            {(active || amended) && (
                <div style={card}>
                    <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        {PHASES.map((p, i) => {
                            const reached = PHASES.indexOf(phase) >= i || (amended && amended.graduated);
                            const current = p === phase && active;
                            return (
                                <span key={p} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <span style={{
                                        padding: '3px 9px', borderRadius: '6px', fontSize: '0.72rem', fontWeight: 700,
                                        background: current ? 'var(--accent)' : reached ? 'var(--positive-soft)' : 'rgba(100,116,139,0.15)',
                                        color: current ? '#fff' : reached ? 'var(--positive-text)' : 'var(--text-muted)',
                                    }}>{PHASE_LABEL[p]}</span>
                                    {i < PHASES.length - 1 && <span style={{ color: 'var(--text-muted)' }}>›</span>}
                                </span>
                            );
                        })}
                    </div>
                    {active && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.6rem' }}>
                            Round T{state.turnaround_round}/{state.max_rounds} · Next gate: {NEXT_GATE[phase]}
                            <br />Treasury ${Math.round((state.treasury || 0) / 1e6)}M · Reputation {Math.round(state.reputation || 0)}
                        </div>
                    )}
                </div>
            )}

            {/* ── Active round: A/B/C recovery levers ── */}
            {active && state?.config && (
                <div style={card}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                        {state.config.title}
                    </div>
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '0.8rem' }}>
                        {state.config.crisis}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {Object.entries(state.config.options).map(([key, opt]) => (
                            <button key={key} disabled={busy}
                                onClick={() => call('commit', { choice: key })}
                                style={btn('var(--bg-elevated, #2a3140)')}>
                                <span style={{ color: 'var(--accent)' }}>{opt.label}</span> · {opt.title}
                            </button>
                        ))}
                    </div>
                    <button disabled={busy} onClick={() => call('abort')}
                        style={{ ...btn('transparent'), color: 'var(--danger-text)', marginTop: '0.9rem', border: '1px solid var(--danger)' }}>
                        Abort arc (restore completed result)
                    </button>
                </div>
            )}

            {/* ── Completed: amended report ── */}
            {amended && !active && (
                <div style={{ ...card, borderLeft: `3px solid ${amended.graduated ? 'var(--positive)' : 'var(--caution)'}` }}>
                    <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {amended.graduated ? '✅ Comeback complete' : '⏳ Arc expired'}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.6 }}>
                        Amended M_R: <strong>{amended.regenerative_multiple}</strong>
                        {' '}(base {amended.base_regenerative_multiple}{amended.turnaround_premium ? `, +${amended.turnaround_premium} premium` : ''})
                        <br />Final phase: {PHASE_LABEL[amended.final_phase] || amended.final_phase} · rounds used: {amended.rounds_used}
                        <br />Recovered treasury ${Math.round((amended.recovered_treasury || 0) / 1e6)}M · reputation {Math.round(amended.recovered_reputation || 0)}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                        The original R10 result remains the canonical record.
                    </div>
                </div>
            )}
        </div>
    );
}
