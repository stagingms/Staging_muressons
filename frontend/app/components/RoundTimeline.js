'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import styles from './RoundTimeline.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const ROUNDS = Array.from({ length: 10 }, (_, i) => i + 1);

/**
 * F5: Round labels are sourced from the same backend teleprompter scripts the
 * facilitator reads from — NOT hardcoded here. A previous hardcoded map had
 * drifted ("Water Crisis", "Data Ethics", …) and contradicted the actual round
 * content on the same screen. Fallback when the fetch fails: round number only.
 */
function shortRoundTitle(raw) {
    if (!raw || typeof raw !== 'string') return '';
    // Strip a leading "Round N:" / "Round N —" prefix, keep the segment before
    // any em-dash subtitle, then truncate for the node footprint.
    let t = raw.replace(/^round\s*\d+\s*[:—–-]\s*/i, '').split('—')[0].trim();
    if (t.length > 24) t = `${t.slice(0, 23).trimEnd()}…`;
    return t;
}

export default function RoundTimeline({ sessionId, leaderboard = [] }) {
    const [pacingMap, setPacingMap] = useState({});
    const [roundTitles, setRoundTitles] = useState({});

    // Single source of truth for round names (same endpoint the Teleprompter
    // and the Dashboard briefing card already use).
    useEffect(() => {
        fetch(`${API}/api/admin/teleprompter`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (!d?.scripts) return;
                const titles = {};
                Object.entries(d.scripts).forEach(([round, s]) => {
                    titles[round] = shortRoundTitle(s?.title);
                });
                setRoundTitles(titles);
            })
            .catch(() => { /* fallback: nodes show round numbers only */ });
    }, []);

    // ── Derive cohort groups from leaderboard ──
    const cohorts = useMemo(() => {
        // Cohort sessions = entries without player_id
        const cohortSessions = leaderboard.filter(s => !s.player_id);
        // Player sessions = entries with player_id
        const playerSessions = leaderboard.filter(s => !!s.player_id);

        if (cohortSessions.length === 0) return [];

        return cohortSessions.map(cohort => {
            // Find all player sessions that belong to this cohort
            const players = playerSessions.filter(
                p => p.cohort_name === cohort.cohort_name ||
                     p.session_id?.startsWith?.(cohort.session_id?.slice(0, 8))
            );
            return {
                ...cohort,
                playerCount: players.length,
                players,
            };
        });
    }, [leaderboard]);

    // ── Fetch pacing for all cohort sessions ──
    const fetchAllPacing = useCallback(async () => {
        const cohortSessions = leaderboard.filter(s => !s.player_id);
        if (!cohortSessions.length) return;

        const results = {};
        await Promise.all(
            cohortSessions.map(async (s) => {
                try {
                    const res = await fetch(`${API}/api/admin/sessions/${s.session_id}/pacing`, { credentials: 'include' });  // F-21: now a guarded read
                    if (res.ok) {
                        results[s.session_id] = await res.json();
                    }
                } catch { /* offline */ }
            })
        );
        setPacingMap(results);
    }, [leaderboard]);

    useEffect(() => { fetchAllPacing(); }, [fetchAllPacing]);

    // ── Round status logic ──
    const getRoundStatus = (roundNum, currentRound, unlockedRound) => {
        if (roundNum < currentRound) return 'completed';
        if (roundNum === currentRound) return 'active';
        if (roundNum <= unlockedRound) return 'unlocked';
        return 'locked';
    };

    // Progress percentage for the cohort
    const getProgress = (currentRound) => Math.min(100, Math.round(((currentRound - 1) / 10) * 100));

    // ── No cohorts state ──
    if (cohorts.length === 0) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <span className={styles.icon}>📅</span>
                    <div>
                        <h2 className={styles.title}>Round Timeline</h2>
                        <p className={styles.subtitle}>Visual progress through the 10-round simulation</p>
                    </div>
                </div>
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>📋</div>
                    <h3 className={styles.emptyTitle}>No Active Cohorts</h3>
                    <p className={styles.emptyText}>Create a cohort from the Dashboard or Player Registry to track round progress here.</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📅</span>
                <div>
                    <h2 className={styles.title}>Round Timeline</h2>
                    <p className={styles.subtitle}>Per-cohort progress through the 10-round simulation</p>
                </div>
                <div className={styles.headerMeta}>
                    <span className={styles.cohortCount}>{cohorts.length} Cohort{cohorts.length !== 1 ? 's' : ''}</span>
                </div>
            </div>

            {/* ── Legend ── */}
            <div className={styles.legend}>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendComplete}`} /> Completed</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendActive}`} /> Active</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendUnlocked}`} /> Unlocked</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendLocked}`} /> Locked</span>
            </div>

            {/* ── Per-Cohort Timeline Cards ── */}
            <div className={styles.cohortList}>
                {cohorts.map(cohort => {
                    const pacing = pacingMap[cohort.session_id];
                    const unlockedRound = pacing?.unlocked_round ?? cohort.max_unlocked_round ?? 999;
                    const currentRound = cohort.round_number || 1;
                    const progress = getProgress(currentRound);
                    const isSelected = sessionId === cohort.session_id;
                    const isComplete = currentRound > 10;
                    const pacingMode = pacing?.mode || cohort.pacing_mode || 'free_play';

                    return (
                        <div
                            key={cohort.session_id}
                            className={`${styles.cohortSection} ${isSelected ? styles.cohortSelected : ''} ${isComplete ? styles.cohortComplete : ''}`}
                        >
                            {/* ── Cohort Header ── */}
                            <div className={styles.cohortHeader}>
                                <span className={styles.cohortName}>
                                    {cohort.cohort_name || formatSessionId(cohort)}
                                </span>
                                <span className={styles.cohortRoundBadge}>
                                    {isComplete ? '✅ Complete' : `R${currentRound} / 10`}
                                </span>
                                {cohort.playerCount > 0 && (
                                    <span className={styles.cohortPlayerBadge}>
                                        👥 {cohort.playerCount} Player{cohort.playerCount !== 1 ? 's' : ''}
                                    </span>
                                )}
                                <span className={styles.cohortPacing}>
                                    {pacingMode === 'free' || pacingMode === 'free_play' ? '🟢 Free Play' :
                                     pacingMode === 'manual' ? '🔵 Manual' :
                                     pacingMode === 'timed' ? '⏱️ Timed' : `⚙️ ${pacingMode}`}
                                </span>
                                {pacing?.next_unlock_at && (
                                    <span className={styles.cohortTimer}>
                                        Next: {new Date(pacing.next_unlock_at).toLocaleTimeString()}
                                    </span>
                                )}
                            </div>

                            {/* ── Progress Bar ── */}
                            <div className={styles.progressTrack}>
                                <div
                                    className={`${styles.progressFill} ${isComplete ? styles.progressComplete : ''}`}
                                    style={{ width: `${isComplete ? 100 : progress}%` }}
                                />
                                <span className={styles.progressLabel}>{isComplete ? '100' : progress}%</span>
                            </div>

                            {/* ── Timeline Strip ── */}
                            <div className={styles.timeline}>
                                <div className={styles.track} />
                                {ROUNDS.map(r => {
                                    const status = isComplete ? 'completed' : getRoundStatus(r, currentRound, unlockedRound);
                                    return (
                                        <div key={r} className={`${styles.node} ${styles[`node_${status}`]}`}>
                                            <div className={styles.nodeCircle}>
                                                {status === 'completed' ? '✓' : status === 'active' ? '●' : status === 'unlocked' ? '○' : '🔒'}
                                            </div>
                                            <div className={styles.nodeLabel}>R{r}</div>
                                            <div className={styles.nodeDesc}>{roundTitles[r] || ''}</div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* ── Players sub-timeline (if players exist) ── */}
                            {cohort.players?.length > 0 && (
                                <div className={styles.playerSubSection}>
                                    <div className={styles.playerSubHeader}>
                                        <span className={styles.playerSubTitle}>Player Progress</span>
                                    </div>
                                    <div className={styles.playerMiniGrid}>
                                        {cohort.players.map(p => {
                                            const pRound = p.round_number || 1;
                                            const pName = p.cohort_name || formatSessionId(p);
                                            return (
                                                <div key={p.session_id} className={styles.playerMiniRow}>
                                                    <span className={styles.playerMiniName} title={pName}>{pName}</span>
                                                    <div className={styles.miniTimeline}>
                                                        {ROUNDS.map(r => {
                                                            // AC-3 (UX audit #9): a round the server auto-committed
                                                            // is NOT a round the team played. Mark it here so the
                                                            // facilitator sees it on the timeline they already read,
                                                            // rather than only in the export.
                                                            const wasAuto = (p.auto_committed_rounds || []).includes(r);
                                                            return (
                                                                <div
                                                                    key={r}
                                                                    className={`${styles.miniDot} ${
                                                                        r < pRound ? styles.miniComplete :
                                                                        r === pRound ? styles.miniActive :
                                                                        styles.miniLocked
                                                                    }`}
                                                                    style={wasAuto ? { boxShadow: 'inset 0 0 0 2px #fbbf24' } : undefined}
                                                                    title={
                                                                        (roundTitles[r] ? `R${r}: ${roundTitles[r]}` : `R${r}`) +
                                                                        (wasAuto ? ' — AUTO-COMMITTED (not played by the team)' : '')
                                                                    }
                                                                />
                                                            );
                                                        })}
                                                    </div>
                                                    <span className={styles.playerMiniRound}>R{pRound}</span>
                                                    {(p.auto_committed_rounds || []).length > 0 && (
                                                        <span
                                                            title={`Auto-committed round(s): ${p.auto_committed_rounds.join(', ')} — the server submitted a saved draft or defaults because the round closed first. Relevant to grading.`}
                                                            style={{ fontSize: 'var(--type-caption)', fontWeight: 800, color: '#fbbf24', marginLeft: 4, whiteSpace: 'nowrap' }}
                                                        >⏱{p.auto_committed_rounds.length}</span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
