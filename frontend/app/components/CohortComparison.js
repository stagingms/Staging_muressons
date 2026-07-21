'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function CohortComparison({ facilitatorId }) {
    const [cohorts, setCohorts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState('treasury_m');

    useEffect(() => {
        const url = facilitatorId
            ? `${API}/api/admin/cohort-comparison?facilitator_id=${facilitatorId}`
            : `${API}/api/admin/cohort-comparison`;
        fetch(url).then(r => r.json()).then(d => { setCohorts(d.cohorts || []); setLoading(false); }).catch(() => setLoading(false));
    }, [facilitatorId]);

    const sorted = [...cohorts].sort((a, b) => {
        if (sortBy === 'cohort_name') return a.cohort_name.localeCompare(b.cohort_name);
        return (b[sortBy] || 0) - (a[sortBy] || 0);
    });

    const COLS = [
        { key: 'cohort_name', label: 'Cohort', fmt: v => v },
        { key: 'round', label: 'Round', fmt: v => `${v}/10` },
        { key: 'treasury_m', label: 'Treasury ($M)', fmt: v => `$${v.toFixed(2)}M` },
        { key: 'reputation', label: 'Reputation', fmt: v => v.toFixed(1) },
        { key: 'ebitda_m', label: 'EBITDA ($M)', fmt: v => `$${v.toFixed(2)}M` },
        { key: 'synergy', label: 'Synergy', fmt: v => `${v}x` },
        { key: 'cost_of_capital', label: 'CoC', fmt: v => `${(v * 100).toFixed(1)}%` },
        { key: 'active_crises', label: 'Crises', fmt: v => v },
    ];

    if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading comparison...</div>;
    if (cohorts.length === 0) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No cohorts available for comparison</div>;

    return (
        <div style={{ padding: '1.5rem' }}>
            <h2 style={{ margin: '0 0 1rem', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>📊 Cohort Comparison</h2>

            <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: '12px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                        <tr style={{ background: 'var(--bg-body)' }}>
                            {COLS.map(col => (
                                <th key={col.key} onClick={() => setSortBy(col.key)} style={{
                                    padding: '0.75rem 1rem', textAlign: col.key === 'cohort_name' ? 'left' : 'center',
                                    cursor: 'pointer', borderBottom: '2px solid var(--border-subtle)',
                                    color: sortBy === col.key ? '#3b82f6' : 'var(--text-muted)',
                                    fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em',
                                    whiteSpace: 'nowrap', userSelect: 'none',
                                }}>
                                    {col.label} {sortBy === col.key ? '▼' : ''}
                                </th>
                            ))}
                            <th style={{ padding: '0.75rem 1rem', textAlign: 'center', borderBottom: '2px solid var(--border-subtle)', color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.75rem' }}>FLAGS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sorted.map((c, i) => {
                            const isTop = i === 0;
                            return (
                                <tr key={c.session_id} style={{ background: isTop ? 'rgba(34,197,94,0.04)' : 'var(--bg-card)', borderBottom: '1px solid var(--border-subtle)' }}>
                                    {COLS.map(col => {
                                        let cellColor = 'var(--text-primary)';
                                        if (col.key === 'treasury_m' && c.treasury_m < 0) cellColor = '#ef4444';
                                        if (col.key === 'reputation' && c.reputation < 30) cellColor = '#ef4444';
                                        if (col.key === 'active_crises' && c.active_crises >= 3) cellColor = '#ef4444';
                                        return (
                                            <td key={col.key} style={{
                                                padding: '0.75rem 1rem', fontWeight: col.key === 'cohort_name' ? 600 : 500,
                                                textAlign: col.key === 'cohort_name' ? 'left' : 'center',
                                                color: cellColor, fontFamily: col.key !== 'cohort_name' ? 'var(--font-mono)' : undefined,
                                            }}>
                                                {isTop && col.key === 'cohort_name' && '🏆 '}
                                                {col.fmt(c[col.key])}
                                            </td>
                                        );
                                    })}
                                    <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                        <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                                            {c.greenwashing && <span title="Greenwashing" style={{ fontSize: '0.9rem' }}>🌿🚨</span>}
                                            {c.lockin && <span title="Tech Lock-In" style={{ fontSize: '0.9rem' }}>🔒</span>}
                                            {c.fog && <span title="Fog of War" style={{ fontSize: '0.9rem' }}>🌫️</span>}
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
