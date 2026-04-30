'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './GodModeStatus.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GodModeStatus() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    // Global settings state (merged from GlobalSettings)
    const [settings, setSettings] = useState(null);
    const [freezeMsg, setFreezeMsg] = useState('System maintenance in progress.');
    const [settingsStatus, setSettingsStatus] = useState('');

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/system-status`);
            if (res.ok) setStatus(await res.json());
        } catch { /* ignore */ }
        setLoading(false);
    };

    const loadSettings = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/settings`);
            if (res.ok) setSettings(await res.json());
        } catch {}
    };

    useEffect(() => {
        load();
        loadSettings();
        const i = setInterval(load, 10000);
        return () => clearInterval(i);
    }, []);

    // ── Global Settings handlers ──
    const handleFreeze = async () => {
        if (!confirm('⚠️ This will freeze ALL active simulations. Continue?')) return;
        const res = await fetch(`${API}/api/admin/god/freeze`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: freezeMsg }),
        });
        if (res.ok) { load(); loadSettings(); setSettingsStatus('System FROZEN'); setTimeout(() => setSettingsStatus(''), 3000); }
    };

    const handleUnfreeze = async () => {
        const res = await fetch(`${API}/api/admin/god/unfreeze`, { method: 'POST' });
        if (res.ok) { load(); loadSettings(); setSettingsStatus('System UNFROZEN'); setTimeout(() => setSettingsStatus(''), 3000); }
    };

    if (loading) return <div className={styles.loading}>Loading system status…</div>;
    if (!status) return <div className={styles.error}>Failed to load system status</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🏠</span>
                <div>
                    <h2>System Status</h2>
                    <p className={styles.subtitle}>Real-time overview of the entire platform</p>
                </div>
            </div>

            {status.system_frozen && (
                <div className={styles.freezeBanner}>
                    ❄️ <strong>System is FROZEN</strong> — All simulations are paused
                </div>
            )}

            <div className={styles.cardGrid}>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>👨‍🏫</div>
                    <div className={styles.cardValue}>{status.total_facilitators}</div>
                    <div className={styles.cardLabel}>FACILITATORS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🏢</div>
                    <div className={styles.cardValue}>{status.total_cohorts}</div>
                    <div className={styles.cardLabel}>COHORTS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>👥</div>
                    <div className={styles.cardValue}>{status.total_players}</div>
                    <div className={styles.cardLabel}>PLAYERS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🔌</div>
                    <div className={styles.cardValue}>{status.active_ws_connections}</div>
                    <div className={styles.cardLabel}>WS CONNECTIONS</div>
                </div>
            </div>

            <div className={styles.gaugeRow}>
                <div className={styles.gauge}>
                    <span>💰 Avg Treasury</span>
                    <strong>${status.avg_treasury}M</strong>
                    <div className={styles.bar}><div className={styles.barFill} style={{ width: `${Math.min(status.avg_treasury, 100)}%`, background: '#10b981' }} /></div>
                </div>
                <div className={styles.gauge}>
                    <span>⭐ Avg Reputation</span>
                    <strong>{status.avg_reputation}</strong>
                    <div className={styles.bar}><div className={styles.barFill} style={{ width: `${Math.min(status.avg_reputation, 100)}%`, background: '#f59e0b' }} /></div>
                </div>
            </div>

            {/* ── Platform Controls (merged from GlobalSettings) ── */}
            {settings && (
                <div className={styles.section}>
                    <h3>⚙️ Platform Controls</h3>
                    {settingsStatus && (
                        <div style={{
                            marginBottom: '1rem', padding: '0.5rem 1rem', borderRadius: '6px',
                            background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
                            fontSize: '0.82rem', fontWeight: 600, color: '#10b981',
                        }}>
                            {settingsStatus}
                        </div>
                    )}
                    <div className={styles.controlsGrid}>
                        {/* Emergency Freeze */}
                        <div className={`${styles.controlCard} ${settings.system_frozen ? styles.controlCardFrozen : ''}`}>
                            <div>
                                <div className={styles.controlTitle}>🚨 Emergency Freeze</div>
                                <div className={styles.controlDesc}>
                                    {settings.system_frozen
                                        ? `❄️ Frozen since ${new Date(settings.freeze_started_at).toLocaleString()}`
                                        : 'Instantly pause all simulations with a maintenance banner.'}
                                </div>
                            </div>
                            {!settings.system_frozen ? (
                                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                    <input
                                        type="text"
                                        placeholder="Freeze message…"
                                        value={freezeMsg}
                                        onChange={e => setFreezeMsg(e.target.value)}
                                        style={{
                                            padding: '0.4rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem',
                                            border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                            color: 'var(--text-primary)', width: '180px',
                                        }}
                                    />
                                    <button onClick={handleFreeze} style={{
                                        padding: '0.4rem 0.8rem', borderRadius: '6px', border: 'none',
                                        background: '#ef4444', color: '#fff', fontWeight: 700, fontSize: '0.75rem',
                                        cursor: 'pointer', whiteSpace: 'nowrap',
                                    }}>
                                        🔴 Freeze
                                    </button>
                                </div>
                            ) : (
                                <button onClick={handleUnfreeze} style={{
                                    padding: '0.4rem 0.8rem', borderRadius: '6px', border: 'none',
                                    background: '#10b981', color: '#fff', fontWeight: 700, fontSize: '0.75rem',
                                    cursor: 'pointer', whiteSpace: 'nowrap',
                                }}>
                                    🟢 Unfreeze
                                </button>
                            )}
                        </div>

                        {/* ── Pedagogical Scaffolding Controls ── */}
                        <div className={styles.controlCard} style={{
                            borderLeft: settings.prediction_gates_enabled || settings.round_recap_enabled || settings.real_world_cards_enabled
                                ? '3px solid #a855f7' : '3px solid rgba(148,163,184,0.15)',
                        }}>
                            <div style={{ flex: 1 }}>
                                <div className={styles.controlTitle}>🧠 Pedagogical Scaffolding</div>
                                <div className={styles.controlDesc}>
                                    Metacognitive features, formative checkpoints, and learner journey aids.
                                    <span style={{ fontSize: '0.6rem', color: '#a78bfa', fontStyle: 'italic', marginLeft: 4 }}>
                                        Experience level is set per-cohort during creation
                                    </span>
                                </div>

                                <div style={{
                                    display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.6rem',
                                    alignItems: 'center',
                                }}>
                                    {[
                                        { key: 'prediction_gates_enabled', label: '🔮 Predictions', default: false },
                                        { key: 'confidence_calibration_enabled', label: '🎰 Confidence', default: false },
                                        { key: 'board_room_moments_enabled', label: '🏢 Board Room', default: true },
                                        { key: 'round_recap_enabled', label: '📋 Recap', default: false },
                                        { key: 'real_world_cards_enabled', label: '🌍 Case Cards', default: false },
                                        { key: 'strategy_memo_enabled', label: '📝 Memo', default: false },
                                        { key: 'debrief_protocol_enabled', label: '🎭 Debrief', default: false },
                                        { key: 'self_learning_mode', label: '🎓 Self-Learn', default: false },
                                        { key: 'r6_revelation_enabled', label: '🚨 R6 Twist', default: true },
                                        { key: 'r7_budget_allocation_enabled', label: '♻️ R7 Budget', default: true },
                                        { key: 'r8_tribunal_enabled', label: '⚖️ R8 Tribunal', default: true },
                                    ].map(t => (
                                        <button
                                            key={t.key}
                                            onClick={async () => {
                                                const next = !settings[t.key];
                                                const res = await fetch(`${API}/api/admin/global-settings`, {
                                                    method: 'PATCH',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({ [t.key]: next }),
                                                });
                                                if (res.ok) { loadSettings(); setSettingsStatus(`${t.label} ${next ? 'ON' : 'OFF'}`); setTimeout(() => setSettingsStatus(''), 3000); }
                                            }}
                                            style={{
                                                padding: '2px 8px', borderRadius: 4, border: 'none',
                                                background: settings[t.key] ? 'rgba(168,85,247,0.15)' : 'rgba(148,163,184,0.08)',
                                                color: settings[t.key] ? '#c084fc' : '#64748b',
                                                fontWeight: 700, fontSize: '0.58rem', cursor: 'pointer',
                                                transition: 'all 0.15s',
                                            }}
                                        >
                                            {settings[t.key] ? '●' : '○'} {t.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Hardening Phase Intelligence ── */}
            {status.hardening && (() => {
                const h = status.hardening;
                const regimeColors = { easing: '#10b981', neutral: '#94a3b8', tightening: '#f59e0b', crisis: '#ef4444' };
                const regimeIcons = { easing: '🕊️', neutral: '⚖️', tightening: '🦅', crisis: '🔥' };
                const hasData = Object.keys(h.macro_rate_distribution || {}).length > 0 ||
                                Object.keys(h.pathway_distribution || {}).length > 0;
                if (!hasData) return null;
                return (
                    <div className={styles.section}>
                        <h3>🧪 Hardening Phase Intelligence</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                            {/* Macro Rate Distribution */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(99,102,241,0.04)',
                                border: '1px solid rgba(99,102,241,0.15)',
                            }}>
                                <div style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#818cf8', marginBottom: '0.5rem' }}>
                                    🏦 Monetary Policy Distribution
                                </div>
                                {Object.entries(h.macro_rate_distribution || {}).map(([regime, count]) => (
                                    <div key={regime} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                                        <span style={{ fontSize: '0.85rem' }}>{regimeIcons[regime] || '📊'}</span>
                                        <span style={{ flex: 1, fontSize: '0.72rem', fontWeight: 600, color: regimeColors[regime] || '#94a3b8', textTransform: 'capitalize' }}>{regime}</span>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}>{count}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Ending Pathways */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(168,85,247,0.04)',
                                border: '1px solid rgba(168,85,247,0.15)',
                            }}>
                                <div style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#a78bfa', marginBottom: '0.5rem' }}>
                                    🗺️ Active Ending Pathways
                                </div>
                                {Object.keys(h.pathway_distribution || {}).length > 0 ? Object.entries(h.pathway_distribution).map(([path, count]) => (
                                    <div key={path} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                                        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#c4b5fd', textTransform: 'capitalize' }}>{path.replace(/_/g, ' ')}</span>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}>{count}</span>
                                    </div>
                                )) : (
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontStyle: 'italic' }}>No R10 completions yet</div>
                                )}
                            </div>

                            {/* NBS + Retraining Outcomes */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(16,185,129,0.04)',
                                border: '1px solid rgba(16,185,129,0.15)',
                            }}>
                                <div style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#10b981', marginBottom: '0.5rem' }}>
                                    🌿 Stochastic Outcomes
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                                    <strong style={{ color: '#4ade80' }}>NBS Success:</strong>{' '}
                                    {h.nbs_outcomes?.succeeded || 0} ✓ · {h.nbs_outcomes?.failed || 0} ✗ · {h.nbs_outcomes?.not_triggered || 0} pending
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
                                    <strong style={{ color: '#818cf8' }}>Retraining:</strong>{' '}
                                    {h.retraining_outcomes?.succeeded || 0} ✓ · {h.retraining_outcomes?.failed || 0} ✗
                                </div>
                            </div>

                            {/* Scope 3 + AI Act */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(245,158,11,0.04)',
                                border: '1px solid rgba(245,158,11,0.15)',
                            }}>
                                <div style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#f59e0b', marginBottom: '0.5rem' }}>
                                    📋 Regulatory Exposure
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                                    <strong style={{ color: '#fbbf24' }}>Scope 3 Completeness:</strong>{' '}
                                    {h.avg_scope3_completeness != null ? `${h.avg_scope3_completeness}% avg` : 'Not yet triggered'}
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
                                    <strong style={{ color: '#f87171' }}>AI Monetised:</strong>{' '}
                                    {h.ai_monetised_count} sessions — {h.ai_monetised_count > 0 ? 'EU AI Act costs active R7+' : 'no AI deployment'}
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })()}

            {Object.keys(status.round_distribution).length > 0 && (
                <div className={styles.section}>
                    <h3>Round Distribution</h3>
                    <div className={styles.roundBars}>
                        {Object.entries(status.round_distribution).sort().map(([r, count]) => (
                            <div key={r} className={styles.roundBar}>
                                <div className={styles.roundBarLabel}>{r}</div>
                                <div className={styles.roundBarTrack}>
                                    <div className={styles.roundBarFill} style={{ width: `${Math.min(count * 20, 100)}%` }} />
                                </div>
                                <span className={styles.roundBarCount}>{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {status.recent_audit?.length > 0 && (
                <div className={styles.section}>
                    <h3>Recent Activity</h3>
                    <div className={styles.activityList}>
                        {status.recent_audit.slice(0, 5).map((e, i) => (
                            <div key={i} className={styles.activityItem}>
                                <span className={styles.activityAction}>{e.action.replace(/_/g, ' ')}</span>
                                <span className={styles.activityTime}>{new Date(e.timestamp).toLocaleString()}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
