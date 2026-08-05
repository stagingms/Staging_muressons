'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function DecisionTimeline({ sessionId, leaderboard = [] }) {
    const [timeline, setTimeline] = useState([]);
    const [selectedRound, setSelectedRound] = useState(null);
    const [loading, setLoading] = useState(false);
    const [sid, setSid] = useState(sessionId || '');

    const sessions = leaderboard.filter(s => !s.player_id);

    useEffect(() => {
        const targetSid = sid || sessionId;
        if (!targetSid) return;
        setLoading(true);
        fetch(`${API}/api/admin/decision-history/${targetSid}`)
            .then(r => r.json())
            .then(d => { setTimeline(d.timeline || []); setLoading(false); if (d.timeline?.length) setSelectedRound(d.timeline.length - 1); })
            .catch(() => setLoading(false));
    }, [sid, sessionId]);

    const current = selectedRound !== null ? timeline[selectedRound] : null;

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>🕐 Decision History Replay</h2>

            {sessions.length > 0 && (
                <select value={sid} onChange={e => setSid(e.target.value)} style={{
                    padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem', maxWidth: '400px',
                }}>
                    <option value="">Select a cohort...</option>
                    {sessions.map(s => <option key={s.session_id} value={s.session_id}>{s.cohort_name || s.session_id}</option>)}
                </select>
            )}

            {loading && <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading history...</div>}

            {timeline.length > 0 && (
                <>
                    {/* Timeline Dots */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '1rem 0' }}>
                        {timeline.map((r, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
                                <button onClick={() => setSelectedRound(i)} style={{
                                    width: '36px', height: '36px', borderRadius: '50%', border: 'none',
                                    background: selectedRound === i ? '#3b82f6' : r.complexity_events.length > 0 ? '#f59e0b' : 'var(--bg-body)',
                                    color: selectedRound === i ? '#fff' : 'var(--text-primary)',
                                    fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer',
                                    boxShadow: selectedRound === i ? '0 2px 8px rgba(59,130,246,0.4)' : 'inset 0 0 0 2px var(--border-subtle)',
                                    transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                                }}>R{r.round}</button>
                                {i < timeline.length - 1 && (
                                    <div style={{ width: '20px', height: '2px', background: 'var(--border-subtle)' }} />
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Selected Round Detail */}
                    {current && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            {/* KPIs */}
                            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem' }}>
                                <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                    📈 Round {current.round} State
                                </h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                                    {[
                                        { label: 'Treasury', value: `$${current.treasury_m}M`, color: current.treasury_m < 0 ? '#ef4444' : '#22c55e' },
                                        { label: 'Reputation', value: current.reputation, color: current.reputation < 30 ? '#ef4444' : '#3b82f6' },
                                        { label: 'EBITDA', value: `$${current.ebitda_m}M`, color: '#8b5cf6' },
                                        { label: 'Synergy', value: `${current.synergy}x`, color: '#06b6d4' },
                                        { label: 'Inflation', value: `${(current.inflation * 100).toFixed(1)}%`, color: '#f59e0b' },
                                        { label: 'CoC', value: `${(current.cost_of_capital * 100).toFixed(1)}%`, color: '#64748b' },
                                    ].map((m, i) => (
                                        <div key={i} style={{ padding: '0.5rem', borderRadius: '6px', background: 'var(--bg-body)' }}>
                                            <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{m.label}</div>
                                            <div style={{ fontSize: '1rem', fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
                                        </div>
                                    ))}
                                </div>

                                {current.choices.length > 0 && (
                                    <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: '6px', background: 'rgba(59,130,246,0.08)', fontSize: '0.82rem' }}>
                                        <strong>Decision:</strong> {current.choices.join(', ')} | <strong>CapEx:</strong> ${current.total_capex.toLocaleString()}
                                    </div>
                                )}
                            </div>

                            {/* Events + BU Summary */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {current.complexity_events.length > 0 && (
                                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1rem' }}>
                                        <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>⚡ Events Fired</h4>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                            {current.complexity_events.map((e, i) => (
                                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0', fontSize: '0.82rem' }}>
                                                    <span>{e.icon}</span>
                                                    <span style={{ color: 'var(--text-primary)' }}>{e.label}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {current.bu_summary.length > 0 && (
                                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1rem' }}>
                                        <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>🏢 BU Snapshot</h4>
                                        <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
                                            <thead><tr style={{ color: 'var(--text-muted)' }}>
                                                <th style={{ textAlign: 'left', padding: '0.25rem' }}>BU</th>
                                                <th style={{ textAlign: 'right', padding: '0.25rem' }}>Rev</th>
                                                <th style={{ textAlign: 'right', padding: '0.25rem' }}>OpEx</th>
                                                <th style={{ textAlign: 'right', padding: '0.25rem' }}>SL</th>
                                            </tr></thead>
                                            <tbody>
                                                {current.bu_summary.map((b, i) => (
                                                    <tr key={i} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                                                        <td style={{ padding: '0.3rem', fontWeight: 600 }}>{b.bu_id}</td>
                                                        <td style={{ padding: '0.3rem', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>${b.revenue_m}M</td>
                                                        <td style={{ padding: '0.3rem', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>${b.opex_m}M</td>
                                                        <td style={{ padding: '0.3rem', textAlign: 'right', fontFamily: 'var(--font-mono)', color: b.social_license < 40 ? '#ef4444' : '#22c55e' }}>{b.social_license}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
