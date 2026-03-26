'use client';

import { useMemo } from 'react';
import styles from './DashboardHome.module.css';

export default function DashboardHome({ leaderboard = [], onNavigate }) {
    const stats = useMemo(() => {
        const cohorts = leaderboard.filter(s => !s.player_id);
        const players = leaderboard.filter(s => !!s.player_id);
        const allSessions = leaderboard;

        const avgTreasury = allSessions.length
            ? allSessions.reduce((sum, s) => sum + (s.total_cash || s.corporate_treasury || 0), 0) / allSessions.length
            : 0;
        const avgReputation = allSessions.length
            ? allSessions.reduce((sum, s) => sum + (s.group_reputation || 0), 0) / allSessions.length
            : 0;
        const avgRound = allSessions.length
            ? allSessions.reduce((sum, s) => sum + (s.round_number || 1), 0) / allSessions.length
            : 0;

        const lagging = allSessions.filter(s => (s.round_number || 1) < avgRound - 1);
        const lowTreasury = allSessions.filter(s => (s.total_cash || s.corporate_treasury || 0) < avgTreasury * 0.5);
        const lowRep = allSessions.filter(s => (s.group_reputation || 0) < 40);

        return {
            totalCohorts: cohorts.length,
            totalPlayers: players.length,
            totalSessions: allSessions.length,
            avgTreasury,
            avgReputation,
            avgRound: Math.round(avgRound * 10) / 10,
            lagging,
            lowTreasury,
            lowRep,
            alertCount: lagging.length + lowTreasury.length + lowRep.length,
        };
    }, [leaderboard]);

    const formatCurrency = (val) => {
        if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
        if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
        return `$${val.toFixed(0)}`;
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>📊 Dashboard Overview</h2>
                <p className={styles.subtitle}>At-a-glance summary of all active cohorts and sessions</p>
            </div>

            {/* ── Summary Cards ── */}
            <div className={styles.cardGrid}>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🏫</div>
                    <div className={styles.cardValue}>{stats.totalCohorts}</div>
                    <div className={styles.cardLabel}>Active Cohorts</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>👥</div>
                    <div className={styles.cardValue}>{stats.totalPlayers}</div>
                    <div className={styles.cardLabel}>Active Players</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🔄</div>
                    <div className={styles.cardValue}>{stats.avgRound}</div>
                    <div className={styles.cardLabel}>Avg. Round</div>
                </div>
                <div className={`${styles.card} ${stats.alertCount > 0 ? styles.cardAlert : ''}`}>
                    <div className={styles.cardIcon}>{stats.alertCount > 0 ? '⚠️' : '✅'}</div>
                    <div className={styles.cardValue}>{stats.alertCount}</div>
                    <div className={styles.cardLabel}>Active Alerts</div>
                </div>
            </div>


            {/* ── Alert Panels ── */}
            {stats.alertCount > 0 && (
                <div className={styles.alertSection}>
                    <h3 className={styles.alertTitle}>⚠️ Attention Required</h3>
                    <div className={styles.alertGrid}>
                        {stats.lagging.length > 0 && (
                            <div className={styles.alertCard}>
                                <div className={styles.alertCardIcon}>🐢</div>
                                <div>
                                    <strong>{stats.lagging.length} Lagging Team{stats.lagging.length > 1 ? 's' : ''}</strong>
                                    <p>Below average round progress</p>
                                </div>
                            </div>
                        )}
                        {stats.lowTreasury.length > 0 && (
                            <div className={styles.alertCard}>
                                <div className={styles.alertCardIcon}>💸</div>
                                <div>
                                    <strong>{stats.lowTreasury.length} Low Treasury</strong>
                                    <p>Below 50% of average treasury</p>
                                </div>
                            </div>
                        )}
                        {stats.lowRep.length > 0 && (
                            <div className={styles.alertCard}>
                                <div className={styles.alertCardIcon}>📉</div>
                                <div>
                                    <strong>{stats.lowRep.length} Low Reputation</strong>
                                    <p>Reputation below 40 threshold</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── Quick Actions ── */}
            <div className={styles.quickActions}>
                <h3 className={styles.sectionTitle}>Quick Actions</h3>
                <div className={styles.actionGrid}>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('leaderboard')}>
                        📋 View Leaderboard
                    </button>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('registry')}>
                        👥 Player Registry
                    </button>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('audit_trail')}>
                        📝 Audit Trail
                    </button>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('reports')}>
                        📊 Export Reports
                    </button>
                </div>
            </div>

            {/* ── Session Status Table ── */}
            {leaderboard.length > 0 && (
                <div className={styles.sessionTable}>
                    <h3 className={styles.sectionTitle}>Session Status</h3>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>Cohort / Player</th>
                                <th>Round</th>
                                <th>Treasury</th>
                                <th>Reputation</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {leaderboard.slice(0, 15).map(s => {
                                const round = s.round_number || 1;
                                const treasury = s.total_cash || s.corporate_treasury || 0;
                                const rep = s.group_reputation || 0;
                                const isLagging = round < stats.avgRound - 1;
                                const isLowCash = treasury < stats.avgTreasury * 0.5;
                                return (
                                    <tr key={s.session_id}>
                                        <td className={styles.cohortName}>{s.cohort_name || s.session_id?.slice(0, 12)}</td>
                                        <td><span className={styles.roundBadge}>R{round}</span></td>
                                        <td>{formatCurrency(treasury)}</td>
                                        <td>
                                            <span style={{ color: rep > 60 ? '#22c55e' : rep > 40 ? '#f59e0b' : '#ef4444' }}>
                                                {rep.toFixed(1)}
                                            </span>
                                        </td>
                                        <td>
                                            {isLagging ? <span className={styles.statusWarn}>⚠️ Lagging</span>
                                            : isLowCash ? <span className={styles.statusWarn}>💸 Low Cash</span>
                                            : <span className={styles.statusOk}>✅ On Track</span>}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {leaderboard.length === 0 && (
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>🎓</div>
                    <h3>No Active Sessions</h3>
                    <p>Create a cohort from the Leaderboard tab to get started.</p>
                </div>
            )}
        </div>
    );
}
