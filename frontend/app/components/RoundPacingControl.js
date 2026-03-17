'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * RoundPacingControl — God Mode panel for controlling round progression.
 * Modes:
 *   Free — no gating, players advance freely
 *   Manual — facilitator unlocks each round
 *   Timed — schedule unlock at a specific date/time, or immediately
 */
export default function RoundPacingControl() {
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    const [sessionId, setSessionId] = useState('');
    const [sessions, setSessions] = useState([]);
    const [pacing, setPacing] = useState(null);
    const [mode, setMode] = useState('free');
    const [scheduledDatetime, setScheduledDatetime] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');

    // Fetch sessions list
    useEffect(() => {
        fetch(`${API}/api/admin/sessions`)
            .then(r => r.ok ? r.json() : [])
            .then(d => {
                const list = Array.isArray(d) ? d : (d?.sessions || []);
                setSessions(list);
                if (list.length > 0 && !sessionId) {
                    const id = list[0]?.session_id || list[0]?.id || list[0];
                    setSessionId(typeof id === 'string' ? id : String(id));
                }
            })
            .catch(() => { });
    }, [API]);

    // Fetch current pacing when session changes
    const fetchPacing = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing`);
            if (res.ok) {
                const data = await res.json();
                setPacing(data);
                setMode(data.mode);
            }
        } catch { /* offline */ }
    }, [API, sessionId]);

    useEffect(() => { fetchPacing(); }, [fetchPacing]);

    // Refresh pacing every 10s to show countdown updates
    useEffect(() => {
        if (!sessionId) return;
        const timer = setInterval(fetchPacing, 10000);
        return () => clearInterval(timer);
    }, [sessionId, fetchPacing]);

    const handleSetMode = async () => {
        if (!sessionId) return;
        setLoading(true);
        setStatus('');
        try {
            let interval_seconds = 0;
            let scheduled_at = null;

            if (mode === 'timed' && scheduledDatetime) {
                const target = new Date(scheduledDatetime);
                const now = new Date();
                interval_seconds = Math.max(0, Math.floor((target - now) / 1000));
                scheduled_at = target.toISOString();
            }

            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode, interval_seconds, scheduled_at }),
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(data);
                if (mode === 'timed' && interval_seconds === 0) {
                    setStatus(`✅ Next round unlocked immediately! (Round ${data.unlocked_round})`);
                } else if (mode === 'timed' && scheduledDatetime) {
                    setStatus(`✅ Round ${data.unlocked_round + 1} scheduled to unlock at ${new Date(scheduledDatetime).toLocaleString()}`);
                } else {
                    setStatus(`✅ Mode set to "${data.mode}". Unlocked up to Round ${data.unlocked_round >= 999 ? '∞' : data.unlocked_round}.`);
                }
            } else {
                setStatus('❌ Failed to set pacing mode.');
            }
        } catch { setStatus('❌ Network error.'); }
        setLoading(false);
    };

    const handleUnlock = async () => {
        if (!sessionId) return;
        setLoading(true);
        setStatus('');
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing/unlock`, {
                method: 'POST',
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(prev => ({ ...prev, unlocked_round: data.unlocked_round }));
                setStatus(`🔓 Round ${data.unlocked_round} unlocked!`);
            } else {
                setStatus('❌ Failed to unlock round.');
            }
        } catch { setStatus('❌ Network error.'); }
        setLoading(false);
    };

    const handleImmediateUnlock = async () => {
        if (!sessionId) return;
        setLoading(true);
        setStatus('');
        try {
            // Set timed mode with 0 seconds = immediate
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'timed', interval_seconds: 0 }),
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(data);
                setStatus(`⚡ Round ${data.unlocked_round} unlocked immediately!`);
            }
        } catch { setStatus('❌ Network error.'); }
        setLoading(false);
    };

    const MODES = [
        { id: 'free', label: '🟢 Free Play', desc: 'No gating — players advance freely' },
        { id: 'manual', label: '🔒 Manual', desc: 'Facilitator unlocks each round' },
        { id: 'timed', label: '📅 Scheduled', desc: 'Unlock at a specific date and time' },
    ];

    // Calculate time remaining for scheduled unlock
    const getTimeRemaining = () => {
        if (!pacing?.next_unlock_at) return null;
        const target = new Date(pacing.next_unlock_at);
        const now = new Date();
        const diff = target - now;
        if (diff <= 0) return 'Unlocking now…';
        const mins = Math.floor(diff / 60000);
        const secs = Math.floor((diff % 60000) / 1000);
        if (mins > 60) {
            const hrs = Math.floor(mins / 60);
            return `${hrs}h ${mins % 60}m`;
        }
        return `${mins}m ${secs}s`;
    };

    return (
        <section style={{
            background: '#ffffff',
            borderRadius: '16px',
            padding: '2rem',
            maxWidth: '700px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
            <h2 style={{
                margin: '0 0 0.5rem 0',
                fontSize: '1.4rem',
                background: 'linear-gradient(90deg, #6366f1, #a855f7)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
            }}>⏱️ Round Pacing Control</h2>
            <p style={{ color: '#475569', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Control when players can advance to the next round.
            </p>

            {/* Session selector */}
            <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ color: '#334155', fontSize: '0.85rem', display: 'block', marginBottom: '0.4rem', fontWeight: 600 }}>
                    Target Session
                </label>
                <select
                    value={sessionId}
                    onChange={e => setSessionId(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '0.6rem 1rem',
                        background: '#f8fafc',
                        color: '#1e293b',
                        border: '1px solid #cbd5e1',
                        borderRadius: '8px',
                        fontSize: '0.9rem',
                    }}
                >
                    {sessions.length === 0 && <option value="">No sessions found</option>}
                    {sessions.map(s => {
                        const id = s?.session_id || s?.id || s;
                        const name = s?.team_name || s?.name || id;
                        return <option key={id} value={id}>{name} ({String(id).slice(0, 8)}…)</option>;
                    })}
                </select>
            </div>

            {/* Current status */}
            {pacing && (
                <div style={{
                    background: '#f0f4ff',
                    border: '1px solid #c7d2fe',
                    borderRadius: '10px',
                    padding: '1rem 1.2rem',
                    marginBottom: '1.5rem',
                    display: 'flex',
                    gap: '1.5rem',
                    flexWrap: 'wrap',
                }}>
                    <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Mode</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1e293b' }}>
                            {pacing.mode === 'free' ? '🟢 Free' : pacing.mode === 'manual' ? '🔒 Manual' : '📅 Scheduled'}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Unlocked Up To</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1e293b' }}>
                            Round {pacing.unlocked_round >= 999 ? '∞' : pacing.unlocked_round}
                        </div>
                    </div>
                    {pacing.mode === 'timed' && pacing.next_unlock_at && (
                        <div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Next Unlock</div>
                            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#d97706' }}>
                                {getTimeRemaining()}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Mode selector */}
            <div style={{ marginBottom: '1.2rem' }}>
                <label style={{ color: '#334155', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                    Pacing Mode
                </label>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {MODES.map(m => (
                        <button
                            key={m.id}
                            onClick={() => setMode(m.id)}
                            style={{
                                padding: '0.6rem 1.2rem',
                                borderRadius: '8px',
                                border: mode === m.id ? '2px solid #6366f1' : '1px solid #d1d5db',
                                background: mode === m.id ? 'rgba(99, 102, 241, 0.08)' : '#ffffff',
                                color: mode === m.id ? '#4338ca' : '#475569',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: mode === m.id ? 700 : 500,
                                transition: 'all 0.2s',
                                fontFamily: 'inherit',
                            }}
                        >
                            {m.label}
                            <div style={{ fontSize: '0.7rem', color: mode === m.id ? '#6366f1' : '#94a3b8', marginTop: '0.2rem' }}>{m.desc}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Scheduled date/time picker */}
            {mode === 'timed' && (
                <div style={{ marginBottom: '1.2rem' }}>
                    <label style={{ color: '#334155', fontSize: '0.85rem', display: 'block', marginBottom: '0.4rem', fontWeight: 600 }}>
                        📅 Schedule Unlock At
                    </label>
                    <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <input
                            type="datetime-local"
                            value={scheduledDatetime}
                            onChange={e => setScheduledDatetime(e.target.value)}
                            style={{
                                padding: '0.6rem 1rem',
                                background: '#f8fafc',
                                color: '#1e293b',
                                border: '1px solid #cbd5e1',
                                borderRadius: '8px',
                                fontSize: '0.9rem',
                                flex: 1,
                                minWidth: '200px',
                            }}
                        />
                        <span style={{ color: '#475569', fontSize: '0.8rem', fontWeight: 500 }}>or</span>
                        <button
                            onClick={handleImmediateUnlock}
                            disabled={loading}
                            style={{
                                padding: '0.6rem 1.2rem',
                                borderRadius: '8px',
                                border: 'none',
                                background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                                color: '#fff',
                                fontSize: '0.85rem',
                                fontWeight: 700,
                                cursor: loading ? 'wait' : 'pointer',
                                whiteSpace: 'nowrap',
                                fontFamily: 'inherit',
                            }}
                        >
                            ⚡ Immediate
                        </button>
                    </div>
                    <p style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.4rem' }}>
                        Leave blank and click "⚡ Immediate" to unlock now, or pick a future date/time.
                    </p>
                </div>
            )}

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: '0.8rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
                <button
                    onClick={handleSetMode}
                    disabled={loading || !sessionId}
                    style={{
                        padding: '0.7rem 1.8rem',
                        borderRadius: '8px',
                        border: 'none',
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        color: '#fff',
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        cursor: loading ? 'wait' : 'pointer',
                        opacity: loading || !sessionId ? 0.5 : 1,
                        boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)',
                        fontFamily: 'inherit',
                    }}
                >
                    {loading ? '⏳ Saving…' : '💾 Apply Mode'}
                </button>

                {(pacing?.mode === 'manual' || mode === 'manual') && (
                    <button
                        onClick={handleUnlock}
                        disabled={loading || !sessionId}
                        style={{
                            padding: '0.7rem 1.8rem',
                            borderRadius: '8px',
                            border: 'none',
                            background: 'linear-gradient(135deg, #10b981, #059669)',
                            color: '#fff',
                            fontSize: '0.95rem',
                            fontWeight: 700,
                            cursor: loading ? 'wait' : 'pointer',
                            opacity: loading || !sessionId ? 0.5 : 1,
                            boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
                            fontFamily: 'inherit',
                        }}
                    >
                        🔓 Unlock Next Round
                    </button>
                )}
            </div>

            {/* Status message */}
            {status && (
                <div style={{
                    marginTop: '1rem',
                    padding: '0.8rem 1rem',
                    borderRadius: '8px',
                    background: status.startsWith('✅') || status.startsWith('🔓') || status.startsWith('⚡')
                        ? '#f0fdf4' : '#fef2f2',
                    border: status.startsWith('✅') || status.startsWith('🔓') || status.startsWith('⚡')
                        ? '1px solid #bbf7d0' : '1px solid #fecaca',
                    color: status.startsWith('✅') || status.startsWith('🔓') || status.startsWith('⚡')
                        ? '#166534' : '#991b1b',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                }}>
                    {status}
                </div>
            )}
        </section>
    );
}
