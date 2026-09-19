'use client';
import { useState, useEffect, useCallback } from 'react';
import { useConfirm } from './ConfirmModal';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const TRIGGER_LABELS = {
    greenwashing_scandal:     { icon: '🌿🚨', label: 'Greenwashing Scandal',   desc: "Pause when green rhetoric doesn't match investment" },
    technology_lockin_penalty:{ icon: '🔒',   label: 'Technology Lock-In',     desc: 'Pause when a BU locks in for 3+ rounds' },
    tipping_point_reached:    { icon: '🌡️',  label: 'Climate Tipping Point',  desc: 'Pause on global climate tipping point' },
    dividend_ratchet_triggered:{ icon: '📉',  label: 'Dividend Ratchet',       desc: 'Pause when dividends are cut >20%' },
    stakeholder_fatigue_applied:{ icon: '😰', label: 'Stakeholder Fatigue',    desc: 'Pause when crisis fatigue kicks in' },
    treasury_negative:        { icon: '💸',   label: 'Negative Treasury',      desc: 'Pause when treasury goes below $0' },
    reputation_below_20:      { icon: '📉',   label: 'Reputation Crisis',      desc: 'Pause when reputation drops below 20' },
};

const DEFAULT_CONFIG = {
    enabled: false,
    triggers: Object.fromEntries(Object.keys(TRIGGER_LABELS).map(k => [k, false])),
    pause_message: '⏸️ Simulation paused by facilitator for discussion.',
};

export default function AutoPauseConfig({ sessionId }) {
    const [config, setConfig] = useState(DEFAULT_CONFIG);
    const [saving, setSaving]   = useState(false);
    const [resetting, setResetting] = useState(false);
    const [status, setStatus]   = useState(null);
    const [loading, setLoading] = useState(false);
    const [confirm, confirmModal] = useConfirm();

    const showStatus = (msg, duration = 3500) => {
        setStatus(msg);
        setTimeout(() => setStatus(null), duration);
    };

    const load = useCallback(() => {
        if (!sessionId) return;
        setLoading(true);
        fetch(`${API}/api/admin/sessions/${sessionId}/auto-pause`, {
            credentials: 'include',
        })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data) {
                    const { session_id: _sid, type: _t, ...cfg } = data;
                    setConfig({ ...DEFAULT_CONFIG, ...cfg });
                }
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [sessionId]);

    useEffect(() => { load(); }, [load]);

    const save = async () => {
        if (!sessionId) return;
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/auto-pause`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(config),
            });
            if (res.ok) {
                showStatus('✅ Saved for this cohort only');
            } else {
                const err = await res.json().catch(() => ({}));
                showStatus(`❌ ${err.detail || 'Save failed'}`);
            }
        } catch {
            showStatus('❌ Network error');
        }
        setSaving(false);
    };

    const resetToDefaults = async () => {
        if (!sessionId) return;
        const ok = await confirm({
            title: 'Reset Auto-Pause Triggers',
            message: "Reset this cohort's auto-pause config to platform defaults?",
            impact: 'All customized pause triggers for this cohort will be replaced by the default system rules.',
            confirmLabel: 'Reset to defaults',
            danger: true,
        });
        if (!ok) return;
        setResetting(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/auto-pause`, {
                method: 'DELETE',
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                const { session_id: _sid, reset: _r, ...cfg } = data;
                setConfig({ ...DEFAULT_CONFIG, ...cfg });
                showStatus('↩️ Reset to platform defaults');
            } else {
                showStatus('❌ Reset failed — this cohort keeps its current triggers');
            }
        } catch { showStatus('❌ Reset failed'); }
        setResetting(false);
    };

    // ── No session selected ────────────────────────────────────────
    if (!sessionId) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>⏸️</div>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.4rem' }}>No cohort selected</div>
                <div style={{ fontSize: '0.82rem' }}>
                    Select a session from the Leaderboard first.<br />
                    Auto-pause is configured <strong>per cohort</strong> — changes only affect the selected session.
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

            {/* ── Header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        ⏸️ Auto-Pause Triggers
                    </h2>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        Settings apply to <strong>this cohort only</strong> — other sessions are unaffected.
                    </p>
                    <div style={{
                        display: 'inline-block', marginTop: '0.35rem',
                        padding: '0.2rem 0.65rem', borderRadius: '99px',
                        background: '#3b82f618', border: '1px solid #3b82f640',
                        fontSize: 'var(--type-caption)', fontWeight: 700, color: '#60a5fa',
                        fontFamily: 'monospace', letterSpacing: '0.04em',
                    }}>
                        {sessionId}
                    </div>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', flexShrink: 0 }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: config.enabled ? '#22c55e' : 'var(--text-muted)' }}>
                        {config.enabled ? 'ENABLED' : 'DISABLED'}
                    </span>
                    <input type="checkbox" checked={config.enabled}
                        onChange={e => setConfig(p => ({ ...p, enabled: e.target.checked }))}
                        style={{ width: '18px', height: '18px', accentColor: '#22c55e' }} />
                </label>
            </div>

            {/* ── Trigger Checklist ── */}
            <div style={{ opacity: config.enabled ? 1 : 0.45, pointerEvents: config.enabled ? 'auto' : 'none', transition: 'opacity 0.3s' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {Object.entries(TRIGGER_LABELS).map(([key, { icon, label, desc }]) => (
                        <div key={key} style={{
                            padding: '0.75rem 1rem', borderRadius: '8px',
                            background: 'var(--bg-card)',
                            border: `1px solid ${(config.triggers || {})[key] ? '#3b82f633' : 'var(--border-subtle)'}`,
                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                            transition: 'border-color 0.2s',
                        }}>
                            <input type="checkbox"
                                checked={(config.triggers || {})[key] || false}
                                onChange={e => setConfig(p => ({
                                    ...p,
                                    triggers: { ...(p.triggers || {}), [key]: e.target.checked }
                                }))}
                                style={{ width: '16px', height: '16px', accentColor: '#3b82f6', flexShrink: 0 }} />
                            <span style={{ fontSize: '1.3rem' }}>{icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>{label}</div>
                                <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* ── Pause Message ── */}
                <div style={{ marginTop: '1rem' }}>
                    <label style={{
                        display: 'block', fontSize: 'var(--type-caption)', fontWeight: 700,
                        textTransform: 'uppercase', letterSpacing: '0.1em',
                        color: 'var(--text-muted)', marginBottom: '0.3rem',
                    }}>
                        Pause Message (shown to players)
                    </label>
                    <input type="text"
                        value={config.pause_message}
                        onChange={e => setConfig(p => ({ ...p, pause_message: e.target.value }))}
                        style={{
                            width: '100%', padding: '0.6rem 1rem', borderRadius: '6px',
                            border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                            color: 'var(--text-primary)', fontSize: '0.85rem', boxSizing: 'border-box',
                        }} />
                </div>
            </div>

            {/* ── Actions ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <button onClick={resetToDefaults} disabled={resetting}
                    style={{
                        padding: '0.5rem 1.1rem', borderRadius: '8px',
                        border: '1px solid var(--border-subtle)', background: 'transparent',
                        color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.8rem',
                        cursor: 'pointer', opacity: resetting ? 0.5 : 1,
                    }}>
                    {resetting ? '⏳ Resetting...' : '↩️ Reset to defaults'}
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    {status && <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{status}</span>}
                    <button onClick={save} disabled={saving || loading} style={{
                        padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none',
                        background: 'linear-gradient(135deg, #3b82f6, #06b6d4)', color: '#fff',
                        fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                        opacity: (saving || loading) ? 0.6 : 1,
                    }}>
                        {saving ? '⏳ Saving...' : '💾 Save for this cohort'}
                    </button>
                </div>
            </div>
            {confirmModal}
        </div>
    );
}
