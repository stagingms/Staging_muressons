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
                    </div>
                </div>
            )}

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
