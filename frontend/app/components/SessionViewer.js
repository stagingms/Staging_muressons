'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import styles from './SessionViewer.module.css';
import { Abbr } from './Glossary';
import { formatSessionId, getShortCode } from '../utils/sessionUtils';


const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * SessionViewer — Admin component to view any/all player sessions.
 * Shows a live mini-cockpit for each session with key metrics.
 *
 * Props:
 *  - leaderboard: Array of session summaries from the admin leaderboard
 */
export default function SessionViewer({ leaderboard }) {
    const [viewMode, setViewMode] = useState('closed'); // 'closed' | 'single' | 'all'
    const [selectedId, setSelectedId] = useState(null);
    const [sessions, setSessions] = useState({});
    const intervalRef = useRef(null);

    // Fetch dashboard data for a single session
    const fetchSession = useCallback(async (sid) => {
        try {
            const res = await fetch(`${API}/api/simulations/${sid}/dashboard`);
            if (!res.ok) return null;
            const data = await res.json();
            return data;
        } catch {
            return null;
        }
    }, []);

    // Fetch all or single session data
    const refreshData = useCallback(async () => {
        if (viewMode === 'single' && selectedId) {
            const data = await fetchSession(selectedId);
            if (data) setSessions(prev => ({ ...prev, [selectedId]: data }));
        } else if (viewMode === 'all') {
            const results = {};
            for (const s of leaderboard) {
                const data = await fetchSession(s.session_id);
                if (data) results[s.session_id] = data;
            }
            if (Object.keys(results).length) setSessions(results);
        }
    }, [viewMode, selectedId, leaderboard, fetchSession]);

    // Auto-refresh every 5 seconds when viewer is open
    useEffect(() => {
        if (viewMode === 'closed') {
            clearInterval(intervalRef.current);
            return;
        }
        refreshData();
        intervalRef.current = setInterval(refreshData, 5000);
        return () => clearInterval(intervalRef.current);
    }, [viewMode, selectedId, refreshData]);

    const openSingle = (sid) => {
        setSelectedId(sid);
        setViewMode('single');
    };

    const openAll = () => {
        setViewMode('all');
        setSelectedId(null);
    };

    const close = () => {
        setViewMode('closed');
        setSelectedId(null);
        setSessions({});
    };

    // Get sessions to display
    const displayIds = viewMode === 'all'
        ? leaderboard.map(s => s.session_id)
        : selectedId ? [selectedId] : [];

    return (
        <section className={styles.viewer}>
            {/* Toolbar */}
            <div className={styles.toolbar}>
                <div className={styles.toolbarLeft}>
                    <span className={styles.toolbarIcon}>👁️</span>
                    <h2>Session Viewer</h2>
                </div>
                <div className={styles.toolbarActions}>
                    {viewMode !== 'closed' && (
                        <button className={styles.refreshBtn} onClick={refreshData}>
                            🔄 Refresh
                        </button>
                    )}
                    {viewMode !== 'all' && leaderboard.length > 0 && (
                        <button className={styles.viewAllBtn} onClick={openAll}>
                            📊 View All ({leaderboard.length})
                        </button>
                    )}
                    {viewMode !== 'closed' && (
                        <button className={styles.closeBtn} onClick={close}>
                            ✕ Close
                        </button>
                    )}
                </div>
            </div>

            {/* Session Selector (when closed) */}
            {viewMode === 'closed' && (
                <div className={styles.selectorGrid}>
                    {leaderboard.map(s => (
                        <button
                            key={s.session_id}
                            className={styles.selectorCard}
                            onClick={() => openSingle(s.session_id)}
                        >
                                <span className={styles.selectorName}>
                                {s.cohort_name || formatSessionId(s)}
                            </span>
                            <span className={styles.selectorRound}>
                                R{s.round_number}/10
                            </span>
                        </button>
                    ))}
                    {leaderboard.length === 0 && (
                        <div className={styles.emptyState}>No active sessions</div>
                    )}
                </div>
            )}

            {/* Session Cards */}
            {viewMode !== 'closed' && (
                <div className={`${styles.cardGrid} ${viewMode === 'all' ? styles.gridAll : styles.gridSingle}`}>
                    {displayIds.map(sid => {
                        const data = sessions[sid];
                        const lb = leaderboard.find(s => s.session_id === sid);
                        return (
                            <SessionCard
                                key={sid}
                                sessionId={sid}
                                data={data}
                                leaderboardEntry={lb}
                                isSelected={viewMode === 'single'}
                                onSelect={() => openSingle(sid)}
                                compact={viewMode === 'all' && leaderboard.length > 2}
                            />
                        );
                    })}
                </div>
            )}
        </section>
    );
}

/* ── Individual Session Card ──────────────────────────────────── */
function SessionCard({ sessionId, data, leaderboardEntry, isSelected, onSelect, compact }) {
    const gs = data?.global_state || {};
    const bus = data?.business_units || [];
    const round = data?.current_round || leaderboardEntry?.round_number || '?';
    const cohort = leaderboardEntry?.cohort_name || formatSessionId(leaderboardEntry) || sessionId.slice(0, 12);

    const treasury = gs.corporate_treasury || leaderboardEntry?.total_cash || 0;
    const reputation = gs.group_reputation || leaderboardEntry?.group_reputation || 0;
    const synergy = gs.synergy_multiplier || leaderboardEntry?.group_synergy || 1.0;

    // Aggregate BU metrics
    const avgSL = bus.length
        ? bus.reduce((s, b) => s + (b.social_license_score || 0), 0) / bus.length
        : leaderboardEntry?.avg_social_license || 0;
    const totalNCD = bus.length
        ? bus.reduce((s, b) => s + (b.natural_capital_debt || 0), 0)
        : 0;

    // Active flags
    const flags = gs.active_event_flags
        ? Object.keys(gs.active_event_flags).filter(k =>
            gs.active_event_flags[k] === true || typeof gs.active_event_flags[k] === 'string'
        )
        : leaderboardEntry?.active_flags || [];

    const loading = !data;

    const getHealthColor = (val, low, mid) => {
        if (val <= low) return styles.metricRed;
        if (val <= mid) return styles.metricYellow;
        return styles.metricGreen;
    };

    return (
        <div
            className={`${styles.sessionCard} ${isSelected ? styles.cardExpanded : ''} ${compact ? styles.cardCompact : ''}`}
            onClick={!isSelected ? onSelect : undefined}
        >
            {/* Card Header */}
            <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                    <span className={styles.cardCohort}>{cohort}</span>
                    <span className={styles.cardRound}>Round {round}/10</span>
                </div>
                <div className={`${styles.cardStatus} ${round > 10 ? styles.statusComplete : styles.statusLive}`}>
                    {round > 10 ? '✅ Complete' : '🟢 Live'}
                </div>
            </div>

            {loading && (
                <div className={styles.loadingOverlay}>
                    <span className={styles.spinner}>⟳</span>
                    Loading...
                </div>
            )}

            {/* Key Metrics */}
            <div className={styles.metricsGrid}>
                <div className={styles.metricCard}>
                    <span className={styles.metricIcon}>💰</span>
                    <span className={styles.metricLabel}>Treasury</span>
                    <span className={`${styles.metricValue} ${getHealthColor(treasury / 1_000_000, 20, 40)}`}>
                        ${(treasury / 1_000_000).toFixed(1)}M
                    </span>
                </div>
                <div className={styles.metricCard}>
                    <span className={styles.metricIcon}>⭐</span>
                    <span className={styles.metricLabel}>Reputation</span>
                    <span className={`${styles.metricValue} ${getHealthColor(reputation, 30, 55)}`}>
                        {reputation.toFixed ? reputation.toFixed(0) : reputation}
                    </span>
                </div>
                <div className={styles.metricCard}>
                    <span className={styles.metricIcon}>🤝</span>
                    <span className={styles.metricLabel}>Social License</span>
                    <span className={`${styles.metricValue} ${getHealthColor(avgSL, 30, 55)}`}>
                        {avgSL.toFixed(1)}
                    </span>
                </div>
                <div className={styles.metricCard}>
                    <span className={styles.metricIcon}>🔗</span>
                    <span className={styles.metricLabel}>Synergy</span>
                    <span className={`${styles.metricValue} ${getHealthColor(synergy, 0.9, 1.2)}`}>
                        {(typeof synergy === 'number' ? synergy : 1.0).toFixed(2)}x
                    </span>
                </div>
            </div>

            {/* BU Status (expanded only) */}
            {!compact && bus.length > 0 && (
                <div className={styles.buSection}>
                    <h4 className={styles.buSectionTitle}>Business Units</h4>
                    <div className={styles.buGrid}>
                        {bus.map(bu => (
                            <div key={bu.bu_id} className={styles.buCard}>
                                <span className={styles.buName}>{bu.bu_id}</span>
                                <div className={styles.buMetrics}>
                                    <span title="Revenue — total income">Rev: ${(bu.revenue_base / 1_000_000).toFixed(1)}M</span>
                                    <span title="Social License — stakeholder trust score">SL: {bu.social_license_score?.toFixed(0) || '?'}</span>
                                    <span title="Natural Capital Debt — accumulated environmental damage">NCD: {bu.natural_capital_debt?.toFixed(0) || '0'}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Shadow Board Archetype Badge */}
            {gs.active_event_flags?.shadow_board_archetype && (
                <div style={{
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid',
                    borderColor: gs.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                        ? 'rgba(16, 185, 129, 0.4)'
                        : gs.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                        ? 'rgba(245, 158, 11, 0.4)'
                        : 'rgba(139, 92, 246, 0.4)',
                    background: gs.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                        ? 'rgba(16, 185, 129, 0.08)'
                        : gs.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                        ? 'rgba(245, 158, 11, 0.08)'
                        : 'rgba(139, 92, 246, 0.08)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                }}>
                    <span style={{ fontSize: '1.1rem' }}>
                        {gs.active_event_flags.shadow_board_archetype === 'Sustainability-First' ? '🌱'
                            : gs.active_event_flags.shadow_board_archetype === 'Profit-Maximiser' ? '📈'
                            : '⚡'}
                    </span>
                    <div>
                        <div style={{
                            fontWeight: 700,
                            color: gs.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                                ? '#10b981'
                                : gs.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                                ? '#f59e0b'
                                : '#8b5cf6',
                        }}>
                            {gs.active_event_flags.shadow_board_archetype}
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                            Shadow Board R5 — rejected {gs.active_event_flags.shadow_board_rejection?.replace(/_/g, ' ') || '?'}
                        </div>
                    </div>
                </div>
            )}

            {/* Active Flags */}
            {flags.length > 0 && (
                <div className={styles.flagsRow}>
                    {flags.filter(f => !f.startsWith('shadow_board_')).slice(0, compact ? 3 : 8).map(f => (
                        <span key={f} className={styles.flagTag}>{f.replace(/_/g, ' ')}</span>
                    ))}
                    {flags.filter(f => !f.startsWith('shadow_board_')).length > (compact ? 3 : 8) && (
                        <span className={styles.flagMore}>+{flags.filter(f => !f.startsWith('shadow_board_')).length - (compact ? 3 : 8)}</span>
                    )}
                </div>
            )}

            {/* Session ID footer */}
            <div className={styles.cardFooter}>
                <code className={styles.sessionIdCode}>{leaderboardEntry?.short_code || sessionId.slice(0, 8)}</code>
            </div>
        </div>
    );
}
