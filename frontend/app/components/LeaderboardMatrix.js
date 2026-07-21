'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import styles from './LeaderboardMatrix.module.css';
import { Abbr } from './Glossary';
import { fmtM } from '../utils/formatCurrency';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * LeaderboardMatrix — God Mode cohort leaderboard with individual player scores.
 * Columns: Terminal Value, Total Cash, Synergy, Risk Heatmap, Talent Flight Risk,
 *          Stakeholder Map %, Materiality %, Learning Bonus
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

    // ── Phase R2 (V2-1): sort / search / column triage ──────────────────
    // Display-only: rows are reordered/hidden client-side; the leaderboard
    // array, its fetches, and row identity (session_id) are untouched, so
    // selection and delete/practice controls keep operating on the right
    // session regardless of sort order.
    const [sortKey, setSortKey] = useState(null);   // null = server order
    const [sortDir, setSortDir] = useState('desc');
    const [query, setQuery] = useState('');
    const [showAllCols, setShowAllCols] = useState(false);

    const displayRows = useMemo(() => {
        const q = query.trim().toLowerCase();
        const matches = (r) => !q
            || (r.cohort_name || '').toLowerCase().includes(q)
            || (r.player_id || '').toLowerCase().includes(q)
            || (r.player_name || '').toLowerCase().includes(q);

        // Default path: byte-identical to the pre-R2 rendering.
        if (!sortKey && !q) return leaderboard;

        const byId = new Map(leaderboard.map(r => [r.session_id, r]));
        const parentOf = (r) => r.parent_cohort_id ? byId.get(r.parent_cohort_id) : null;

        // Search only: keep server order; a cohort survives if it or any of
        // its players matches; a player survives if it or its parent matches.
        if (!sortKey) {
            const cohortHasMatch = new Set(
                leaderboard.filter(r => r.parent_cohort_id && matches(r)).map(r => r.parent_cohort_id)
            );
            return leaderboard.filter(r => r.parent_cohort_id
                ? (matches(r) || matches(parentOf(r) || {}))
                : (matches(r) || cohortHasMatch.has(r.session_id)));
        }

        // Sorted: cohorts ordered by key, each followed by its (sorted) players,
        // so grouping survives the sort.
        const val = (r) => sortKey === 'cohort_name'
            ? (r.cohort_name || '')
            : (typeof r[sortKey] === 'number' ? r[sortKey] : (r[sortKey] ?? -Infinity));
        const cmp = (a, b) => {
            const va = val(a), vb = val(b);
            const d = typeof va === 'string' ? va.localeCompare(String(vb)) : (va - vb);
            return sortDir === 'asc' ? d : -d;
        };
        const cohorts = [...leaderboard.filter(r => !r.parent_cohort_id)].sort(cmp);
        const out = [];
        const seen = new Set();
        for (const c of cohorts) {
            const kids = [...leaderboard.filter(r => r.parent_cohort_id === c.session_id)].sort(cmp);
            const anyMatch = matches(c) || kids.some(matches);
            if (!q || anyMatch) {
                out.push(c); seen.add(c.session_id);
                for (const k of kids) {
                    if (!q || matches(k) || matches(c)) { out.push(k); seen.add(k.session_id); }
                }
            }
        }
        for (const r of leaderboard) { // orphans (parent not in list)
            if (!seen.has(r.session_id) && (!q || matches(r))) out.push(r);
        }
        return out;
    }, [leaderboard, sortKey, sortDir, query]);

    const toggleSort = (key) => {
        if (sortKey === key) {
            if (sortDir === 'desc') setSortDir('asc');
            else { setSortKey(null); setSortDir('desc'); } // third click: server order
        } else { setSortKey(key); setSortDir('desc'); }
    };

    const SortTh = ({ label, k, title, className }) => (
        <th
            className={className}
            title={title ? `${title} — click to sort` : 'Click to sort'}
            aria-sort={sortKey === k ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            onClick={() => toggleSort(k)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort(k); } }}
            tabIndex={0}
            style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap' }}
        >
            {label}{sortKey === k ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
        </th>
    );

    // Fetch practice mode status for all top-level cohorts
    const fetchPracticeStates = useCallback(async () => {
        const cohorts = leaderboard.filter(s => !s.player_id && !s.parent_cohort_id);
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

    // Count cohorts and players separately
    const cohortCount = leaderboard.filter(s => !s.parent_cohort_id).length;
    const playerCount = leaderboard.filter(s => !!s.parent_cohort_id).length;
    const totalCount = leaderboard.length;

    // Score badge helper
    const scoreBadge = (value, maxVal, unit = '%') => {
        if (!value && value !== 0) return <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>;
        const pct = maxVal ? (value / maxVal) * 100 : value;
        let bg, color;
        if (pct >= 80) { bg = 'rgba(16, 185, 129, 0.12)'; color = '#10b981'; }
        else if (pct >= 60) { bg = 'rgba(245, 158, 11, 0.12)'; color = '#f59e0b'; }
        else if (pct > 0) { bg = 'rgba(239, 68, 68, 0.12)'; color = '#ef4444'; }
        else { return <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>; }
        return (
            <span style={{
                fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.5rem',
                borderRadius: '4px', background: bg, color, fontFamily: 'var(--font-mono)',
                border: `1px solid ${color}22`,
            }}>
                {typeof value === 'number' ? value.toFixed(0) : value}{unit}
            </span>
        );
    };


    return (
        <section className={styles.matrix}>
            <div className={styles.header}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={styles.icon}>🏆</span>
                    <h2>Player Leaderboard</h2>
                    <span className={styles.count}>
                        {cohortCount} cohort{cohortCount !== 1 ? 's' : ''}
                        {playerCount > 0 && ` · ${playerCount} player${playerCount !== 1 ? 's' : ''}`}
                    </span>
                </div>
                {/* Phase R2 (V2-1): triage controls — search, sort reset, column split */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <input
                        type="search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="🔎 Filter by cohort or player…"
                        aria-label="Filter leaderboard by cohort or player name"
                        style={{
                            padding: '0.35rem 0.7rem', borderRadius: 'var(--radius-chip, 6px)',
                            border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                            color: 'var(--text-primary)', fontSize: '0.78rem', minWidth: '210px',
                        }}
                    />
                    {sortKey && (
                        <button
                            onClick={() => { setSortKey(null); setSortDir('desc'); }}
                            title="Back to server ranking order"
                            style={{
                                padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-chip, 6px)',
                                border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                color: 'var(--text-muted)', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600,
                            }}
                        >✕ Clear sort</button>
                    )}
                    <button
                        onClick={() => setShowAllCols(v => !v)}
                        aria-pressed={showAllCols}
                        title={showAllCols ? 'Show the 11 triage columns only' : 'Show all 18 columns (assessment metrics)'}
                        style={{
                            padding: '0.3rem 0.7rem', borderRadius: 'var(--radius-chip, 6px)',
                            border: '1px solid var(--border-subtle)',
                            background: showAllCols ? 'var(--accent-soft, rgba(99,102,241,0.12))' : 'var(--bg-body)',
                            color: showAllCols ? 'var(--accent, #6366f1)' : 'var(--text-muted)',
                            fontSize: '0.72rem', cursor: 'pointer', fontWeight: 700,
                        }}
                    >{showAllCols ? '▾ Fewer metrics' : '▸ More metrics'}</button>
                </div>
            </div>

            <div className={styles.tableWrap}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th className={styles.rank}>#</th>
                            <SortTh label="Cohort" k="cohort_name" />
                            <th>Player</th>
                            <SortTh label="Round" k="round_number" />
                            <SortTh label="Terminal Value" k="terminal_value" />
                            <SortTh label="Total Cash" k="total_cash" />
                            <SortTh label="Synergy" k="group_synergy" />
                            <SortTh label="Reputation" k="group_reputation" title="Reputation — public perception score" />
                            {showAllCols && <SortTh label="Bonus" k="bonus_score" title="Bonus points from quizzes & learning" />}
                            {showAllCols && <th className={styles.heatCol} title="Stakeholder Map accuracy %">Stakeholder</th>}
                            {showAllCols && <th className={styles.heatCol} title="CSRD Materiality accuracy %">Materiality</th>}
                            {showAllCols && <th className={styles.heatCol} title="Learning activities completed (podcasts + quizzes)">Learning</th>}
                            {showAllCols && <th className={styles.heatCol}><Abbr term="NCD">NCD Risk</Abbr></th>}
                            {showAllCols && <th className={styles.heatCol}><Abbr term="SL">Social License</Abbr></th>}
                            <th>Talent Risk</th>
                            {showAllCols && <th title="Shadow Board Audit archetype — R5 value judgment">Shadow Board</th>}
                            <th>Practice</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {displayRows.map((sess, i) => {
                            const isCohort = !sess.parent_cohort_id;
                            const isPlayer = !!sess.parent_cohort_id;
                            const isPractice = practiceStates[sess.session_id];
                            const isLoading = loadingPractice[sess.session_id];

                            // Compute rank only among the same level
                            const rank = i + 1;

                            return (
                                <tr
                                    key={sess.session_id}
                                    className={`${styles.row} ${sess.session_id === selectedSession ? styles.selectedRow : ''} ${isPlayer ? styles.playerRow : ''}`}
                                    onClick={() => onSelectSession?.(sess.session_id)}
                                    title={sess.session_id === selectedSession
                                        ? 'Selected — session-scoped tools (Override, Undo, Messages…) act on this session'
                                        : 'Click to select — session-scoped tools will act on this session'}
                                    style={{ animationDelay: `${i * 50}ms`, cursor: 'pointer' }}
                                >
                                    <td className={styles.rank}>
                                        {isCohort ? (
                                            <span className={i === 0 ? styles.gold : i === 1 ? styles.silver : i === 2 ? styles.bronze : ''}>
                                                {rank}
                                            </span>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>└</span>
                                        )}
                                    </td>
                                    <td className={styles.cohortName}>
                                        {sess.session_id === selectedSession && (
                                            <span title="Selected — session-scoped tools act on this session" style={{ marginRight: '4px', color: '#22c55e', fontWeight: 800 }}>✓</span>
                                        )}
                                        {isCohort && isPractice && <span title="Practice Mode Active" style={{ marginRight: '4px' }}>🎓</span>}
                                        {isPlayer ? (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', paddingLeft: '8px' }}>
                                                {sess.cohort_name}
                                            </span>
                                        ) : (
                                            sess.cohort_name
                                        )}
                                    </td>
                                    <td className={styles.mono}>
                                        {sess.player_id ? (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                                                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{sess.player_id}</span>
                                                {sess.player_name && (
                                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'inherit' }}>
                                                        {sess.player_name}
                                                    </span>
                                                )}
                                            </div>
                                        ) : '–'}
                                    </td>
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
                                    {showAllCols && (
                                    <td className={styles.mono} style={{ color: sess.bonus_score > 0 ? '#059669' : '#94a3b8' }}>
                                        {sess.bonus_score > 0 ? `🏅 ${(sess.bonus_score || 0).toLocaleString()}` : '–'}
                                    </td>
                                    )}
                                    {/* Individual Player Scores */}
                                    {showAllCols && (
                                    <td style={{ textAlign: 'center' }}>
                                        {sess.stakeholder_map_completed
                                            ? scoreBadge(sess.stakeholder_map_accuracy, 100)
                                            : <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        }
                                    </td>
                                    )}
                                    {showAllCols && (
                                    <td style={{ textAlign: 'center' }}>
                                        {sess.csrd_completed
                                            ? scoreBadge(sess.materiality_accuracy, 100)
                                            : <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        }
                                    </td>
                                    )}
                                    {showAllCols && (
                                    <td style={{ textAlign: 'center' }}>
                                        {sess.learning_bonus_count > 0 ? (
                                            <span style={{
                                                fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.5rem',
                                                borderRadius: '4px',
                                                background: 'rgba(99, 102, 241, 0.12)',
                                                color: '#6366f1',
                                                fontFamily: 'var(--font-mono)',
                                                border: '1px solid rgba(99, 102, 241, 0.2)',
                                            }}>
                                                📚 {sess.learning_bonus_count}
                                                <span style={{ fontSize: '0.6rem', opacity: 0.7, marginLeft: '3px' }}>
                                                    (+{sess.learning_bonus_total.toLocaleString()})
                                                </span>
                                            </span>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        )}
                                    </td>
                                    )}
                                    {showAllCols && (
                                    <td>
                                        <div className={`${styles.heatCell} ${riskColor(sess.avg_natural_capital_debt)}`}>
                                            {sess.avg_natural_capital_debt.toFixed(1)}
                                        </div>
                                    </td>
                                    )}
                                    {showAllCols && (
                                    <td>
                                        <div className={`${styles.heatCell} ${riskColor(sess.avg_social_license, true)}`}>
                                            {sess.avg_social_license.toFixed(1)}
                                        </div>
                                    </td>
                                    )}
                                    <td>
                                        {sess.talent_flight_risk ? (
                                            <span className={styles.flightRisk}>
                                                ⚠️ {sess.talent_penalty_multiplier.toFixed(2)}×
                                            </span>
                                        ) : (
                                            <span className={styles.safe}>✓ Safe</span>
                                        )}
                                    </td>
                                    {showAllCols && (
                                    <td>
                                        {sess.shadow_board_archetype ? (
                                            <span
                                                title={`Rejected: ${(sess.shadow_board_rejection || '').replace(/_/g, ' ')}`}
                                                style={{
                                                    fontSize: '0.72rem',
                                                    fontWeight: 700,
                                                    padding: '0.15rem 0.4rem',
                                                    borderRadius: '4px',
                                                    background: sess.shadow_board_archetype === 'Sustainability-First'
                                                        ? 'rgba(16, 185, 129, 0.12)'
                                                        : sess.shadow_board_archetype === 'Profit-Maximiser'
                                                        ? 'rgba(245, 158, 11, 0.12)'
                                                        : 'rgba(139, 92, 246, 0.12)',
                                                    color: sess.shadow_board_archetype === 'Sustainability-First'
                                                        ? '#10b981'
                                                        : sess.shadow_board_archetype === 'Profit-Maximiser'
                                                        ? '#f59e0b'
                                                        : '#8b5cf6',
                                                    border: `1px solid ${sess.shadow_board_archetype === 'Sustainability-First'
                                                        ? 'rgba(16, 185, 129, 0.3)'
                                                        : sess.shadow_board_archetype === 'Profit-Maximiser'
                                                        ? 'rgba(245, 158, 11, 0.3)'
                                                        : 'rgba(139, 92, 246, 0.3)'}`,
                                                    whiteSpace: 'nowrap',
                                                }}
                                            >
                                                {sess.shadow_board_archetype === 'Sustainability-First' ? '🌱'
                                                    : sess.shadow_board_archetype === 'Profit-Maximiser' ? '📈' : '⚡'}
                                                {' '}{sess.shadow_board_archetype}
                                            </span>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>–</span>
                                        )}
                                    </td>
                                    )}
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
                                <td colSpan={showAllCols ? 18 : 11} className={styles.empty}>
                                    No active sessions. Start a simulation to see the leaderboard.
                                </td>
                            </tr>
                        )}
                        {leaderboard.length > 0 && displayRows.length === 0 && (
                            <tr>
                                <td colSpan={showAllCols ? 18 : 11} className={styles.empty}>
                                    No cohorts or players match “{query}”.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
