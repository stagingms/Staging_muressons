'use client';

/**
 * FacilitatorVisibilityEditor — god-mode Facilitator Registry modal.
 *
 * Sets a PER-FACILITATOR analytics-visibility profile: an admin-owned,
 * account-level baseline for which facilitator-dashboard panels this account
 * sees, layered global defaults → this profile → per-cohort overrides.
 * Facilitator column only (the player column is cohort-level pedagogy).
 *
 * GET/PUT /api/admin/god/facilitators/{id}/analytics-visibility (super_admin+).
 */
import { useState, useEffect, useCallback } from 'react';
import { FACILITATOR_ANALYTICS } from './AnalyticsControlPanel';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function FacilitatorVisibilityEditor({ facilitator, onClose }) {
    const facId = facilitator?.facilitator_id;
    const [defaults, setDefaults] = useState({});
    const [profile, setProfile] = useState({});   // sparse: only overridden keys
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        if (!facId) return;
        setLoading(true);
        try {
            const r = await fetch(`${API}/api/admin/god/facilitators/${facId}/analytics-visibility`, { credentials: 'include' });
            if (r.ok) {
                const d = await r.json();
                setDefaults(d.global_defaults?.facilitator || {});
                setProfile(d.profile?.facilitator || {});
            } else setError('Failed to load profile');
        } catch { setError('Connection error'); }
        setLoading(false);
    }, [facId]);

    useEffect(() => { load(); }, [load]);

    const effective = (key) => (key in profile ? profile[key] : (defaults[key] !== false));

    const save = async (nextProfile) => {
        setSaving(true);
        setError(null);
        try {
            const r = await fetch(`${API}/api/admin/god/facilitators/${facId}/analytics-visibility`, {
                method: 'PUT', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ facilitator: nextProfile }),
            });
            if (r.ok) {
                const d = await r.json();
                setProfile(d.profile?.facilitator || {});
            } else setError('Save failed');
        } catch { setError('Connection error'); }
        setSaving(false);
    };

    const toggleKey = (key) => {
        const next = { ...profile, [key]: !effective(key) };
        // Drop entries that match the global default — keeps the profile sparse,
        // so future changes to the global default flow through automatically.
        if (next[key] === (defaults[key] !== false)) delete next[key];
        setProfile(next);
        save(next);
    };

    const resetAll = () => { setProfile({}); save({}); };

    if (!facilitator) return null;
    const overriddenCount = Object.keys(profile).length;

    return (
        <div
            onClick={onClose}
            style={{ position: 'fixed', inset: 0, zIndex: 9500, background: 'rgba(2,6,17,0.72)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                style={{ width: 'min(560px, 94vw)', maxHeight: '84vh', overflowY: 'auto', background: 'linear-gradient(165deg, #101729, #0b1020)', border: '1px solid rgba(148,163,184,0.18)', borderRadius: 14, padding: '18px 20px', color: '#e2e8f0', boxShadow: '0 24px 70px rgba(0,0,0,0.55)' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <span style={{ fontSize: '1.1rem' }}>👁️</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '0.98rem', fontWeight: 800 }}>Visibility profile — {facilitator.name}</div>
                        <div style={{ fontSize: 'var(--type-caption)', color: '#94a3b8' }}>{facId} · facilitator-dashboard panels this account can see</div>
                    </div>
                    <button onClick={onClose} style={{ padding: '4px 10px', borderRadius: 7, border: '1px solid rgba(148,163,184,0.25)', background: 'transparent', color: '#94a3b8', cursor: 'pointer', fontWeight: 700, fontSize: 'var(--type-caption)' }}>✕ Close</button>
                </div>
                <p style={{ fontSize: 'var(--type-caption)', color: '#94a3b8', margin: '6px 0 12px', lineHeight: 1.5 }}>
                    Account-level baseline, layered <em>global defaults → this profile → per-cohort overrides</em>.
                    Unmodified panels follow the global default; {overriddenCount > 0 ? `${overriddenCount} overridden here.` : 'nothing is overridden yet.'}
                </p>

                {error && <div style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 700, marginBottom: 8 }}>❌ {error}</div>}
                {loading ? (
                    <div style={{ padding: '1.5rem', textAlign: 'center', color: '#64748b', fontSize: '0.8rem' }}>Loading…</div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: 8 }}>
                        {FACILITATOR_ANALYTICS.map((a) => {
                            const on = effective(a.key);
                            const overridden = a.key in profile;
                            return (
                                <button
                                    key={a.key}
                                    onClick={() => toggleKey(a.key)}
                                    disabled={saving}
                                    title={a.tooltip}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px',
                                        borderRadius: 10, cursor: 'pointer', textAlign: 'left',
                                        border: `1px solid ${overridden ? 'rgba(245,158,11,0.45)' : 'rgba(148,163,184,0.15)'}`,
                                        background: on ? 'rgba(16,185,129,0.07)' : 'rgba(148,163,184,0.05)',
                                        color: '#e2e8f0', opacity: saving ? 0.7 : 1,
                                    }}
                                >
                                    <span style={{ fontSize: '0.85rem' }}>{a.icon}</span>
                                    <span style={{ flex: 1, minWidth: 0, fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.label}</span>
                                    {overridden && <span style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#fbbf24', letterSpacing: '0.05em' }}>SET</span>}
                                    <span style={{ width: 34, height: 18, borderRadius: 9, position: 'relative', flexShrink: 0, background: on ? '#10b981' : 'rgba(148,163,184,0.3)', transition: 'background 0.15s' }}>
                                        <span style={{ position: 'absolute', top: 2, left: on ? 18 : 2, width: 14, height: 14, borderRadius: '50%', background: '#fff', transition: 'left 0.15s' }} />
                                    </span>
                                </button>
                            );
                        })}
                    </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 14 }}>
                    <button
                        onClick={resetAll}
                        disabled={saving || loading || overriddenCount === 0}
                        style={{ padding: '7px 14px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(148,163,184,0.08)', color: '#cbd5e1', cursor: overriddenCount ? 'pointer' : 'not-allowed', fontWeight: 700, fontSize: 'var(--type-caption)', opacity: overriddenCount ? 1 : 0.5 }}
                    >
                        ↺ Clear profile (follow global defaults)
                    </button>
                </div>
            </div>
        </div>
    );
}
