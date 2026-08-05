'use client';
import { useState, useEffect, useCallback } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * SystemicRiskControls — God Mode panel for tuning the Phase-1
 * systemic risk engines: Difficulty Tier, Black Swan probability,
 * NPC Cascading Reactions, Tipping Points, and Foreshadowing.
 *
 * Reads/writes to the God Mode settings blob via the admin API.
 */



const TOGGLE_SWITCHES = [
    { key: 'systemic_risk_enabled',       label: 'ESG-Adjusted WACC + Tipping Points', icon: '⚙️',  desc: 'Dynamic cost-of-capital that responds to carbon intensity, governance risk, and social license. Enables irreversible systemic tipping gates.' },
    { key: 'black_swan_events_enabled',   label: 'Black Swan Events',                  icon: '🦢',  desc: 'Stochastic, low-probability, high-impact events (sovereign crises, pandemic waves, climate litigation) triggered by game state + difficulty tier.' },
    { key: 'npc_cascading_enabled',       label: 'NPC Cascading Reactions',             icon: '👥',  desc: 'Stakeholder NPCs trigger irreversible cascades (divestment campaigns, proxy fights, regulatory enforcement) when satisfaction drops below thresholds.' },
    { key: 'foreshadowing_signals_enabled', label: 'Foreshadowing Signals',             icon: '🔮',  desc: 'Pedagogical hints that signal upcoming systemic consequences based on student decisions. Helps students learn cause-effect relationships.' },
    // Post-completion Turnaround module (P1/P4). NOT a tick engine — an optional
    // 4-round crisis-recovery arc a granted facilitator runs AFTER a run finishes.
    { key: 'turnaround_module_enabled', label: 'Post-Completion Turnaround Module', icon: '🔧',  desc: 'Optional 4-round crisis-recovery arc a GRANTED facilitator can run AFTER a session completes its 10 rounds, offered to teams whose terminal M_R fell below 0.80. Off by default; also requires a per-facilitator grant. A normal run stays complete at R10.' },
];

export default function SystemicRiskControls() {
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState('');

    const fetchSettings = useCallback(() => {
        fetch(`${API}/api/admin/god/settings`)
            .then(r => r.ok ? r.json() : Promise.reject('Failed'))
            .then(d => { setSettings(d); setLoading(false); })
            .catch(() => { setError('Cannot reach API'); setLoading(false); });
    }, []);

    useEffect(() => { fetchSettings(); }, [fetchSettings]);

    const updateSetting = async (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
        setSaving(true);
        setSaved(false);
        setError('');
        try {
            const res = await fetch(`${API}/api/admin/god/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: value }),
            });
            if (!res.ok) throw new Error('Save failed');
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Loading systemic risk settings...</div>;

    const sectionLabel = (icon, text, accent = '#94a3b8') => (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            marginBottom: '1rem', paddingBottom: '0.5rem',
            borderBottom: `1px solid ${accent}22`,
        }}>
            <span style={{ fontSize: '0.85rem' }}>{icon}</span>
            <span style={{
                fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.14em',
                textTransform: 'uppercase', color: accent,
            }}>{text}</span>
            <span style={{ flex: 1, height: '1px', background: `${accent}22` }} />
        </div>
    );

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <div style={{
                        width: '38px', height: '38px', borderRadius: '10px',
                        background: 'linear-gradient(135deg, #ef4444, #f97316)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.1rem', boxShadow: '0 4px 12px rgba(239,68,68,0.25)',
                    }}>🌡️</div>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                            Systemic Risk Controls
                        </h2>
                        <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.05em' }}>
                            PHASE-1 ENGINE CONFIGURATION
                        </div>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {saving && <span style={{ fontSize: 'var(--type-caption)', color: '#f59e0b' }}>⏳ Saving...</span>}
                    {saved && <span style={{ fontSize: 'var(--type-caption)', color: '#22c55e', fontWeight: 600 }}>✅ Saved</span>}
                    {error && <span style={{ fontSize: 'var(--type-caption)', color: '#ef4444' }}>⚠️ {error}</span>}
                </div>
            </div>

            {/* ── Difficulty Tier Info ── */}
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: '12px', padding: '1.25rem',
            }}>
                {sectionLabel('⚡', 'Difficulty Tier', '#f59e0b')}
                <div style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                    padding: '0.85rem 1rem', borderRadius: '8px',
                    background: 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(245,158,11,0.02))',
                    border: '1px solid rgba(245,158,11,0.15)',
                }}>
                    <span style={{ fontSize: '1.1rem', marginTop: '1px' }}>🔒</span>
                    <div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                            Set Per-Cohort at Creation
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                            Difficulty tier (Introductory / Professional / Executive) is configured per-cohort
                            via the <strong style={{ color: 'var(--text-secondary)' }}>Experience Level</strong> preset
                            when creating a new cohort. This ensures each cohort&apos;s Black Swan probability
                            multipliers, impact severity, treasury floor, and NPC fine caps are locked to
                            the facilitator&apos;s original pedagogical intent.
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Engine Toggle Switches ── */}
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: '12px', padding: '1.25rem',
            }}>
                {sectionLabel('🔧', 'Engine Toggles', '#818cf8')}
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                    Enable or disable individual systemic risk engines. Disabling an engine causes it to silently
                    skip during tick processing — existing state is preserved but no new calculations are performed.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {TOGGLE_SWITCHES.map(toggle => {
                        const isOn = settings?.[toggle.key] !== false;
                        return (
                            <div key={toggle.key} style={{
                                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                                padding: '0.85rem 1rem', borderRadius: '8px',
                                background: isOn ? 'rgba(99,102,241,0.04)' : 'rgba(0,0,0,0.04)',
                                border: `1px solid ${isOn ? 'rgba(99,102,241,0.15)' : 'rgba(0,0,0,0.06)'}`,
                                transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                            }}>
                                <div
                                    onClick={() => updateSetting(toggle.key, !isOn)}
                                    role="switch"
                                    aria-checked={isOn}
                                    tabIndex={0}
                                    onKeyDown={e => e.key === 'Enter' && updateSetting(toggle.key, !isOn)}
                                    style={{
                                        width: '44px', minWidth: '44px', height: '24px', borderRadius: '12px',
                                        background: isOn
                                            ? 'linear-gradient(135deg, #818cf8, #6366f1)'
                                            : 'rgba(100,116,139,0.3)',
                                        cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
                                        boxShadow: isOn ? '0 2px 8px rgba(99,102,241,0.3)' : 'none',
                                        marginTop: '2px',
                                    }}
                                >
                                    <div style={{
                                        width: '18px', height: '18px', borderRadius: '50%',
                                        background: '#fff', position: 'absolute', top: '3px',
                                        left: isOn ? '23px' : '3px',
                                        transition: 'left 0.2s',
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                                    }} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                                        <span style={{ fontSize: '0.85rem' }}>{toggle.icon}</span>
                                        <span style={{
                                            fontSize: '0.82rem', fontWeight: 700,
                                            color: isOn ? 'var(--text-primary)' : 'var(--text-muted)',
                                        }}>{toggle.label}</span>
                                        <span style={{
                                            fontSize: 'var(--type-caption)', padding: '1px 6px', borderRadius: '4px',
                                            background: isOn ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.08)',
                                            color: isOn ? '#22c55e' : '#ef4444',
                                            fontWeight: 700, fontFamily: 'var(--font-mono, monospace)',
                                        }}>{isOn ? 'ON' : 'OFF'}</span>
                                    </div>
                                    <div style={{
                                        fontSize: 'var(--type-caption)', color: 'var(--text-muted)', lineHeight: 1.5,
                                    }}>{toggle.desc}</div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* ── Pedagogical Notes ── */}
            <div style={{
                background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(99,102,241,0.04))',
                border: '1px solid rgba(16,185,129,0.15)',
                borderRadius: '12px', padding: '1.25rem',
                borderLeft: '3px solid #10b981',
            }}>
                {sectionLabel('📖', 'Pedagogical Notes', '#10b981')}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <p style={{ margin: 0 }}>
                        <strong style={{ color: '#818cf8' }}>Difficulty Tier Ownership:</strong> Each cohort&apos;s difficulty
                        tier is locked at creation via the Experience Level preset (Classroom → Foundation,
                        Workshop → Advanced, Executive → Expert). This prevents runtime drift between
                        God Mode global settings and per-cohort pedagogical intent.
                    </p>
                    <p style={{ margin: 0, marginTop: '0.5rem', padding: '0.6rem', borderRadius: '6px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
                        💡 <strong>Tip:</strong> Disable foreshadowing signals for expert-tier cohorts to remove
                        pedagogical safety nets. Re-enable after the simulation for debrief transparency.
                    </p>
                </div>
            </div>
        </div>
    );
}
