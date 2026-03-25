'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './GodModeStatus.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GodModeStatus() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/system-status`);
            if (res.ok) setStatus(await res.json());
        } catch { /* ignore */ }
        setLoading(false);
    };

    useEffect(() => { load(); const i = setInterval(load, 10000); return () => clearInterval(i); }, []);

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
