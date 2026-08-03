'use client';

import React, { useMemo, useState, useCallback, useEffect } from 'react';
import styles from './ReportsExport.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const fmt$ = (v) => v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v / 1e3).toFixed(0)}K` : `$${(v || 0).toFixed(0)}`;
const fmtPct = (v) => `${(v ?? 0).toFixed(1)}%`;
const fmtNum = (v, d = 2) => (v ?? 0).toFixed(d);

// ── Tiny inline sparkline (SVG) ──────────────────────────────────
function Sparkline({ data = [], color = '#3b82f6', height = 28 }) {
    if (!data || data.length < 2) return <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>—</span>;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const w = 80;
    const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${height - ((v - min) / range) * (height - 4) - 2}`).join(' ');
    return (
        <svg width={w} height={height} style={{ display: 'block' }}>
            <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
    );
}

// ── CEO Radar mini display ───────────────────────────────────────
function CEOScorePills({ scores = {} }) {
    const DIMS = { strategic_thinking: 'Strategy', financial_acumen: 'Finance', stakeholder_mgmt: 'Stakeholders', sustainability_leadership: 'ESG', crisis_mgmt: 'Crisis', communication: 'Comms' };
    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {Object.entries(DIMS).map(([k, label]) => {
                const v = scores[k];
                if (v == null) return null;
                const pct = (v / 10) * 100;
                const col = pct >= 70 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444';
                return (
                    <span key={k} title={`${label}: ${v}/10`} style={{
                        fontSize: '0.68rem', padding: '1px 5px', borderRadius: '4px',
                        background: `${col}20`, color: col, fontWeight: 600, border: `1px solid ${col}40`,
                    }}>
                        {label} {v.toFixed(1)}
                    </span>
                );
            })}
        </div>
    );
}

// ── Session Deep-Dive Panel ──────────────────────────────────────
function SessionDrillDown({ sessionId, onClose }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const r = await fetch(`${API}/api/admin/session-report/${sessionId}`);
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                if (!cancelled) setData(await r.json());
            } catch (e) { if (!cancelled) setErr(e.message); }
            finally { if (!cancelled) setLoading(false); }
        })();
        return () => { cancelled = true; };
    }, [sessionId]);

    const tvHistory = data?.round_history?.map(r => r.terminal_value) ?? [];
    const repHistory = data?.round_history?.map(r => r.reputation) ?? [];
    const ciHistory = data?.round_history?.map(r => r.avg_ci) ?? [];

    if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>⏳ Loading report…</div>;
    if (err) return <div style={{ padding: '1rem', color: '#ef4444' }}>⚠️ {err}</div>;
    if (!data) return null;

    const k = data.kpis || {};

    return (
        <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-active)', borderRadius: '12px', padding: '1.5rem', marginTop: '0.75rem', position: 'relative' }}>
            <button onClick={onClose} style={{ position: 'absolute', top: '0.75rem', right: '0.75rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.1rem' }}>✕</button>

            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1rem' }}>
                📊 {data.cohort_name} — Full Report <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.78rem' }}>{data.archetype}</span>
            </h3>

            {/* KPI Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                {[
                    { label: 'Terminal Value', val: fmt$(k.terminal_value), spark: tvHistory, col: '#3b82f6' },
                    { label: 'Treasury', val: fmt$(k.treasury), spark: null, col: '#06b6d4' },
                    { label: 'Reputation', val: fmtNum(k.reputation, 1), spark: repHistory, col: k.reputation > 60 ? '#10b981' : k.reputation > 40 ? '#f59e0b' : '#ef4444' },
                    { label: 'Avg SLO', val: fmtNum(k.avg_slo, 1), spark: null, col: '#8b5cf6' },
                    { label: 'Avg Carbon CI', val: fmtNum(k.avg_carbon_intensity, 1), spark: ciHistory, col: '#f59e0b' },
                    { label: 'Total tCO₂e', val: fmtNum(k.total_tco2e, 0), spark: null, col: '#ef4444' },
                    { label: 'Avg NCD', val: fmt$(k.avg_ncd), spark: null, col: '#dc2626' },
                    { label: 'Synergy ×', val: fmtNum(k.synergy_multiplier, 3), spark: null, col: '#10b981' },
                    { label: 'M_R', val: fmtNum(k.regenerative_multiple, 3), spark: null, col: k.regenerative_multiple >= 1.2 ? '#10b981' : k.regenerative_multiple >= 0.8 ? '#f59e0b' : '#ef4444' },
                    { label: 'Bonus Score', val: `+${k.bonus_score || 0}`, spark: null, col: '#f59e0b' },
                ].map(({ label, val, spark, col }) => (
                    <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.6rem 0.75rem' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: '2px' }}>{label}</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: col }}>{val}</div>
                        {spark && spark.length > 1 && <Sparkline data={spark} color={col} height={22} />}
                    </div>
                ))}
            </div>

            {/* CEO Interview */}
            {data.ceo_interview && (
                <div style={{ marginBottom: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px' }}>🎤 CEO Interview — Overall {data.ceo_interview.overall_avg}/10</div>
                    <CEOScorePills scores={data.ceo_interview.final_scores} />
                </div>
            )}

            {/* BU Breakdown */}
            <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px' }}>🏢 Business Unit Breakdown</div>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                        <thead>
                            <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)' }}>
                                {['BU', 'Revenue', 'OPEX', 'Margin', 'CI', 'tCO₂e', 'SLO', 'NCD', 'Gov Risk', 'Burnout'].map(h => (
                                    <th key={h} style={{ textAlign: 'left', padding: '4px 8px', fontWeight: 600 }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {(data.bu_breakdown || []).map(bu => (
                                <tr key={bu.bu_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                    <td style={{ padding: '4px 8px', fontWeight: 600, color: 'var(--text-primary)' }}>{bu.bu_name}</td>
                                    <td style={{ padding: '4px 8px' }}>{fmt$(bu.revenue)}</td>
                                    <td style={{ padding: '4px 8px' }}>{fmt$(bu.opex)}</td>
                                    <td style={{ padding: '4px 8px', color: bu.margin_pct > 20 ? '#10b981' : '#f59e0b' }}>{fmtPct(bu.margin_pct)}</td>
                                    <td style={{ padding: '4px 8px' }}>{fmtNum(bu.carbon_intensity, 1)}</td>
                                    <td style={{ padding: '4px 8px' }}>{fmtNum(bu.tco2e_emissions, 0)}</td>
                                    <td style={{ padding: '4px 8px', color: bu.social_license_score > 60 ? '#10b981' : bu.social_license_score > 40 ? '#f59e0b' : '#ef4444' }}>{fmtNum(bu.social_license_score, 1)}</td>
                                    <td style={{ padding: '4px 8px', color: bu.natural_capital_debt > 1e6 ? '#ef4444' : 'inherit' }}>{fmt$(bu.natural_capital_debt)}</td>
                                    <td style={{ padding: '4px 8px' }}>{fmtNum(bu.governance_risk_score, 1)}</td>
                                    <td style={{ padding: '4px 8px', color: bu.staff_burnout_index > 50 ? '#ef4444' : 'inherit' }}>{fmtNum(bu.staff_burnout_index, 1)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Sandbox + Side Tracks row */}
            <div style={{ display: 'grid', gridTemplateColumns: data.sandbox ? '1fr 1fr' : '1fr', gap: '0.75rem' }}>
                {data.sandbox && (
                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.75rem' }}>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px' }}>🧪 Regulatory Sandbox</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)' }}>{data.sandbox.active_regulations} active instrument{data.sandbox.active_regulations !== 1 ? 's' : ''}</div>
                        {data.sandbox.instruments?.length > 0 && <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '3px' }}>{data.sandbox.instruments.join(', ')}</div>}
                        <div style={{ fontSize: '0.78rem', color: '#ef4444', marginTop: '6px' }}>Compliance burden: {fmt$(data.sandbox.cumulative_compliance_burden)}</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Complexity {fmtNum(data.sandbox.complexity_index, 0)}/100 · Capture risk {fmtNum(data.sandbox.capture_risk, 0)}%</div>
                    </div>
                )}
                {data.side_tracks?.length > 0 && (
                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.75rem' }}>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px' }}>🛤️ Side Tracks</div>
                        {data.side_tracks.map(t => (
                            <div key={t.track_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '3px' }}>
                                <span style={{ color: 'var(--text-primary)' }}>{t.display_name}</span>
                                <span style={{ color: t.completed ? '#10b981' : '#f59e0b', fontWeight: 600 }}>{t.grade} ({t.total_score})</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Main Component ───────────────────────────────────────────────
export default function ReportsExport({ leaderboard = [] }) {
    const [expandedSession, setExpandedSession] = useState(null);
    const [sortKey, setSortKey] = useState('terminal_value');
    const [sortDir, setSortDir] = useState(-1); // -1 = desc

    const toggleSort = (key) => {
        if (sortKey === key) setSortDir(d => -d);
        else { setSortKey(key); setSortDir(-1); }
    };

    const reportData = useMemo(() => leaderboard.map(s => ({
        session_id: s.session_id,
        cohort: s.cohort_name || formatSessionId(s),
        short_code: s.short_code || s.session_id?.slice(0, 8),
        round: s.round_number || 1,
        treasury: s.total_cash || 0,
        terminal_value: s.terminal_value || 0,
        reputation: s.group_reputation || 0,
        avg_slo: s.avg_social_license || 0,
        avg_ncd: s.avg_natural_capital_debt || 0,
        synergy: s.group_synergy || 1,
        bonus: s.bonus_score || 0,
        talent_risk: s.talent_flight_risk || false,
        // AC-3 (UX audit #9): rounds the server auto-committed rather than the
        // team playing them — carried into CSV/JSON so grading can see it.
        auto_committed_rounds: s.auto_committed_rounds || [],
        ending_pathway: s.ending_pathway || '—',
        facilitator: s.facilitator_id || 'N/A',
        difficulty: s.difficulty_tier || '—',
        active_flags: (s.active_flags || []).length,
    })), [leaderboard]);

    const sorted = useMemo(() => [...reportData].sort((a, b) => sortDir * ((b[sortKey] ?? 0) - (a[sortKey] ?? 0))), [reportData, sortKey, sortDir]);

    const stats = useMemo(() => {
        if (!sorted.length) return null;
        const tvs = sorted.map(d => d.terminal_value);
        const reps = sorted.map(d => d.reputation);
        const slos = sorted.map(d => d.avg_slo);
        const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
        return {
            count: sorted.length,
            avgTV: avg(tvs), maxTV: Math.max(...tvs), minTV: Math.min(...tvs),
            avgRep: avg(reps), maxRep: Math.max(...reps), minRep: Math.min(...reps),
            avgSLO: avg(slos),
            talentRisk: sorted.filter(d => d.talent_risk).length,
        };
    }, [sorted]);

    const handleExportCSV = useCallback(() => {
        // AC-3 (UX audit #9): grading needs to distinguish a round the team
        // PLAYED from one the server auto-committed on their behalf (Option B,
        // $1/BU). Without these two columns the two are identical in the export.
        const headers = ['Cohort', 'Session ID', 'Round', 'Terminal Value', 'Treasury', 'Reputation', 'Avg SLO', 'Avg NCD', 'Synergy', 'Bonus', 'Talent Risk', 'Auto-Committed Rounds', 'Auto-Committed Count', 'Ending', 'Difficulty', 'Facilitator'];
        const rows = sorted.map(d => [
            `"${d.cohort}"`, d.session_id, d.round,
            d.terminal_value.toFixed(0), d.treasury.toFixed(0),
            d.reputation.toFixed(1), d.avg_slo.toFixed(1),
            d.avg_ncd.toFixed(0), d.synergy.toFixed(3),
            d.bonus, d.talent_risk ? 'YES' : 'no',
            `"${(d.auto_committed_rounds || []).join(' ')}"`,
            (d.auto_committed_rounds || []).length,
            d.ending_pathway, d.difficulty, d.facilitator,
        ]);
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `mgc_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click(); URL.revokeObjectURL(url);
    }, [sorted]);

    const handleExportJSON = useCallback(() => {
        const blob = new Blob([JSON.stringify(sorted, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `mgc_report_${new Date().toISOString().slice(0, 10)}.json`;
        a.click(); URL.revokeObjectURL(url);
    }, [sorted]);

    const SortTh = ({ label, k }) => (
        <th onClick={() => toggleSort(k)} style={{ cursor: 'pointer', padding: '6px 10px', textAlign: 'left', color: sortKey === k ? '#60a5fa' : 'var(--text-muted)', userSelect: 'none', whiteSpace: 'nowrap', fontSize: '0.72rem', fontWeight: 600 }}>
            {label} {sortKey === k ? (sortDir === -1 ? '↓' : '↑') : ''}
        </th>
    );

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📊</span>
                <div>
                    <h2 className={styles.title}>Reports &amp; Export</h2>
                    <p className={styles.subtitle}>Full session analytics — click any row for a deep-dive. Export to CSV or JSON.</p>
                </div>
            </div>

            {/* Summary Stats */}
            {stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.6rem', marginBottom: '1rem' }}>
                    {[
                        { label: 'Sessions', val: stats.count, col: '#60a5fa' },
                        { label: 'Avg Terminal Value', val: fmt$(stats.avgTV), col: '#3b82f6' },
                        { label: 'Avg Reputation', val: fmtNum(stats.avgRep, 1), col: stats.avgRep > 60 ? '#10b981' : '#f59e0b' },
                        { label: 'Avg SLO', val: fmtNum(stats.avgSLO, 1), col: '#8b5cf6' },
                        { label: 'Best TV', val: fmt$(stats.maxTV), col: '#10b981' },
                        { label: 'Worst TV', val: fmt$(stats.minTV), col: '#ef4444' },
                        { label: 'Best Reputation', val: fmtNum(stats.maxRep, 1), col: '#10b981' },
                        { label: '⚠️ Talent Risk', val: stats.talentRisk, col: stats.talentRisk > 0 ? '#f59e0b' : '#10b981' },
                    ].map(({ label, val, col }) => (
                        <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.6rem 0.75rem' }}>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{label}</div>
                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: col }}>{val}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* Export Buttons */}
            <div className={styles.exportRow}>
                <button className={styles.exportBtn} onClick={handleExportCSV} disabled={!sorted.length}>📄 Export CSV</button>
                <button className={styles.exportBtn} onClick={handleExportJSON} disabled={!sorted.length} style={{ background: 'rgba(99,102,241,0.12)', color: '#818cf8', borderColor: 'rgba(99,102,241,0.3)' }}>📋 Export JSON</button>
                <span className={styles.recordCount}>{sorted.length} session{sorted.length !== 1 ? 's' : ''}</span>
            </div>

            {/* Data Table */}
            {sorted.length > 0 ? (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <SortTh label="Cohort" k="cohort" />
                                <SortTh label="R#" k="round" />
                                <SortTh label="Terminal Value" k="terminal_value" />
                                <SortTh label="Treasury" k="treasury" />
                                <SortTh label="Reputation" k="reputation" />
                                <SortTh label="Avg SLO" k="avg_slo" />
                                <SortTh label="Avg NCD" k="avg_ncd" />
                                <SortTh label="Synergy" k="synergy" />
                                <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontSize: '0.72rem' }}>Flags</th>
                                <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontSize: '0.72rem' }}>Difficulty</th>
                                <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontSize: '0.72rem' }}>Deep-Dive</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map(d => (
                                <React.Fragment key={d.session_id}>
                                    <tr
                                        onClick={() => setExpandedSession(expandedSession === d.session_id ? null : d.session_id)}
                                        style={{ cursor: 'pointer', background: expandedSession === d.session_id ? 'rgba(59,130,246,0.06)' : undefined, transition: 'background 0.15s' }}
                                    >
                                        <td className={styles.cohortName}>{d.cohort}</td>
                                        <td><span className={styles.roundBadge}>R{d.round}</span></td>
                                        <td style={{ fontWeight: 700, color: '#60a5fa' }}>{fmt$(d.terminal_value)}</td>
                                        <td>{fmt$(d.treasury)}</td>
                                        <td style={{ color: d.reputation > 60 ? '#22c55e' : d.reputation > 40 ? '#f59e0b' : '#ef4444', fontWeight: 600 }}>{fmtNum(d.reputation, 1)}</td>
                                        <td style={{ color: d.avg_slo > 60 ? '#22c55e' : d.avg_slo > 40 ? '#f59e0b' : '#ef4444' }}>{fmtNum(d.avg_slo, 1)}</td>
                                        <td style={{ color: d.avg_ncd > 1e6 ? '#ef4444' : 'var(--text-secondary)' }}>{fmt$(d.avg_ncd)}</td>
                                        <td style={{ color: d.synergy > 1.1 ? '#10b981' : 'var(--text-secondary)' }}>{fmtNum(d.synergy, 3)}</td>
                                        <td>
                                            {d.active_flags > 0 && <span style={{ fontSize: '0.65rem', color: '#f59e0b', background: 'rgba(245,158,11,0.12)', padding: '1px 5px', borderRadius: '4px' }}>{d.active_flags} active</span>}
                                            {d.talent_risk && <span style={{ fontSize: '0.65rem', color: '#ef4444', marginLeft: '3px' }}>⚠️ talent</span>}
                                            {/* AC-3: auto-committed rounds are a grading caveat, so they
                                                are visible on screen and not only in the export. */}
                                            {d.auto_committed_rounds?.length > 0 && (
                                                <span
                                                    title={`Auto-committed (not played) in round(s): ${d.auto_committed_rounds.join(', ')}. The server submitted defaults or a saved draft because the round closed first.`}
                                                    style={{ fontSize: '0.65rem', color: '#fbbf24', marginLeft: '4px', fontWeight: 700 }}
                                                >⏱ auto×{d.auto_committed_rounds.length}</span>
                                            )}
                                        </td>
                                        <td><span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', background: 'var(--bg-elevated)', padding: '1px 5px', borderRadius: '4px' }}>{d.difficulty}</span></td>
                                        <td style={{ color: '#60a5fa', fontSize: '0.75rem', fontWeight: 600 }}>{expandedSession === d.session_id ? '▲ Close' : '▼ Expand'}</td>
                                    </tr>
                                    {expandedSession === d.session_id && (
                                        <tr key={`${d.session_id}-drill`}>
                                            <td colSpan={11} style={{ padding: '0 8px 12px' }}>
                                                <SessionDrillDown sessionId={d.session_id} onClose={() => setExpandedSession(null)} />
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className={styles.empty}>No session data available. Sessions will appear here once players have started.</div>
            )}
        </div>
    );
}
