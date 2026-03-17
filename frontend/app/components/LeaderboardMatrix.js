'use client';

import { useState } from 'react';
import styles from './LeaderboardMatrix.module.css';
import { Abbr } from './Glossary';
import CreateCohortModal from './CreateCohortModal';

/**
 * LeaderboardMatrix — God Mode cohort leaderboard.
 * Columns: Terminal Value, Total Cash, Synergy, Risk Heatmap, Talent Flight Risk
 *
 * Props:
 *  - leaderboard: array of session metrics from GET /api/admin/leaderboard
 *  - onSelectSession: (sessionId) => void
 */
export default function LeaderboardMatrix({
    leaderboard = [],
    onSelectSession,
    onDeleteSession,
    onSessionCreated,
    selectedSession,
}) {
    const [createOpen, setCreateOpen] = useState(false);

    const riskColor = (value, inverse = false) => {
        const v = inverse ? 100 - value : value;
        if (v > 66) return styles.riskHigh;
        if (v > 33) return styles.riskMed;
        return styles.riskLow;
    };

    const handleCreated = (newSession) => {
        setCreateOpen(false);
        onSessionCreated?.(newSession);
    };

    return (
        <section className={styles.matrix}>
            <div className={styles.header}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={styles.icon}>🏆</span>
                    <h2>Player Leaderboard</h2>
                    <span className={styles.count}>{leaderboard.length} players</span>
                </div>
                <button className={styles.createBtn} onClick={() => setCreateOpen(true)}>+ Set Up Cohort</button>
            </div>

            <CreateCohortModal
                isOpen={createOpen}
                onClose={() => setCreateOpen(false)}
                onCreated={handleCreated}
            />

            <div className={styles.tableWrap}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th className={styles.rank}>#</th>
                            <th>Cohort</th>
                            <th>Player</th>
                            <th>Round</th>
                            <th>Terminal Value</th>
                            <th>Total Cash</th>
                            <th>Synergy</th>
                            <th title="Reputation — public perception score">Reputation</th>
                            <th className={styles.heatCol}><Abbr term="NCD">NCD Risk</Abbr></th>
                            <th className={styles.heatCol}><Abbr term="SL">Social License</Abbr></th>
                            <th>Talent Risk</th>
                            <th className={styles.actionCol}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {leaderboard.map((sess, i) => (
                            <tr
                                key={sess.session_id}
                                className={`${styles.row} ${sess.session_id === selectedSession ? styles.selectedRow : ''}`}
                                onClick={() => onSelectSession?.(sess.session_id)}
                                style={{ animationDelay: `${i * 50}ms` }}
                            >
                                <td className={styles.rank}>
                                    <span className={i === 0 ? styles.gold : i === 1 ? styles.silver : i === 2 ? styles.bronze : ''}>
                                        {i + 1}
                                    </span>
                                </td>
                                <td className={styles.cohortName}>{sess.cohort_name}</td>
                                <td className={styles.mono}>{sess.player_id || '–'}</td>
                                <td className={styles.mono}>{sess.round_number}/10</td>
                                <td className={styles.mono}>
                                    ${(sess.terminal_value / 1_000_000).toFixed(1)}M
                                </td>
                                <td className={styles.mono}>
                                    ${(sess.total_cash / 1_000_000).toFixed(1)}M
                                </td>
                                <td className={styles.mono}>
                                    {sess.group_synergy.toFixed(2)}×
                                </td>
                                <td className={styles.mono}>
                                    {sess.group_reputation.toFixed(0)}
                                </td>
                                <td>
                                    <div className={`${styles.heatCell} ${riskColor(sess.avg_natural_capital_debt)}`}>
                                        {sess.avg_natural_capital_debt.toFixed(1)}
                                    </div>
                                </td>
                                <td>
                                    <div className={`${styles.heatCell} ${riskColor(sess.avg_social_license, true)}`}>
                                        {sess.avg_social_license.toFixed(1)}
                                    </div>
                                </td>
                                <td>
                                    {sess.talent_flight_risk ? (
                                        <span className={styles.flightRisk}>
                                            ⚠️ {sess.talent_penalty_multiplier.toFixed(2)}×
                                        </span>
                                    ) : (
                                        <span className={styles.safe}>✓ Safe</span>
                                    )}
                                </td>
                                <td className={styles.actionCol}>
                                    <button
                                        className={styles.deleteBtn}
                                        title={sess.player_id ? `Remove player ${sess.player_id}` : "Delete this session"}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            const label = sess.player_id
                                                ? `${sess.cohort_name} — Player ${sess.player_id}`
                                                : sess.cohort_name;
                                            onDeleteSession?.(sess.session_id, label);
                                        }}
                                    >
                                        🗑️
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {leaderboard.length === 0 && (
                            <tr>
                                <td colSpan={12} className={styles.empty}>
                                    No active sessions. Start a simulation to see the leaderboard.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
