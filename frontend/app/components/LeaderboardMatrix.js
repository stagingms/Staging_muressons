'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './LeaderboardMatrix.module.css';
import { Abbr } from './Glossary';
import { fmtM } from '../utils/formatCurrency';

const API = process.env.NEXT_PUBLIC_API_URL || '';

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
    selectedSession,
}) {

    const [practiceStates, setPracticeStates] = useState({}); // {session_id: true/false}
    const [loadingPractice, setLoadingPractice] = useState({});

    // Fetch practice mode status for all top-level cohorts
    const fetchPracticeStates = useCallback(async () => {
        const cohorts = leaderboard.filter(s => !s.player_id);
        const states = {};
        for (const cohort of cohorts) {
            try {
                const res = await fetch(`${API}/api/admin/sessions/${cohort.session_id}/practice-mode`);
                if (res.ok) {
                    const data = await res.json();
                    states[cohort.session_id] = data.practice_mode;
                }
            } catch { /* ignore */ }
        }
        setPracticeStates(prev => ({ ...prev, ...states }));
    }, [leaderboard]);

    useEffect(() => {
        if (leaderboard.length > 0) fetchPracticeStates();
    }, [leaderboard, fetchPracticeStates]);

    const togglePractice = async (sessionId) => {
        const isActive = practiceStates[sessionId];
        setLoadingPractice(prev => ({ ...prev, [sessionId]: true }));
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/practice-mode`, {
                method: isActive ? 'DELETE' : 'POST',
            });
            if (res.ok) {
                setPracticeStates(prev => ({ ...prev, [sessionId]: !isActive }));
            }
        } catch { /* ignore */ }
        setLoadingPractice(prev => ({ ...prev, [sessionId]: false }));
    };

    const riskColor = (value, inverse = false) => {
        const v = inverse ? 100 - value : value;
        if (v > 66) return styles.riskHigh;
        if (v > 33) return styles.riskMed;
        return styles.riskLow;
    };



    return (
        <section className={styles.matrix}>
            <div className={styles.header}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={styles.icon}>🏆</span>
                    <h2>Player Leaderboard</h2>
                    <span className={styles.count}>{leaderboard.length} players</span>
                </div>
            </div>

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
                            <th title="Bonus points from quizzes & learning">Bonus</th>
                            <th className={styles.heatCol}><Abbr term="NCD">NCD Risk</Abbr></th>
                            <th className={styles.heatCol}><Abbr term="SL">Social License</Abbr></th>
                            <th>Talent Risk</th>
                            <th>Practice</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {leaderboard.map((sess, i) => {
                            const isCohort = !sess.player_id;
                            const isPractice = practiceStates[sess.session_id];
                            const isLoading = loadingPractice[sess.session_id];

                            return (
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
                                    <td className={styles.cohortName}>
                                        {isPractice && <span title="Practice Mode Active" style={{ marginRight: '4px' }}>🎓</span>}
                                        {sess.cohort_name}
                                    </td>
                                    <td className={styles.mono}>{sess.player_id || '–'}</td>
                                    <td className={styles.mono}>{sess.round_number}/10</td>
                                    <td className={styles.mono}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <span>{fmtM(sess.terminal_value)}</span>
                                            {sess.sparkline && sess.sparkline.length > 1 && (
                                                <svg width="60" height="20" viewBox={`0 0 60 20`} style={{ overflow: 'visible' }}>
                                                    <polyline
                                                        fill="none"
                                                        stroke={sess.sparkline[sess.sparkline.length - 1] >= sess.sparkline[0] ? "#10b981" : "#ef4444"}
                                                        strokeWidth="1.5"
                                                        points={sess.sparkline.map((val, idx) => {
                                                            const min = Math.min(...sess.sparkline);
                                                            const max = Math.max(...sess.sparkline);
                                                            const range = max - min || 1;
                                                            const x = (idx / (sess.sparkline.length - 1)) * 60;
                                                            const y = 20 - ((val - min) / range) * 20;
                                                            return `${x},${y}`;
                                                        }).join(' ')}
                                                    />
                                                </svg>
                                            )}
                                        </div>
                                    </td>
                                    <td className={styles.mono}>
                                        {fmtM(sess.total_cash)}
                                    </td>
                                    <td className={styles.mono}>
                                        {sess.group_synergy.toFixed(2)}×
                                    </td>
                                    <td className={styles.mono}>
                                        {sess.group_reputation.toFixed(0)}
                                    </td>
                                    <td className={styles.mono} style={{ color: sess.bonus_score > 0 ? '#059669' : '#94a3b8' }}>
                                        {sess.bonus_score > 0 ? `🏅 ${(sess.bonus_score || 0).toLocaleString()}` : '–'}
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
                                    <td>
                                        {isCohort ? (
                                            <button
                                                className={`${styles.practiceBtn} ${isPractice ? styles.practiceBtnActive : ''}`}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    togglePractice(sess.session_id);
                                                }}
                                                disabled={isLoading}
                                                title={isPractice
                                                    ? 'Practice mode active — rounds capped at 2, then auto-reset'
                                                    : 'Enable practice mode (max 2 rounds, then reset)'}
                                            >
                                                {isLoading ? '⏳' : isPractice ? '🎓 ON' : 'OFF'}
                                            </button>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        )}
                                    </td>
                                    <td>
                                        {isCohort && onDeleteSession ? (
                                            <div style={{ display: 'flex', gap: '4px' }}>
                                                <button
                                                    className={styles.actionBtn}
                                                    onClick={(e) => { e.stopPropagation(); onDeleteSession(sess.session_id, sess.cohort_name, false); }}
                                                    title="Soft delete — recoverable for 7 days"
                                                    style={{ color: '#f59e0b', borderColor: 'rgba(245,158,11,0.3)' }}
                                                >
                                                    📦
                                                </button>
                                                <button
                                                    className={styles.actionBtn}
                                                    onClick={(e) => { e.stopPropagation(); onDeleteSession(sess.session_id, sess.cohort_name, true); }}
                                                    title="Hard delete — permanently remove all data"
                                                    style={{ color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}
                                                >
                                                    🗑️
                                                </button>
                                            </div>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                        {leaderboard.length === 0 && (
                            <tr>
                                <td colSpan={14} className={styles.empty}>
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
