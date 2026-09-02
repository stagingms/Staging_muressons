'use client';
import { useState, useEffect } from 'react';
import { playerIdHeader } from '../hooks/useSimulation';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const SEV_COLORS = { critical: '#ef4444', warning: '#f59e0b', info: '#3b82f6', success: '#22c55e' };
const SEV_BG = { critical: 'rgba(239,68,68,0.08)', warning: 'rgba(245,158,11,0.08)', info: 'rgba(59,130,246,0.08)', success: 'rgba(34,197,94,0.08)' };

/* severity priority for sorting within a round */
const SEV_PRIORITY = { critical: 0, warning: 1, info: 2, success: 3 };

/* cohort color palette — distinct tints for up to 12 cohorts */
const COHORT_PALETTE = [
    '#38bdf8', '#a78bfa', '#34d399', '#fb923c', '#f472b6',
    '#facc15', '#2dd4bf', '#c084fc', '#4ade80', '#f87171',
    '#60a5fa', '#e879f9',
];

function EventCard({ evt, showCohort, cohortColor }) {
    return (
        <div style={{
            padding: '0.75rem 1rem', borderRadius: '8px',
            background: SEV_BG[evt.severity] || SEV_BG.info,
            border: `1px solid ${SEV_COLORS[evt.severity] || SEV_COLORS.info}22`,
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            transition: 'transform 0.12s, box-shadow 0.12s',
        }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateX(3px)'; e.currentTarget.style.boxShadow = `0 2px 12px ${SEV_COLORS[evt.severity] || '#3b82f6'}18`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateX(0)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
            <span style={{ fontSize: '1.3rem' }}>{evt.icon}</span>
            <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {evt.label}
                </div>
                {typeof evt.value === 'string' && evt.value.length > 5 && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{evt.value}</div>
                )}
            </div>
            {showCohort && evt._cohort_name && (
                <span style={{
                    padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: 'var(--type-caption)', fontWeight: 700,
                    background: `${cohortColor || '#64748b'}20`, color: cohortColor || '#64748b',
                    border: `1px solid ${cohortColor || '#64748b'}40`,
                    maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>{evt._cohort_name}</span>
            )}
            <span style={{
                padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: 'var(--type-caption)', fontWeight: 700,
                background: SEV_COLORS[evt.severity] || '#64748b', color: '#fff',
            }}>R{evt.round}</span>
        </div>
    );
}

function RoundGroup({ round, events, defaultOpen, showCohort, cohortColorMap }) {
    const [open, setOpen] = useState(defaultOpen);
    const critCount = events.filter(e => e.severity === 'critical').length;
    const warnCount = events.filter(e => e.severity === 'warning').length;

    return (
        <div style={{
            borderRadius: '10px',
            border: `1px solid ${critCount > 0 ? 'rgba(239,68,68,0.25)' : 'var(--border-subtle)'}`,
            background: 'var(--bg-card)',
            overflow: 'hidden',
            transition: 'border-color 0.2s',
        }}>
            <button onClick={() => setOpen(o => !o)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.7rem 1rem', border: 'none', cursor: 'pointer',
                background: open ? 'rgba(59,130,246,0.06)' : 'transparent',
                transition: 'background 0.15s',
            }}>
                <span style={{
                    fontSize: 'var(--type-caption)', transition: 'transform 0.2s',
                    transform: open ? 'rotate(90deg)' : 'rotate(0deg)',
                    color: 'var(--text-muted)',
                }}>▶</span>
                <span style={{
                    padding: '0.2rem 0.65rem', borderRadius: '5px', fontSize: '0.75rem', fontWeight: 800,
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff',
                    letterSpacing: '0.04em',
                }}>R{round}</span>
                <span style={{ flex: 1, textAlign: 'left', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Round {round}
                </span>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                    {critCount > 0 && (
                        <span style={{
                            padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: 'var(--type-caption)', fontWeight: 700,
                            background: 'rgba(239,68,68,0.12)', color: '#ef4444',
                        }}>{critCount} critical</span>
                    )}
                    {warnCount > 0 && (
                        <span style={{
                            padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: 'var(--type-caption)', fontWeight: 700,
                            background: 'rgba(245,158,11,0.12)', color: '#f59e0b',
                        }}>{warnCount} warning</span>
                    )}
                    <span style={{
                        padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: 'var(--type-caption)', fontWeight: 600,
                        background: 'rgba(99,102,241,0.1)', color: '#818cf8',
                    }}>{events.length} event{events.length !== 1 ? 's' : ''}</span>
                </div>
            </button>
            {open && (
                <div style={{ padding: '0.5rem 0.75rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {events
                        .slice()
                        .sort((a, b) => (SEV_PRIORITY[a.severity] ?? 9) - (SEV_PRIORITY[b.severity] ?? 9))
                        .map((evt, i) => <EventCard key={i} evt={evt} showCohort={showCohort} cohortColor={cohortColorMap?.[evt._cohort_id]} />)}
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════
 *  CohortGroup — collapsible per-cohort section
 * ═══════════════════════════════════════════════════ */
function CohortGroup({ cohort, color, filterSev, sortDir, defaultOpen }) {
    const [open, setOpen] = useState(defaultOpen);

    const filteredRounds = cohort.feed
        .map(r => {
            const evts = filterSev === 'all' ? r.events : r.events.filter(e => e.severity === filterSev);
            return { round: r.round, events: evts };
        })
        .filter(r => r.events.length > 0)
        .sort((a, b) => sortDir === 'desc' ? b.round - a.round : a.round - b.round);

    const totalFiltered = filteredRounds.reduce((s, r) => s + r.events.length, 0);
    const critTotal = filteredRounds.reduce((s, r) => s + r.events.filter(e => e.severity === 'critical').length, 0);

    if (totalFiltered === 0) return null;

    return (
        <div style={{
            borderRadius: '12px',
            border: `1px solid ${color}30`,
            background: 'var(--bg-card)',
            overflow: 'hidden',
        }}>
            {/* cohort header */}
            <button onClick={() => setOpen(o => !o)} style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.8rem 1rem', border: 'none', cursor: 'pointer',
                background: open ? `${color}0a` : 'transparent',
                transition: 'background 0.15s',
                borderBottom: open ? `1px solid ${color}20` : 'none',
            }}>
                <span style={{
                    fontSize: 'var(--type-caption)', transition: 'transform 0.2s',
                    transform: open ? 'rotate(90deg)' : 'rotate(0deg)',
                    color: 'var(--text-muted)',
                }}>▶</span>
                <span style={{
                    width: '10px', height: '10px', borderRadius: '3px',
                    background: color, flexShrink: 0,
                }} />
                <span style={{
                    flex: 1, textAlign: 'left', fontSize: '0.88rem', fontWeight: 700,
                    color: 'var(--text-primary)',
                }}>
                    {cohort.cohort_name}
                </span>
                <span style={{
                    fontSize: 'var(--type-caption)', color: 'var(--text-muted)', fontWeight: 600,
                }}>R{cohort.round}</span>
                <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                    {critTotal > 0 && (
                        <span style={{
                            padding: '0.15rem 0.45rem', borderRadius: '10px', fontSize: 'var(--type-caption)', fontWeight: 700,
                            background: 'rgba(239,68,68,0.12)', color: '#ef4444',
                        }}>🔴 {critTotal}</span>
                    )}
                    <span style={{
                        padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: 'var(--type-caption)', fontWeight: 600,
                        background: `${color}18`, color,
                    }}>{totalFiltered} event{totalFiltered !== 1 ? 's' : ''}</span>
                </div>
            </button>

            {/* cohort body: round groups inside */}
            {open && (
                <div style={{ padding: '0.5rem 0.6rem 0.6rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {filteredRounds.map((r, i) => (
                        <RoundGroup
                            key={r.round}
                            round={r.round}
                            events={r.events}
                            defaultOpen={i < 2}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════
 *  MAIN EXPORTED COMPONENT
 * ═══════════════════════════════════════════════════ */
export default function ComplexityEventFeed({ sessionId }) {
    const [feed, setFeed] = useState([]);           // single-cohort feed
    const [allCohorts, setAllCohorts] = useState([]); // multi-cohort data
    const [loading, setLoading] = useState(false);
    const [filterSev, setFilterSev] = useState('all');
    const [viewMode, setViewMode] = useState('grouped'); // 'grouped' | 'flat' | 'cohort'
    const [sortDir, setSortDir] = useState('desc');
    const [cohortFilter, setCohortFilter] = useState('all'); // 'all' or a session_id

    /* ── fetch single session ── */
    useEffect(() => {
        if (!sessionId) return;
        setLoading(true);
        fetch(`${API}/api/admin/complexity-events/${sessionId}`, { credentials: 'include', headers: { ...playerIdHeader() } })
            .then(r => r.json())
            .then(d => { setFeed(d.feed || []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [sessionId]);

    /* ── fetch all cohorts (for cohort view) ── */
    useEffect(() => {
        if (viewMode !== 'cohort') return;
        setLoading(true);
        fetch(`${API}/api/admin/complexity-events-all`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => { setAllCohorts(d.cohorts || []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [viewMode]);

    /* ── cohort color map ── */
    const cohortColorMap = {};
    allCohorts.forEach((c, i) => { cohortColorMap[c.session_id] = COHORT_PALETTE[i % COHORT_PALETTE.length]; });

    /* ── no session + not in cohort mode ── */
    if (!sessionId && viewMode !== 'cohort') {
        // Auto-switch to cohort view when no session selected
        return (
            <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        📡 Complexity Event Feed
                    </h2>
                </div>
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📡</div>
                    <p>Select a cohort to view per-session events, or</p>
                    <button onClick={() => setViewMode('cohort')} style={{
                        marginTop: '0.75rem', padding: '0.6rem 1.5rem', borderRadius: '8px',
                        border: '1px solid rgba(56,189,248,0.3)',
                        background: 'rgba(56,189,248,0.1)', color: '#38bdf8',
                        fontSize: '0.85rem', fontWeight: 700, cursor: 'pointer',
                        transition: 'all 0.15s',
                    }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(56,189,248,0.2)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'rgba(56,189,248,0.1)'}
                    >
                        🏫 View All Cohorts
                    </button>
                </div>
            </div>
        );
    }

    /* ── derive data for single-session views ── */
    const allEvents = feed.flatMap(r => r.events);
    const filteredFlat = filterSev === 'all' ? allEvents : allEvents.filter(e => e.severity === filterSev);

    const sortedRounds = feed
        .map(r => {
            const evts = filterSev === 'all' ? r.events : r.events.filter(e => e.severity === filterSev);
            return { round: r.round, events: evts };
        })
        .filter(r => r.events.length > 0)
        .sort((a, b) => sortDir === 'desc' ? b.round - a.round : a.round - b.round);

    const flatSorted = filteredFlat.slice().sort((a, b) =>
        sortDir === 'desc' ? b.round - a.round || (SEV_PRIORITY[a.severity] ?? 9) - (SEV_PRIORITY[b.severity] ?? 9)
                           : a.round - b.round || (SEV_PRIORITY[a.severity] ?? 9) - (SEV_PRIORITY[b.severity] ?? 9)
    );

    /* ── derive data for cohort view ── */
    const visibleCohorts = cohortFilter === 'all'
        ? allCohorts
        : allCohorts.filter(c => c.session_id === cohortFilter);

    const cohortSortedList = visibleCohorts.slice().sort((a, b) => {
        if (sortDir === 'desc') return b.total_events - a.total_events;
        return a.total_events - b.total_events;
    });

    /* ── pill button style helper ── */
    const pillBtn = (active, color) => ({
        padding: '0.3rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600,
        border: active ? '2px solid' : '1px solid var(--border-subtle)',
        borderColor: active ? (color || '#3b82f6') : undefined,
        background: active ? `${color || '#3b82f6'}14` : 'var(--bg-body)',
        color: active ? (color || '#3b82f6') : 'var(--text-muted)',
        cursor: 'pointer', transition: 'all 0.15s',
    });

    const viewBtnStyle = (isActive) => ({
        padding: '0.35rem 0.75rem', borderRadius: '5px', fontSize: 'var(--type-caption)', fontWeight: 700,
        border: 'none', cursor: 'pointer', transition: 'all 0.15s',
        background: isActive ? 'rgba(99,102,241,0.2)' : 'transparent',
        color: isActive ? '#a5b4fc' : 'var(--text-muted)',
    });

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* ── Header row ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    📡 Complexity Event Feed
                </h2>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {['all', 'critical', 'warning', 'info', 'success'].map(s => (
                        <button key={s} onClick={() => setFilterSev(s)} style={pillBtn(filterSev === s, SEV_COLORS[s])}>
                            {s === 'all' ? '🌐 All' : s.charAt(0).toUpperCase() + s.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* ── Controls row: view mode + sort direction + cohort filter ── */}
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.5rem 0.75rem', borderRadius: '8px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                flexWrap: 'wrap', gap: '0.5rem',
            }}>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button onClick={() => setViewMode('grouped')} style={viewBtnStyle(viewMode === 'grouped')}>
                        📋 By Round
                    </button>
                    <button onClick={() => setViewMode('flat')} style={viewBtnStyle(viewMode === 'flat')}>
                        📜 Flat List
                    </button>
                    <button onClick={() => { setViewMode('cohort'); setCohortFilter('all'); }} style={viewBtnStyle(viewMode === 'cohort')}>
                        🏫 By Cohort
                    </button>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {/* Cohort filter dropdown — only in cohort mode */}
                    {viewMode === 'cohort' && allCohorts.length > 1 && (
                        <select
                            value={cohortFilter}
                            onChange={e => setCohortFilter(e.target.value)}
                            style={{
                                padding: '0.3rem 0.6rem', borderRadius: '5px', fontSize: 'var(--type-caption)', fontWeight: 600,
                                border: '1px solid var(--border-subtle)',
                                background: 'var(--bg-body)', color: 'var(--text-primary)',
                                cursor: 'pointer',
                            }}
                        >
                            <option value="all">All Cohorts ({allCohorts.length})</option>
                            {allCohorts.map(c => (
                                <option key={c.session_id} value={c.session_id}>
                                    {c.cohort_name} — R{c.round} ({c.total_events} events)
                                </option>
                            ))}
                        </select>
                    )}
                    <button onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')} style={{
                        padding: '0.35rem 0.75rem', borderRadius: '5px', fontSize: 'var(--type-caption)', fontWeight: 700,
                        border: '1px solid var(--border-subtle)', cursor: 'pointer', transition: 'all 0.15s',
                        background: 'transparent', color: 'var(--text-muted)',
                        display: 'flex', alignItems: 'center', gap: '0.35rem',
                    }}>
                        {sortDir === 'desc' ? '⬇️ Newest First' : '⬆️ Oldest First'}
                    </button>
                </div>
            </div>

            {/* ── Feed content ── */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading events...</div>
            ) : viewMode === 'cohort' ? (
                /* ═══ COHORT VIEW ═══ */
                cohortSortedList.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No cohort events found</div>
                ) : (
                    <div style={{ maxHeight: '650px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {cohortSortedList.map((c, idx) => (
                            <CohortGroup
                                key={c.session_id}
                                cohort={c}
                                color={cohortColorMap[c.session_id] || '#64748b'}
                                filterSev={filterSev}
                                sortDir={sortDir}
                                defaultOpen={idx < 2}
                            />
                        ))}
                    </div>
                )
            ) : filteredFlat.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No events found</div>
            ) : viewMode === 'grouped' ? (
                <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {sortedRounds.map(r => (
                        <RoundGroup
                            key={r.round}
                            round={r.round}
                            events={r.events}
                            defaultOpen={sortedRounds.indexOf(r) < 3}
                        />
                    ))}
                </div>
            ) : (
                <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {flatSorted.map((evt, i) => <EventCard key={i} evt={evt} />)}
                </div>
            )}

            {/* ── Summary footer ── */}
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                {viewMode === 'cohort'
                    ? `${visibleCohorts.reduce((s, c) => s + c.total_events, 0)} total events across ${visibleCohorts.length} cohort${visibleCohorts.length !== 1 ? 's' : ''}`
                    : `${allEvents.length} total events across ${feed.length} rounds`
                }
                {filterSev !== 'all' && ` · filtered: ${filterSev}`}
            </div>
        </div>
    );
}
