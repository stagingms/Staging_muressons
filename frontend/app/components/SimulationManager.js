'use client';

import React, { useState, useMemo, useEffect, Fragment } from 'react';
import styles from './SimulationManager.module.css';
import CreateCohortModal from './CreateCohortModal';
import { formatSessionId } from '../utils/sessionUtils';
import AnalyticsControlPanel from './AnalyticsControlPanel';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function SimulationManager({ leaderboard = [], onSessionCreated, hideCreate = false, fetchInternal = false, currentFacilitatorId = null }) {
    const [createOpen, setCreateOpen] = useState(false);
    const [internalData, setInternalData] = useState([]);
    const [analyticsModalSession, setAnalyticsModalSession] = useState(null);
    const [expandedConfigRow, setExpandedConfigRow] = useState(null);

    const [refreshing, setRefreshing] = useState(false);

    const refreshData = () => {
        if (!fetchInternal) return;
        setRefreshing(true);
        fetch(`${API}/api/admin/leaderboard`)
            .then(r => r.json())
            .then(d => setInternalData(d.leaderboard || d.sessions || []))
            .catch(() => {})
            .finally(() => setRefreshing(false));
    };

    useEffect(() => {
        if (!fetchInternal) return;
        refreshData();
    }, [fetchInternal]);

    const displayData = fetchInternal ? internalData : leaderboard;

    const toggleConfigRow = (sessionId) => {
        setExpandedConfigRow(expandedConfigRow === sessionId ? null : sessionId);
    };

    const grouped = useMemo(() => {
        const groups = {};
        displayData.forEach(s => {
            const fac = s.facilitator_id || 'Unknown';
            if (!groups[fac]) groups[fac] = { facilitator: fac, sessions: [] };
            groups[fac].sessions.push(s);
        });
        return Object.values(groups);
    }, [displayData]);

    const handleCreated = (newSession) => {
        setCreateOpen(false);
        // Re-fetch full leaderboard so the new cohort appears with all correct fields
        // (appending the raw /simulations/start response would show blank rows)
        if (fetchInternal) {
            refreshData();
        }
        onSessionCreated?.(newSession);
    };

    const formatCurrency = (val) => val >= 1e6 ? `$${(val / 1e6).toFixed(1)}M` : `$${val?.toFixed(0) || '0'}`;

    const renderConfigDetails = (s) => {
        const cfg = s;
        const paradigmLabels = {
            legacy_abc: 'Narrative Crises',
            stakeholder_weighted: 'Stakeholder Weighted',
            esg_integrated: 'ESG Integrated',
            healthcare: 'Healthcare',
        };
        const expLabels = {
            classroom_easy: 'Classroom',
            workshop_standard: 'Workshop',
            executive_hard: 'Executive',
            chaos_extreme: 'Chaos Mode',
        };

        // Pedagogy stored as "pedagogical_overrides" on the session dict
        const pedagogy = cfg.pedagogical_overrides || cfg.pedagogical_toggles || cfg.pedagogy || {};
        const enabledPedagogy = Object.entries(pedagogy).filter(([, v]) => v).map(([k]) => k.replace(/_enabled$/, '').replace(/_/g, ' '));
        const sideTracks = cfg.side_tracks || cfg.enabled_side_tracks || [];

        // Currency is stored as currency_symbol (the symbol character like $, ₹)
        const currencyDisplay = cfg.currency_symbol || cfg.display_currency || cfg.currency || '—';

        // Ending pathway is stored in active_event_flags on the global state, or on the session itself
        const endingPathway = cfg.ending_pathway 
            || cfg.active_event_flags?.ending_pathway 
            || '—';

        // Determine if cohort is expired
        const isExpired = cfg.end_date && new Date(cfg.end_date + 'T23:59:59') < new Date();

        return (
            <tr key={`${s.session_id}-config`}>
                <td colSpan={7} style={{ padding: 0, background: 'rgba(59,130,246,0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <div style={{ padding: '14px 20px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {/* Expired banner */}
                        {isExpired && (
                            <div style={{
                                padding: '6px 14px', borderRadius: 8, fontSize: '0.75rem', fontWeight: 700,
                                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                                color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px',
                            }}>
                                🔒 Cohort Expired — Game locked since {cfg.end_date}. Final results are still visible.
                            </div>
                        )}
                        {/* Row 1: Core config */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                            <ConfigChip label="Experience Level" value={expLabels[cfg.experience_level || cfg.scenario_preset] || cfg.experience_level || cfg.scenario_preset || '—'} color="#818cf8" />
                            <ConfigChip label="Paradigm" value={paradigmLabels[cfg.decision_paradigm] || cfg.decision_paradigm || '—'} color="#3b82f6" />
                            <ConfigChip label="Currency" value={currencyDisplay} color="#22c55e" />
                            <ConfigChip label="Ending Pathway" value={endingPathway.replace(/_/g, ' ')} color="#f59e0b" />
                            <ConfigChip label="CEO Interview" value={cfg.ceo_interview_enabled ? `✅ ${cfg.ceo_interview_voice_gender || 'female'}` : '❌ Off'} color="#ec4899" />
                            <ConfigChip label="Start Date" value={cfg.start_date || '—'} color="#06b6d4" />
                            <ConfigChip label="End Date" value={cfg.end_date ? (isExpired ? `⛔ ${cfg.end_date}` : cfg.end_date) : '∞ Open'} color={isExpired ? '#ef4444' : '#06b6d4'} />
                            <ConfigChip label="Session ID" value={s.session_id?.slice(0, 16) || '—'} color="var(--text-muted)" mono />
                        </div>

                        {/* Row 2: Pedagogy */}
                        <div>
                            <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#a78bfa', marginBottom: '4px', display: 'block' }}>
                                🎓 Pedagogical Scaffolding
                            </span>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {enabledPedagogy.length > 0 ? enabledPedagogy.map(p => (
                                    <span key={p} style={{
                                        padding: '3px 10px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 600,
                                        background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.3)',
                                        color: '#a78bfa', textTransform: 'capitalize',
                                    }}>{p}</span>
                                )) : (
                                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>None enabled</span>
                                )}
                            </div>
                        </div>

                        {/* Row 3: Side Tracks */}
                        {sideTracks.length > 0 && (
                            <div>
                                <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#f59e0b', marginBottom: '4px', display: 'block' }}>
                                    🛤️ Side Tracks
                                </span>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                    {sideTracks.map(t => (
                                        <span key={typeof t === 'string' ? t : t.track_id} style={{
                                            padding: '3px 10px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 600,
                                            background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
                                            color: '#f59e0b', textTransform: 'capitalize',
                                        }}>{(typeof t === 'string' ? t : t.track_id).replace(/_/g, ' ')}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </td>
            </tr>
        );
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🗂️</span>
                <div style={{ flex: 1 }}>
                    <h2 className={styles.title}>Simulation Manager</h2>
                    <p className={styles.subtitle}>Manage and compare multiple simulation instances grouped by facilitator.</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {fetchInternal && (
                        <button
                            onClick={refreshData}
                            disabled={refreshing}
                            title="Refresh cohort list"
                            style={{
                                padding: '0 14px', height: '38px', borderRadius: '8px',
                                border: '1px solid var(--border-subtle)',
                                background: 'var(--bg-elevated)', color: 'var(--text-muted)',
                                cursor: refreshing ? 'not-allowed' : 'pointer',
                                fontSize: '0.8rem', fontWeight: 600,
                                display: 'flex', alignItems: 'center', gap: '5px',
                                transition: 'all 0.15s',
                                opacity: refreshing ? 0.6 : 1,
                            }}
                        >
                            <span style={{ display: 'inline-block', animation: refreshing ? 'spin 0.8s linear infinite' : 'none' }}>↻</span>
                            {refreshing ? 'Refreshing…' : 'Refresh'}
                        </button>
                    )}
                    {!hideCreate && (
                        <button className={styles.createBtn} onClick={() => setCreateOpen(true)}>+ Set Up Cohort</button>
                    )}
                </div>
            </div>

            <CreateCohortModal
                isOpen={createOpen}
                onClose={() => setCreateOpen(false)}
                onCreated={handleCreated}
                currentFacilitatorId={currentFacilitatorId}
            />

            {grouped.length === 0 ? (
                <div className={styles.empty}>No active simulations.</div>
            ) : (
                <div className={styles.groupGrid}>
                    {grouped.map(g => (
                        <div key={g.facilitator} className={styles.groupCard}>
                            <div className={styles.groupHeader}>
                                <span className={styles.groupFac}>👤 {g.facilitator}</span>
                                <span className={styles.groupCount}>{g.sessions.length} cohort{g.sessions.length !== 1 ? 's' : ''}</span>
                            </div>
                            <div className={styles.tableWrap} style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', borderRadius: 0 }}>
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            <th style={{ width: 32 }} />
                                            <th>Cohort / Session</th>
                                            <th>Round</th>
                                            <th style={{ textAlign: 'right' }}>Treasury</th>
                                            <th>Schedule</th>
                                            <th style={{ textAlign: 'center' }}>Pacing</th>
                                            <th style={{ textAlign: 'center' }}>Visibility</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {g.sessions.map(s => (
                                                <Fragment key={s.session_id}>
                                                    <tr>
                                                        <td style={{ paddingRight: 0 }}>
                                                            <button
                                                                onClick={() => toggleConfigRow(s.session_id)}
                                                                style={{
                                                                    background: 'none', border: 'none', cursor: 'pointer',
                                                                    color: expandedConfigRow === s.session_id ? '#818cf8' : 'var(--text-muted)',
                                                                    fontSize: '0.72rem', padding: '2px 4px', borderRadius: 4,
                                                                    transition: 'all 0.15s',
                                                                }}
                                                                title="Toggle cohort configuration details"
                                                            >
                                                                {expandedConfigRow === s.session_id ? '▼' : '▶'}
                                                            </button>
                                                        </td>
                                                        <td className={styles.sessionName}>{s.cohort_name || formatSessionId(s)}</td>
                                                        <td><span className={styles.sessionRound}>R{s.round_number || 1}</span></td>
                                                        <td style={{ textAlign: 'right' }}><span className={styles.sessionTreasury}>{formatCurrency(s.total_cash || s.corporate_treasury || 0)}</span></td>
                                                        <td>
                                                            <div className={styles.scheduleCell} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                {s.start_time ? (
                                                                    <span className={styles.scheduleItem} style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                                                        From: {new Date(s.start_time).toLocaleDateString()}
                                                                    </span>
                                                                ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>}
                                                            </div>
                                                        </td>
                                                        <td style={{ textAlign: 'center' }}>
                                                            {(() => {
                                                                const mode = s.pacing_mode || 'free_play';
                                                                const modes = {
                                                                    free_play: { icon: '🔓', label: 'Free Play', bg: 'rgba(59,130,246,0.08)', color: '#3b82f6', border: 'rgba(59,130,246,0.2)' },
                                                                    manual: { icon: '✋', label: `Manual · R${s.max_unlocked_round || '?'}`, bg: 'rgba(245,158,11,0.08)', color: '#f59e0b', border: 'rgba(245,158,11,0.2)' },
                                                                    scheduled: { icon: '📅', label: 'Scheduled', bg: 'rgba(168,85,247,0.08)', color: '#a855f7', border: 'rgba(168,85,247,0.2)' },
                                                                };
                                                                const m = modes[mode] || modes.free_play;
                                                                return (
                                                                    <span style={{
                                                                        display: 'inline-flex', alignItems: 'center', gap: 4,
                                                                        fontSize: '0.68rem', fontWeight: 600, padding: '3px 10px',
                                                                        borderRadius: 12, whiteSpace: 'nowrap',
                                                                        background: m.bg, color: m.color,
                                                                        border: `1px solid ${m.border}`,
                                                                    }}>
                                                                        {m.icon} {m.label}
                                                                    </span>
                                                                );
                                                            })()}
                                                        </td>
                                                        <td style={{ textAlign: 'center', display: 'flex', gap: '6px', justifyContent: 'center' }}>
                                                            <button 
                                                                className={styles.pacingBtn} 
                                                                onClick={() => {
                                                                    localStorage.setItem('fac_selected_session', s.session_id);
                                                                    window.open('/admin/facilitator', '_blank');
                                                                }}
                                                                title="Open Cohort as Facilitator"
                                                                style={{ color: '#10b981', borderColor: 'rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.05)' }}
                                                            >
                                                                🚀 Open
                                                            </button>
                                                            <button 
                                                                className={styles.pacingBtn} 
                                                                onClick={() => setAnalyticsModalSession(s)}
                                                                title="Analytics Visibility Controls"
                                                            >
                                                                👁️ Visibility
                                                            </button>
                                                        </td>
                                                    </tr>
                                                    {expandedConfigRow === s.session_id && renderConfigDetails(s)}
                                                </Fragment>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ))}
                </div>
            )}



            {analyticsModalSession && (
                <div className={styles.modalOverlay} onClick={() => setAnalyticsModalSession(null)}>
                    <div className={styles.modalContent} onClick={e => e.stopPropagation()} style={{ maxWidth: '900px' }}>
                        <button className={styles.closeBtn} onClick={() => setAnalyticsModalSession(null)}>✕</button>
                        <AnalyticsControlPanel sessionId={analyticsModalSession.session_id} />
                    </div>
                </div>
            )}
        </div>
    );
}

function ConfigChip({ label, value, color, mono }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '0.6rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
                {label}
            </span>
            <span style={{
                fontSize: '0.78rem', fontWeight: 700, color,
                fontFamily: mono ? 'var(--font-mono)' : 'inherit',
                textTransform: mono ? 'none' : 'capitalize',
            }}>
                {value}
            </span>
        </div>
    );
}
