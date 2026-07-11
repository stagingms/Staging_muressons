'use client';
import { useState, useEffect } from 'react';
import styles from './CohortDiversityPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const VERTICALS = [
    { id: 'agriculture', label: 'Agriculture', icon: '🌾' },
    { id: 'banking_financial_services', label: 'Banking & Finance', icon: '🏦' },
    { id: 'oil_gas', label: 'Oil & Gas', icon: '⛽' },
    { id: 'retail_fmcg', label: 'Retail / FMCG', icon: '🛒' },
    { id: 'technology', label: 'Technology', icon: '💻' },
    { id: 'pharma', label: 'Pharma / Healthcare', icon: '💊' },
];

const REGIONS = [
    { id: 'asean', label: 'ASEAN', short: '🌏' },
    { id: 'south_asia', label: 'India', short: '🇮🇳' },
    { id: 'europe', label: 'Europe', short: '🇪🇺' },
    { id: 'north_america', label: 'N. America', short: '🇺🇸' },
    { id: 'africa', label: 'Africa', short: '🌍' },
];

/* ─── Helpers ─── */
function getMaxCount(distribution) {
    let max = 0;
    for (const row of Object.values(distribution)) {
        for (const count of Object.values(row)) {
            if (count > max) max = count;
        }
    }
    return max || 1;
}

function getCellBg(count, max) {
    if (!count) return 'transparent';
    const intensity = count / max;
    const alpha = 0.15 + intensity * 0.55;
    return `rgba(99,102,241,${alpha.toFixed(2)})`;
}

function HeatmapCell({ count, players, maxCount }) {
    const [showTooltip, setShowTooltip] = useState(false);
    const bg = getCellBg(count, maxCount);
    const textColor = count > 0 ? (count / maxCount > 0.6 ? '#fff' : '#818cf8') : 'var(--text-muted, #64748b)';

    return (
        <td
            className={styles.heatCell}
            style={{ background: bg, color: textColor }}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            <span className={styles.heatCount}>{count || '—'}</span>
            {showTooltip && players && players.length > 0 && (
                <div className={styles.tooltip}>
                    {players.map((p, i) => (
                        <div key={i} className={styles.tooltipPlayer}>
                            👤 {p.player_name || p.player_id || `Player ${i + 1}`}
                        </div>
                    ))}
                </div>
            )}
        </td>
    );
}

export default function CohortDiversityPanel({ sessionId }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!sessionId) { setLoading(false); return; }
        setLoading(true);
        setError('');

        fetch(`${API}/api/admin/${sessionId}/cohort-diversity`)
            .then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then(d => {
                setData(d);
                setLoading(false);
            })
            .catch(err => {
                setError(`Failed to load cohort diversity: ${err.message}`);
                setLoading(false);
            });
    }, [sessionId]);

    /* ─── States ─── */
    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.placeholder}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🗺️</div>
                    <p>Select a session to view cohort diversity breakdown.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loadingState}>
                    <div className={styles.spinner} />
                    <span>Loading diversity data…</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.container}>
                <div className={styles.errorState}>{error}</div>
            </div>
        );
    }

    if (!data) return null;

    /* ─── Compute summary stats ─── */
    const distribution = data.distribution || {};
    const maxCount = getMaxCount(distribution);
    const totalPlayers = data.total_players ?? 0;

    // Most common vertical
    const verticalTotals = VERTICALS.map(v => ({
        ...v,
        total: REGIONS.reduce((sum, r) => sum + (distribution[v.id]?.[r.id] || 0), 0),
    }));
    const mostCommonVertical = verticalTotals.reduce((a, b) => a.total >= b.total ? a : b, { total: 0, label: '—', icon: '' });

    // Most common region
    const regionTotals = REGIONS.map(r => ({
        ...r,
        total: VERTICALS.reduce((sum, v) => sum + (distribution[v.id]?.[r.id] || 0), 0),
    }));
    const mostCommonRegion = regionTotals.reduce((a, b) => a.total >= b.total ? a : b, { total: 0, label: '—', short: '' });

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h3 className={styles.title}>🗺️ Cohort Diversity — Industry × Region</h3>
                    <p className={styles.subtitle}>Hover cells to see player names</p>
                </div>
            </div>

            {/* Summary stats */}
            <div className={styles.statsRow}>
                <div className={styles.statItem}>
                    <span className={styles.statValue}>{totalPlayers}</span>
                    <span className={styles.statLabel}>Total Players</span>
                </div>
                <div className={styles.statDivider} />
                <div className={styles.statItem}>
                    <span className={styles.statValue}>{mostCommonVertical.icon} {mostCommonVertical.label}</span>
                    <span className={styles.statLabel}>Top Vertical ({mostCommonVertical.total})</span>
                </div>
                <div className={styles.statDivider} />
                <div className={styles.statItem}>
                    <span className={styles.statValue}>{mostCommonRegion.short} {mostCommonRegion.label}</span>
                    <span className={styles.statLabel}>Top Region ({mostCommonRegion.total})</span>
                </div>
            </div>

            {/* Heatmap table */}
            <div className={styles.tableWrapper}>
                <table className={styles.heatTable}>
                    <thead>
                        <tr>
                            <th className={styles.cornerCell}>Vertical \ Region</th>
                            {REGIONS.map(r => (
                                <th key={r.id} className={styles.colHeader}>
                                    <span className={styles.colFlag}>{r.short}</span>
                                    <span className={styles.colLabel}>{r.label}</span>
                                </th>
                            ))}
                            <th className={styles.colHeader} style={{ opacity: 0.6 }}>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {VERTICALS.map(v => {
                            const rowData = distribution[v.id] || {};
                            const rowTotal = REGIONS.reduce((sum, r) => sum + (rowData[r.id] || 0), 0);
                            return (
                                <tr key={v.id}>
                                    <td className={styles.rowHeader}>
                                        <span>{v.icon}</span>
                                        <span>{v.label}</span>
                                    </td>
                                    {REGIONS.map(r => (
                                        <HeatmapCell
                                            key={r.id}
                                            count={rowData[r.id] || 0}
                                            players={data.players?.[v.id]?.[r.id] || []}
                                            maxCount={maxCount}
                                        />
                                    ))}
                                    <td className={styles.rowTotal}>{rowTotal || '—'}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td className={styles.footerLabel}>Column Total</td>
                            {REGIONS.map(r => {
                                const colTotal = VERTICALS.reduce((sum, v) => sum + (distribution[v.id]?.[r.id] || 0), 0);
                                return <td key={r.id} className={styles.colTotal}>{colTotal || '—'}</td>;
                            })}
                            <td className={styles.grandTotal}>{totalPlayers}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            {/* Legend */}
            <div className={styles.legend}>
                <span className={styles.legendLabel}>Density:</span>
                {[0.2, 0.4, 0.6, 0.8, 1.0].map(intensity => (
                    <div
                        key={intensity}
                        className={styles.legendSwatch}
                        style={{ background: `rgba(99,102,241,${0.15 + intensity * 0.55})` }}
                        title={`~${Math.round(intensity * 100)}% of max`}
                    />
                ))}
                <span className={styles.legendLabel}>Low → High</span>
            </div>
        </div>
    );
}
