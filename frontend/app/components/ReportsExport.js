'use client';

import { useMemo, useState } from 'react';
import styles from './ReportsExport.module.css';

export default function ReportsExport({ leaderboard = [] }) {
    const [exportFormat, setExportFormat] = useState('csv');

    const formatCurrency = (val) => val >= 1e6 ? `$${(val / 1e6).toFixed(1)}M` : `$${val?.toFixed(0) || '0'}`;

    const reportData = useMemo(() => leaderboard.map(s => ({
        cohort: s.cohort_name || s.session_id?.slice(0, 16),
        session_id: s.session_id,
        round: s.round_number || 1,
        treasury: s.total_cash || s.corporate_treasury || 0,
        reputation: s.group_reputation || 0,
        synergy: s.synergy_multiplier || 1,
        facilitator: s.facilitator_id || 'N/A',
        created: s.created_at || '',
    })), [leaderboard]);

    const handleExportCSV = () => {
        const headers = ['Cohort', 'Session ID', 'Round', 'Treasury', 'Reputation', 'Synergy', 'Facilitator', 'Created'];
        const rows = reportData.map(d => [d.cohort, d.session_id, d.round, d.treasury, d.reputation.toFixed(1), d.synergy.toFixed(3), d.facilitator, d.created]);
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `muressons_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click(); URL.revokeObjectURL(url);
    };

    const handleExportJSON = () => {
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `muressons_report_${new Date().toISOString().slice(0, 10)}.json`;
        a.click(); URL.revokeObjectURL(url);
    };

    const stats = useMemo(() => {
        if (!reportData.length) return null;
        const treasuries = reportData.map(d => d.treasury);
        const reputations = reportData.map(d => d.reputation);
        return {
            avgTreasury: treasuries.reduce((a, b) => a + b, 0) / treasuries.length,
            maxTreasury: Math.max(...treasuries),
            minTreasury: Math.min(...treasuries),
            avgRep: reputations.reduce((a, b) => a + b, 0) / reputations.length,
            maxRep: Math.max(...reputations),
            minRep: Math.min(...reputations),
        };
    }, [reportData]);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📊</span>
                <div>
                    <h2 className={styles.title}>Reports & Export</h2>
                    <p className={styles.subtitle}>Download session data and cross-cohort comparison reports.</p>
                </div>
            </div>

            {/* ── Export Buttons ── */}
            <div className={styles.exportRow}>
                <button className={styles.exportBtn} onClick={handleExportCSV} disabled={!reportData.length}>
                    📄 Export CSV
                </button>
                <button className={styles.exportBtn} onClick={handleExportJSON} disabled={!reportData.length}>
                    📋 Export JSON
                </button>
                <span className={styles.recordCount}>{reportData.length} session{reportData.length !== 1 ? 's' : ''}</span>
            </div>

            {/* ── Summary Stats ── */}
            {stats && (
                <div className={styles.statsGrid}>
                    <div className={styles.statCard}><div className={styles.statLabel}>Avg Treasury</div><div className={styles.statValue}>{formatCurrency(stats.avgTreasury)}</div></div>
                    <div className={styles.statCard}><div className={styles.statLabel}>Best Treasury</div><div className={styles.statValue}>{formatCurrency(stats.maxTreasury)}</div></div>
                    <div className={styles.statCard}><div className={styles.statLabel}>Worst Treasury</div><div className={styles.statValue}>{formatCurrency(stats.minTreasury)}</div></div>
                    <div className={styles.statCard}><div className={styles.statLabel}>Avg Reputation</div><div className={styles.statValue}>{stats.avgRep.toFixed(1)}</div></div>
                    <div className={styles.statCard}><div className={styles.statLabel}>Best Reputation</div><div className={styles.statValue}>{stats.maxRep.toFixed(1)}</div></div>
                    <div className={styles.statCard}><div className={styles.statLabel}>Worst Reputation</div><div className={styles.statValue}>{stats.minRep.toFixed(1)}</div></div>
                </div>
            )}

            {/* ── Data Table ── */}
            {reportData.length > 0 ? (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>Cohort</th>
                                <th>Round</th>
                                <th>Treasury</th>
                                <th>Reputation</th>
                                <th>Synergy</th>
                                <th>Facilitator</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reportData.map(d => (
                                <tr key={d.session_id}>
                                    <td className={styles.cohortName}>{d.cohort}</td>
                                    <td><span className={styles.roundBadge}>R{d.round}</span></td>
                                    <td>{formatCurrency(d.treasury)}</td>
                                    <td style={{ color: d.reputation > 60 ? '#22c55e' : d.reputation > 40 ? '#f59e0b' : '#ef4444' }}>{d.reputation.toFixed(1)}</td>
                                    <td>{d.synergy.toFixed(3)}</td>
                                    <td className={styles.facId}>{d.facilitator}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className={styles.empty}>No session data available for export.</div>
            )}
        </div>
    );
}
