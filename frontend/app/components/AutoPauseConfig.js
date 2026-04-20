'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function AutoPauseConfig() {
    const [config, setConfig] = useState({ enabled: false, triggers: {}, pause_message: '' });
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState(null);

    useEffect(() => {
        fetch(`${API}/api/admin/auto-pause`)
            .then(r => r.json())
            .then(data => setConfig({ enabled: false, triggers: {}, pause_message: '', ...data }))
            .catch(() => {});
    }, []);

    const save = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/auto-pause`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) });
            if (res.ok) { setStatus('✅ Saved'); setTimeout(() => setStatus(null), 3000); }
        } catch { setStatus('❌ Failed'); }
        setSaving(false);
    };

    const TRIGGER_LABELS = {
        greenwashing_scandal: { icon: '🌿🚨', label: 'Greenwashing Scandal', desc: 'Pause when green rhetoric doesn\'t match investment' },
        technology_lockin_penalty: { icon: '🔒', label: 'Technology Lock-In', desc: 'Pause when a BU locks in for 3+ rounds' },
        tipping_point_reached: { icon: '🌡️', label: 'Climate Tipping Point', desc: 'Pause on global climate tipping point' },
        dividend_ratchet_triggered: { icon: '📉', label: 'Dividend Ratchet', desc: 'Pause when dividends are cut >20%' },
        stakeholder_fatigue_applied: { icon: '😰', label: 'Stakeholder Fatigue', desc: 'Pause when crisis fatigue kicks in' },
        treasury_negative: { icon: '💸', label: 'Negative Treasury', desc: 'Pause when treasury goes below $0' },
        reputation_below_20: { icon: '📉', label: 'Reputation Crisis', desc: 'Pause when reputation drops below 20' },
    };

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>⏸️ Auto-Pause Triggers</h2>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>Automatically pause the simulation for teachable moments</p>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: config.enabled ? '#22c55e' : 'var(--text-muted)' }}>
                        {config.enabled ? 'ENABLED' : 'DISABLED'}
                    </span>
                    <input type="checkbox" checked={config.enabled} onChange={e => setConfig(p => ({ ...p, enabled: e.target.checked }))}
                        style={{ width: '18px', height: '18px', accentColor: '#22c55e' }} />
                </label>
            </div>

            <div style={{ opacity: config.enabled ? 1 : 0.5, pointerEvents: config.enabled ? 'auto' : 'none', transition: 'opacity 0.3s' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {Object.entries(TRIGGER_LABELS).map(([key, { icon, label, desc }]) => (
                        <div key={key} style={{
                            padding: '0.75rem 1rem', borderRadius: '8px', background: 'var(--bg-card)',
                            border: `1px solid ${(config.triggers || {})[key] ? '#3b82f633' : 'var(--border-subtle)'}`,
                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                        }}>
                            <input type="checkbox" checked={(config.triggers || {})[key] || false}
                                onChange={e => setConfig(p => ({ ...p, triggers: { ...(p.triggers || {}), [key]: e.target.checked } }))}
                                style={{ width: '16px', height: '16px', accentColor: '#3b82f6' }} />
                            <span style={{ fontSize: '1.3rem' }}>{icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>{label}</div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>

                <div style={{ marginTop: '1rem' }}>
                    <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>
                        Pause Message (shown to players)
                    </label>
                    <input type="text" value={config.pause_message} onChange={e => setConfig(p => ({ ...p, pause_message: e.target.value }))}
                        style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem', boxSizing: 'border-box' }} />
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '1rem' }}>
                {status && <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{status}</span>}
                <button onClick={save} disabled={saving} style={{
                    padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none',
                    background: 'linear-gradient(135deg, #3b82f6, #06b6d4)', color: '#fff',
                    fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', opacity: saving ? 0.6 : 1,
                }}>{saving ? '⏳ Saving...' : '💾 Save Configuration'}</button>
            </div>
        </div>
    );
}
