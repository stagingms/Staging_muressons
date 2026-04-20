'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const SEV_COLORS = { critical: '#ef4444', warning: '#f59e0b', info: '#3b82f6', success: '#22c55e' };
const SEV_BG = { critical: 'rgba(239,68,68,0.08)', warning: 'rgba(245,158,11,0.08)', info: 'rgba(59,130,246,0.08)', success: 'rgba(34,197,94,0.08)' };

export default function ComplexityEventFeed({ sessionId }) {
    const [feed, setFeed] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filterSev, setFilterSev] = useState('all');

    useEffect(() => {
        if (!sessionId) return;
        setLoading(true);
        fetch(`${API}/api/admin/complexity-events/${sessionId}`)
            .then(r => r.json())
            .then(d => { setFeed(d.feed || []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [sessionId]);

    if (!sessionId) return (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📡</div>
            <p>Select a cohort to view complexity engine events</p>
        </div>
    );

    const allEvents = feed.flatMap(r => r.events).reverse();
    const filtered = filterSev === 'all' ? allEvents : allEvents.filter(e => e.severity === filterSev);

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    📡 Complexity Event Feed
                </h2>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {['all', 'critical', 'warning', 'info', 'success'].map(s => (
                        <button key={s} onClick={() => setFilterSev(s)} style={{
                            padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600,
                            border: filterSev === s ? '2px solid' : '1px solid var(--border-subtle)',
                            borderColor: filterSev === s ? (SEV_COLORS[s] || '#3b82f6') : undefined,
                            background: filterSev === s ? (SEV_BG[s] || 'rgba(59,130,246,0.08)') : 'var(--bg-body)',
                            color: filterSev === s ? (SEV_COLORS[s] || '#3b82f6') : 'var(--text-muted)',
                            cursor: 'pointer',
                        }}>
                            {s === 'all' ? '🌐 All' : s.charAt(0).toUpperCase() + s.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading events...</div>
            ) : filtered.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No events found</div>
            ) : (
                <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {filtered.map((evt, i) => (
                        <div key={i} style={{
                            padding: '0.75rem 1rem', borderRadius: '8px',
                            background: SEV_BG[evt.severity] || SEV_BG.info,
                            border: `1px solid ${SEV_COLORS[evt.severity] || SEV_COLORS.info}22`,
                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                        }}>
                            <span style={{ fontSize: '1.3rem' }}>{evt.icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                                    {evt.label}
                                </div>
                                {typeof evt.value === 'string' && evt.value.length > 5 && (
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{evt.value}</div>
                                )}
                            </div>
                            <span style={{
                                padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700,
                                background: SEV_COLORS[evt.severity] || '#64748b', color: '#fff',
                            }}>R{evt.round}</span>
                        </div>
                    ))}
                </div>
            )}

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                {allEvents.length} total events across {feed.length} rounds
            </div>
        </div>
    );
}
