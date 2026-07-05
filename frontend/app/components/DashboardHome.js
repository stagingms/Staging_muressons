'use client';

import { useMemo, useState, useEffect } from 'react';
import styles from './DashboardHome.module.css';
import { formatSessionId } from '../utils/sessionUtils';
import { fmtCompact } from '../utils/formatCurrency';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// F6: absolute pedagogical thresholds — alerts must not depend on the
// cross-cohort average (a healthy room with one rich cohort would flag
// everyone else). Starting treasury is $50M; below $10M is genuinely low.
const TREASURY_FLOOR = 10_000_000;
const REPUTATION_FLOOR = 40;

export default function DashboardHome({ leaderboard = [], onNavigate, onCreateCohort, selectedSession = null }) {
    const stats = useMemo(() => {
        const cohorts = leaderboard.filter(s => !s.player_id);
        const players = leaderboard.filter(s => !!s.player_id);
        const allSessions = leaderboard;

        const avgRound = allSessions.length
            ? allSessions.reduce((sum, s) => sum + (s.round_number || 1), 0) / allSessions.length
            : 0;

        // F6: evaluate each *team* exactly once. A "team" is a player
        // sub-session; a cohort row only counts as a team when it has no
        // player sub-sessions (i.e. the cohort session is played directly).
        const cohortIdsWithPlayers = new Set(players.map(p => p.parent_cohort_id).filter(Boolean));
        const cohortRoundById = new Map(cohorts.map(c => [c.session_id, c.round_number || 1]));
        const teams = [
            ...players,
            ...cohorts.filter(c => !cohortIdsWithPlayers.has(c.session_id)),
        ];

        // One entry per team, with all of its alert flags (no double counting).
        const alertTeams = [];
        for (const t of teams) {
            const flags = [];
            const treasury = t.total_cash || t.corporate_treasury || 0;
            const rep = t.group_reputation || 0;
            // Lagging is relative to the team's own cohort round, not a global mean.
            const cohortRound = t.parent_cohort_id ? cohortRoundById.get(t.parent_cohort_id) : null;
            if (cohortRound && (t.round_number || 1) < cohortRound - 1) flags.push('lagging');
            if (treasury < TREASURY_FLOOR) flags.push('lowTreasury');
            if (rep < REPUTATION_FLOOR) flags.push('lowRep');
            if (flags.length) alertTeams.push({ session: t, flags });
        }

        const lagging = alertTeams.filter(a => a.flags.includes('lagging'));
        const lowTreasury = alertTeams.filter(a => a.flags.includes('lowTreasury'));
        const lowRep = alertTeams.filter(a => a.flags.includes('lowRep'));

        return {
            totalCohorts: cohorts.length,
            totalPlayers: players.length,
            totalSessions: allSessions.length,
            avgRound: Math.round(avgRound * 10) / 10,
            lagging,
            lowTreasury,
            lowRep,
            // A team with several problems is still one team needing attention.
            alertCount: alertTeams.length,
        };
    }, [leaderboard]);

    // EX-3: Uses standardized formatCurrency utility
    const formatCurrency = fmtCompact;

    // ── Round Briefing Data ──
    // F3: key the directive card to the cohort being facilitated, never the
    // global max round (which could belong to a different facilitator's
    // cohort). Priority: explicitly selected cohort → the only cohort →
    // fallback to latest round with an explicit "across all cohorts" label.
    const briefingTarget = useMemo(() => {
        const cohorts = leaderboard.filter(s => !s.player_id);
        const selected = cohorts.find(s => s.session_id === selectedSession);
        if (selected) return { cohort: selected, round: selected.round_number || 1 };
        if (cohorts.length === 1) return { cohort: cohorts[0], round: cohorts[0].round_number || 1 };
        if (!leaderboard.length) return { cohort: null, round: 1 };
        return { cohort: null, round: Math.max(...leaderboard.map(s => s.round_number || 1)) };
    }, [leaderboard, selectedSession]);
    const currentRound = briefingTarget.round;

    const [briefingScript, setBriefingScript] = useState(null);

    useEffect(() => {
        fetch(`${API}/api/admin/teleprompter`)
            .then(r => r.json())
            .then(d => {
                const scripts = d.scripts || {};
                setBriefingScript(scripts);
            })
            .catch(() => {});
    }, []);

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
                    <h3 className={styles.alertTitle}>⚠️ Attention Required — {stats.alertCount} team{stats.alertCount > 1 ? 's' : ''}</h3>
                    <div className={styles.alertGrid}>
                        {stats.lagging.length > 0 && (
                            <div
                                className={styles.alertCard}
                                role="button"
                                tabIndex={0}
                                style={{ cursor: 'pointer' }}
                                title={stats.lagging.map(a => a.session.cohort_name || a.session.session_id).join(', ')}
                                onClick={() => onNavigate?.('leaderboard')}
                                onKeyDown={e => e.key === 'Enter' && onNavigate?.('leaderboard')}
                            >
                                <div className={styles.alertCardIcon}>🐢</div>
                                <div>
                                    <strong>{stats.lagging.length} Lagging Team{stats.lagging.length > 1 ? 's' : ''}</strong>
                                    <p>More than 1 round behind their cohort — view in Leaderboard</p>
                                </div>
                            </div>
                        )}
                        {stats.lowTreasury.length > 0 && (
                            <div
                                className={styles.alertCard}
                                role="button"
                                tabIndex={0}
                                style={{ cursor: 'pointer' }}
                                title={stats.lowTreasury.map(a => a.session.cohort_name || a.session.session_id).join(', ')}
                                onClick={() => onNavigate?.('leaderboard')}
                                onKeyDown={e => e.key === 'Enter' && onNavigate?.('leaderboard')}
                            >
                                <div className={styles.alertCardIcon}>💸</div>
                                <div>
                                    <strong>{stats.lowTreasury.length} Low Treasury</strong>
                                    <p>Below {fmtCompact(TREASURY_FLOOR)} floor — view in Leaderboard</p>
                                </div>
                            </div>
                        )}
                        {stats.lowRep.length > 0 && (
                            <div
                                className={styles.alertCard}
                                role="button"
                                tabIndex={0}
                                style={{ cursor: 'pointer' }}
                                title={stats.lowRep.map(a => a.session.cohort_name || a.session.session_id).join(', ')}
                                onClick={() => onNavigate?.('leaderboard')}
                                onKeyDown={e => e.key === 'Enter' && onNavigate?.('leaderboard')}
                            >
                                <div className={styles.alertCardIcon}>📉</div>
                                <div>
                                    <strong>{stats.lowRep.length} Low Reputation</strong>
                                    <p>Reputation below {REPUTATION_FLOOR} threshold — view in Leaderboard</p>
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
                    {onCreateCohort && (
                        <button className={styles.actionBtn} onClick={() => onCreateCohort()}>
                            🚀 Create New Cohort
                        </button>
                    )}
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('leaderboard')}>
                        📋 View Leaderboard
                    </button>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('registry')}>
                        👥 Player Registry
                    </button>
                    {/* F9: was 'audit_trail' — a tab id that no longer exists in the
                        facilitator sidebar (merged into Decision History). Navigating
                        there broke the breadcrumb and nav highlight. */}
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('decision_replay')}>
                        🕰️ Decision History
                    </button>
                    <button className={styles.actionBtn} onClick={() => onNavigate?.('reports')}>
                        📊 Export Reports
                    </button>
                </div>
            </div>

            {/* ── Round Briefing Card ── */}
            {briefingScript && briefingScript[String(currentRound)] && (() => {
                const script = briefingScript[String(currentRound)];
                return (
                    <div className={styles.briefingCard}>
                        <div className={styles.briefingHeader}>
                            <div className={styles.briefingRoundBadge}>R{currentRound}</div>
                            <div style={{ flex: 1 }}>
                                <div className={styles.briefingDirectiveLabel}>
                                    ROUND {currentRound} DIRECTIVE
                                    {' — '}
                                    {briefingTarget.cohort
                                        ? (briefingTarget.cohort.cohort_name || formatSessionId(briefingTarget.cohort))
                                        : 'latest round across all cohorts (select a cohort to pin)'}
                                </div>
                                <h3 className={styles.briefingTitle}>{script.title}</h3>
                            </div>
                            <button
                                className={styles.briefingOpenBtn}
                                onClick={() => onNavigate?.('teleprompter')}
                                title="Open full Teleprompter"
                            >
                                🎤 Full Teleprompter →
                            </button>
                        </div>

                        <div className={styles.briefingGrid}>
                            {/* Talking Points */}
                            <div className={styles.briefingSection}>
                                <div className={styles.briefingSectionLabel}>
                                    <span>💬</span> Talking Points
                                </div>
                                <ul className={styles.briefingList}>
                                    {(script.talking_points || []).slice(0, 4).map((pt, i) => (
                                        <li key={i}>{pt}</li>
                                    ))}
                                </ul>
                                {(script.talking_points || []).length > 4 && (
                                    <div className={styles.briefingMore}>+{script.talking_points.length - 4} more</div>
                                )}
                            </div>

                            {/* Right column: Engines + Discussion */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {/* Engines */}
                                {script.engines_likely?.length > 0 && (
                                    <div className={styles.briefingSection}>
                                        <div className={styles.briefingSectionLabel}>
                                            <span>⚙️</span> Engines Likely to Fire
                                        </div>
                                        <div className={styles.briefingEngines}>
                                            {script.engines_likely.map((eng, i) => (
                                                <span key={i} className={styles.engineChip}>{eng}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Discussion Prompts */}
                                {script.discussion_prompts?.length > 0 && (
                                    <div className={styles.briefingSection}>
                                        <div className={styles.briefingSectionLabel}>
                                            <span>🗣️</span> Discussion Prompts
                                        </div>
                                        <div className={styles.briefingPrompts}>
                                            {script.discussion_prompts.slice(0, 2).map((p, i) => (
                                                <div key={i} className={styles.promptQuote}>&ldquo;{p}&rdquo;</div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })()}

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
                                // F6: same absolute thresholds as the alert cards, so the
                                // table's status column and the alert counts always agree.
                                const isLagging = stats.lagging.some(a => a.session.session_id === s.session_id);
                                const isLowCash = treasury < TREASURY_FLOOR;
                                return (
                                    <tr key={s.session_id}>
                                         <td className={styles.cohortName}>{s.cohort_name || formatSessionId(s)}</td>
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


        </div>
    );
}
