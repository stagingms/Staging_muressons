'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const STATUS_ICONS = { healthy: '🟢', warning: '🟡', stressed: '🟠', critical: '🔴', completed: '🟣' };

// Pulse animation styles for live session indicators
const pulseKeyframes = `
@keyframes healthPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
@keyframes criticalPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(239,68,68,0); }
}
`;

export default function SessionHealthDashboard() {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    // G1/Phase 1: track freshness so a failed refresh is visible instead of
    // silently rendering stale cards.
    const [lastUpdated, setLastUpdated] = useState(null);
    const [refreshFailed, setRefreshFailed] = useState(false);

    const refresh = () => {
        fetch(`${API}/api/admin/session-health`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setSessions(d.sessions || []);
                setLastUpdated(Date.now());
                setRefreshFailed(false);
                setLoading(false);
            })
            .catch(() => { setRefreshFailed(true); setLoading(false); });
    };

    useEffect(() => { refresh(); const t = setInterval(refresh, 15000); return () => clearInterval(t); }, []);

    const statusCounts = sessions.reduce((acc, s) => { acc[s.status] = (acc[s.status] || 0) + 1; return acc; }, {});

    if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading session health...</div>;

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <style dangerouslySetInnerHTML={{ __html: pulseKeyframes }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>🏥 Session Health Monitor</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {refreshFailed ? (
                        <span style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: '#ef4444' }}>
                            ⚠️ Refresh failed{lastUpdated ? ` — showing data as of ${new Date(lastUpdated).toLocaleTimeString()}` : ''}
                        </span>
                    ) : lastUpdated ? (
                        <span style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>
                            Updated {new Date(lastUpdated).toLocaleTimeString()}
                        </span>
                    ) : null}
                    <button onClick={refresh} style={{ padding: '0.4rem 1rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer' }}>🔄 Refresh</button>
                </div>
            </div>

            {/* Status Summary */}
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {Object.entries(statusCounts).map(([status, count]) => (
                    <div key={status} style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.1rem' }}>{STATUS_ICONS[status] || '⚪'}</span>
                        <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-primary)' }}>{count}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{status}</span>
                    </div>
                ))}
            </div>

            {/* Session Cards */}
            {sessions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>No active cohorts</div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem' }}>
                    {sessions.map(s => (
                        <div key={s.session_id} style={{
                            padding: '1.25rem', borderRadius: '12px', background: 'var(--bg-card)',
                            border: `2px solid ${s.status_color}33`, position: 'relative', overflow: 'hidden',
                        }}>
                            {/* Status indicator bar */}
                            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: s.status_color }} />

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{s.cohort_name}</div>
                                    <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>{s.facilitator_id} · {s.paradigm}</div>
                                </div>
                                <div style={{
                                    display: 'flex', alignItems: 'center', gap: '0.25rem',
                                    padding: '0.2rem 0.6rem', borderRadius: '4px',
                                    background: `${s.status_color}15`, color: s.status_color,
                                    fontSize: 'var(--type-caption)', fontWeight: 700,
                                    animation: s.status === 'critical' ? 'criticalPulse 1.5s infinite' : (s.status === 'healthy' ? 'healthPulse 3s infinite' : 'none'),
                                }}>
                                    {STATUS_ICONS[s.status]} {s.status.toUpperCase()}
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                                {[
                                    { label: 'Round', value: `${s.round}/10`, color: '#3b82f6' },
                                    { label: 'Treasury', value: `$${s.treasury_m}M`, color: s.treasury_m < 0 ? '#ef4444' : '#22c55e' },
                                    { label: 'Reputation', value: s.reputation.toFixed(1), color: s.reputation < 30 ? '#ef4444' : '#22c55e' },
                                    { label: 'EBITDA', value: `$${s.ebitda_m}M`, color: '#8b5cf6' },
                                    { label: 'Synergy', value: `${s.synergy}x`, color: '#06b6d4' },
                                    { label: 'Crises', value: s.active_crises, color: s.active_crises > 2 ? '#ef4444' : '#64748b' },
                                    { label: 'CAROIC', value: s.caroic?.caroic_pct != null ? `${s.caroic.caroic_pct}%` : '—', color: (s.caroic?.grade === 'A+' || s.caroic?.grade === 'A') ? '#22c55e' : (s.caroic?.grade === 'B' || s.caroic?.grade === 'C') ? '#f59e0b' : '#ef4444' },
                                    { label: 'Grade', value: s.caroic?.grade || '—', color: (s.caroic?.grade === 'A+' || s.caroic?.grade === 'A') ? '#22c55e' : (s.caroic?.grade === 'B' || s.caroic?.grade === 'C') ? '#f59e0b' : '#ef4444' },
                                ].map((m, i) => (
                                    <div key={i} style={{ padding: '0.4rem', borderRadius: '6px', background: 'var(--bg-body)', textAlign: 'center' }}>
                                        <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{m.label}</div>
                                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Relative advantage bar */}
                            <div style={{ marginTop: '0.75rem', padding: '0.4rem 0.6rem', borderRadius: '6px', background: s.relative_advantage >= 1 ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)' }}>vs Competitor</span>
                                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: s.relative_advantage >= 1 ? '#22c55e' : '#ef4444', fontFamily: 'var(--font-mono)' }}>
                                    {s.relative_advantage >= 1 ? '▲' : '▼'} {s.relative_advantage}x
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
