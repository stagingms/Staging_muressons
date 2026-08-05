'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './PlatformAnalytics.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Railway audit §4.3: tabs come from the shared analytics registry — one
// place to add a card, one tooltip wording for both surfaces.
import { ANALYTICS_TABS as TABS } from '../config/analyticsRegistry';

const CHOICE_COLORS = {
    option_a: '#3b82f6', option_b: '#f59e0b', option_c: '#10b981',
    option_d: '#8b5cf6', option_e: '#ef4444',
};

export default function PlatformAnalytics({ visibility = null, leaderboard = [], onNavigate, onSelectSession }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('heatmap');

    const load = async () => {
        setLoading(true);
        try {
            // credentials: the endpoint is auth-scoped (facilitators see their own
            // cohorts; admins the platform) — the JWT cookie must reach it even
            // when the API origin differs in dev.
            const res = await fetch(`${API}/api/admin/god/analytics`, { credentials: 'include' });
            if (res.ok) setData(await res.json());
        } catch {}
        setLoading(false);
    };
    useEffect(() => { load(); }, []);

    // Filter tabs based on visibility (facilitator mode)
    const visibleTabs = useMemo(() => {
        if (!visibility) return TABS; // God Mode sees all
        return TABS.filter(t => visibility[t.key] !== false);
    }, [visibility]);

    if (loading) return <div className={styles.loading}>Loading analytics…</div>;
    if (!data) return <div className={styles.error}>Failed to load analytics</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📊</span>
                <div>
                    <h2>Cohort Analytics</h2>
                    <p className={styles.subtitle}>
                        {data.total_cohorts} cohorts · {data.total_players} players · {data.total_decisions} decisions
                    </p>
                </div>
                <button className={styles.refreshBtn} onClick={() => load()}>🔄 Refresh</button>
            </div>

            <div className={styles.tabBar}>
                {visibleTabs.map(t => (
                    <button
                        key={t.id}
                        className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`}
                        onClick={() => setTab(t.id)}
                        data-tooltip={t.title}
                        data-tooltip-pos="below"
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            <div className={styles.panel}>
                {tab === 'heatmap' && <DecisionHeatmap data={data.decision_heatmap} />}
                {tab === 'timing' && <TimeToDecision data={data.time_to_decision} />}
                {tab === 'cohorts' && <CohortComparison data={data.cohort_trajectories} leaderboard={leaderboard} onNavigate={onNavigate} onSelectSession={onSelectSession} />}
                {tab === 'convergence' && <ConvergenceAnalysis data={data.convergence} />}
                {tab === 'learning' && <LearningOutcomes data={data.learning_outcomes} />}
                {tab === 'risk' && <RiskExposure data={data.risk_exposure} leaderboard={leaderboard} onNavigate={onNavigate} onSelectSession={onSelectSession} />}
                {tab === 'calibration' && <CalibrationAnalytics />}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   1. DECISION HEATMAP
   ═══════════════════════════════════════ */
function DecisionHeatmap({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No decision data yet" />;
    const rounds = Object.keys(data).sort();
    const allChoices = [...new Set(rounds.flatMap(r => Object.keys(data[r])))].sort();

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Choice Distribution by Round</h3>
            <p className={styles.sectionDesc}>Which options are most popular per round across all players</p>
            <div className={styles.heatmapGrid}>
                {/* Header */}
                <div className={styles.heatRow}>
                    <div className={styles.heatLabel} />
                    {allChoices.map(c => (
                        <div key={c} className={styles.heatColHead}>
                            <span className={styles.choiceDot} style={{ background: CHOICE_COLORS[c] || '#888' }} />
                            {c.replace('option_', 'Option ').toUpperCase()}
                        </div>
                    ))}
                    <div className={styles.heatColHead}>Total</div>
                </div>
                {/* Rows */}
                {rounds.map(r => {
                    const total = Object.values(data[r]).reduce((s, v) => s + v, 0);
                    return (
                        <div key={r} className={styles.heatRow}>
                            <div className={styles.heatLabel}>{r}</div>
                            {allChoices.map(c => {
                                const count = data[r][c] || 0;
                                const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                                const opacity = total > 0 ? 0.15 + (count / total) * 0.85 : 0.1;
                                return (
                                    <div key={c} className={styles.heatCell} style={{
                                        background: `${CHOICE_COLORS[c] || '#888'}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`,
                                    }}>
                                        <strong>{count}</strong>
                                        <span className={styles.heatPct}>{pct}%</span>
                                    </div>
                                );
                            })}
                            <div className={styles.heatTotal}>{total}</div>
                        </div>
                    );
                })}
            </div>
            {/* Stacked bar visual */}
            <div className={styles.stackedBars}>
                {rounds.map(r => {
                    const total = Object.values(data[r]).reduce((s, v) => s + v, 0);
                    return (
                        <div key={r} className={styles.stackedRow}>
                            <span className={styles.barLabel}>{r}</span>
                            <div className={styles.barTrack}>
                                {allChoices.map(c => {
                                    const pct = total > 0 ? (data[r][c] || 0) / total * 100 : 0;
                                    return pct > 0 ? (
                                        <div key={c} className={styles.barSegment} style={{
                                            width: `${pct}%`,
                                            background: CHOICE_COLORS[c] || '#888',
                                        }} title={`${c}: ${data[r][c] || 0} (${Math.round(pct)}%)`} />
                                    ) : null;
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   2. TIME-TO-DECISION
   ═══════════════════════════════════════ */
function TimeToDecision({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No timing data yet" />;
    const rounds = Object.keys(data).sort();
    const maxAvg = Math.max(...rounds.map(r => data[r].avg_seconds || 0));

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Decision Speed Analytics</h3>
            <p className={styles.sectionDesc}>How long players take to commit decisions per round</p>
            <div className={styles.timingGrid}>
                {rounds.map(r => {
                    const d = data[r];
                    const barW = maxAvg > 0 ? (d.avg_seconds / maxAvg) * 100 : 50;
                    return (
                        <div key={r} className={styles.timingCard}>
                            <div className={styles.timingHeader}>
                                <span className={styles.timingRound}>{r}</span>
                                <span className={styles.timingCount}>{d.count} decisions</span>
                            </div>
                            <div className={styles.timingBar}>
                                <div className={styles.timingFill} style={{ width: `${barW}%` }}>
                                    <span>{d.avg_seconds}s avg</span>
                                </div>
                            </div>
                            <div className={styles.timingStats}>
                                <span>⏱ Median: <strong>{d.median_seconds}s</strong></span>
                                <span>📉 Min: <strong>{d.min}s</strong></span>
                                <span>📈 Max: <strong>{d.max}s</strong></span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   3. COHORT COMPARISON
   ═══════════════════════════════════════ */
function CohortComparison({ data, leaderboard, onNavigate, onSelectSession }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No cohort data yet" />;
    const cohorts = Object.keys(data);
    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    const [metric, setMetric] = useState('treasury');

    const maxRound = Math.max(...cohorts.flatMap(c => data[c].map(d => d.round)));
    const maxVal = Math.max(...cohorts.flatMap(c => data[c].map(d => d[metric] || 0)), 1);

    const handleDrillDown = (cohortName) => {
        if (!leaderboard || !onNavigate || !onSelectSession) return;
        const cohort = leaderboard.find(c => c.cohort_name === cohortName || c.session_id.startsWith(cohortName));
        if (cohort) {
            onSelectSession(cohort.session_id);
            onNavigate('session_viewer');
        }
    };

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Cohort KPI Trajectories</h3>
            <div className={styles.metricToggle}>
                {[
                    { m: 'treasury', label: 'Treasury', icon: '💰', title: 'Total accumulated cash reserves.' },
                    { m: 'reputation', label: 'Reputation', icon: '⭐', title: 'Public perception and brand strength scale (0-100).' },
                    { m: 'synergy', label: 'Synergy', icon: '🔗', title: 'Corporate operational efficiency multiplier.' },
                    { m: 'ebitda', label: 'EBITDA', icon: '📊', title: 'Earnings before interest, taxes, depreciation, and amortization.' }
                ].map(({ m, label, icon, title }) => (
                    <button key={m} className={`${styles.metricBtn} ${metric === m ? styles.metricActive : ''}`}
                        onClick={() => setMetric(m)} title={title}>
                        {icon} {label}
                    </button>
                ))}
            </div>
            {/* Simple line chart using CSS */}
            <div className={styles.chartContainer}>
                <div className={styles.chartYAxis}>
                    <span>{metric === 'treasury' || metric === 'ebitda' ? `$${maxVal.toFixed(0)}M` : maxVal.toFixed(1)}</span>
                    <span>{metric === 'treasury' || metric === 'ebitda' ? `$${(maxVal / 2).toFixed(0)}M` : (maxVal / 2).toFixed(1)}</span>
                    <span>0</span>
                </div>
                <div className={styles.chartBody}>
                    {/* Grid lines */}
                    {[0.25, 0.5, 0.75].map(pct => (
                        <div key={pct} className={styles.gridLine} style={{ bottom: `${pct * 100}%` }} />
                    ))}
                    {/* Lines per cohort */}
                    {cohorts.map((cname, ci) => {
                        const points = data[cname];
                        return (
                            <svg key={cname} className={styles.chartSvg}>
                                <polyline
                                    fill="none"
                                    stroke={COLORS[ci % COLORS.length]}
                                    strokeWidth="2.5"
                                    strokeLinejoin="round"
                                    points={points.map(p => {
                                        const x = maxRound > 1 ? ((p.round - 1) / (maxRound - 1)) * 100 : 50;
                                        const y = 100 - ((p[metric] || 0) / maxVal) * 100;
                                        return `${x}%,${y}%`;
                                    }).join(' ')}
                                />
                                {points.map(p => {
                                    const x = maxRound > 1 ? ((p.round - 1) / (maxRound - 1)) * 100 : 50;
                                    const y = 100 - ((p[metric] || 0) / maxVal) * 100;
                                    return <circle key={p.round} cx={`${x}%`} cy={`${y}%`} r="4"
                                        fill={COLORS[ci % COLORS.length]} />;
                                })}
                            </svg>
                        );
                    })}
                    {/* X-axis labels */}
                    <div className={styles.chartXAxis}>
                        {Array.from({ length: maxRound }, (_, i) => (
                            <span key={i}>Y{i + 1}</span>
                        ))}
                    </div>
                </div>
            </div>
            <div className={styles.legend}>
                {cohorts.map((c, i) => (
                    <span 
                        key={c} 
                        className={`${styles.legendItem} ${leaderboard?.length ? styles.clickable : ''}`}
                        onClick={() => handleDrillDown(c)}
                        title="Click to view cohort in Session Viewer"
                        style={{ cursor: 'pointer' }}
                    >
                        <span className={styles.legendDot} style={{ background: COLORS[i % COLORS.length] }} />
                        {c}
                    </span>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   4. CONVERGENCE ANALYSIS
   ═══════════════════════════════════════ */
function ConvergenceAnalysis({ data }) {
    if (!data) return <EmptyState msg="No convergence data yet" />;
    const entropy = data.choice_entropy_by_round || {};
    const capexStd = data.capex_std_by_round || {};
    const rounds = [...new Set([...Object.keys(entropy), ...Object.keys(capexStd)])].sort();
    const ci = data.convergence_index || 0.5;
    const ciPct = Math.round(ci * 100);

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Strategy Convergence Gauge</h3>
            <p className={styles.sectionDesc}>Are players making similar or diverse decisions?</p>

            {/* Big gauge */}
            <div className={styles.gaugeWrap}>
                <div className={styles.gauge}>
                    <div className={styles.gaugeFill} style={{
                        width: `${ciPct}%`,
                        background: ciPct > 70 ? '#10b981' : ciPct > 40 ? '#f59e0b' : '#ef4444'
                    }} />
                </div>
                <div className={styles.gaugeLabels}>
                    <span>🌈 Diverse</span>
                    <strong className={styles.gaugeVal}>{ciPct}% Convergence</strong>
                    <span>🎯 Uniform</span>
                </div>
            </div>

            {/* Per-round breakdown */}
            <div className={styles.convergenceGrid}>
                <div className={styles.convHeader}>
                    <span>Round</span>
                    <span title="A measure of unpredictability. Lower bits indicate players are making identical choices.">Choice Entropy</span>
                    <span title="Variance in capital expenditure. Lower deviation indicates identical spending behaviors.">CapEx StdDev</span>
                </div>
                {rounds.map(r => (
                    <div key={r} className={styles.convRow}>
                        <span className={styles.convRound}>{r}</span>
                        <span>
                            <div className={styles.miniBar}>
                                <div className={styles.miniFill} style={{
                                    width: `${Math.min((entropy[r] || 0) / 1.585 * 100, 100)}%`,
                                    background: '#8b5cf6'
                                }} />
                            </div>
                            {(entropy[r] || 0).toFixed(2)} bits
                        </span>
                        <span>
                            ${((capexStd[r] || 0) / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   5. LEARNING OUTCOMES
   ═══════════════════════════════════════ */
function LearningOutcomes({ data }) {
    if (!data) return <EmptyState msg="No learning data yet" />;
    const badges = data.badges_awarded || {};
    const categories = data.bonuses_by_category || {};

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Learning & Engagement Tracker</h3>

            <div className={styles.summaryCards}>
                <div className={styles.sumCard} title="Total automated points awarded upon reaching learning milestones.">
                    <div className={styles.sumIcon}>🎓</div>
                    <div className={styles.sumVal}>{data.learning_bonuses_total || 0}</div>
                    <div className={styles.sumLabel}>Learning Bonuses</div>
                </div>
                <div className={styles.sumCard} title="Number of physical awards or manual facilitator grade-adjustments given.">
                    <div className={styles.sumIcon}>🏅</div>
                    <div className={styles.sumVal}>{data.student_bonus_count || 0}</div>
                    <div className={styles.sumLabel}>Awards Given</div>
                </div>
                <div className={styles.sumCard} title="Unique achievement badges earned globally.">
                    <div className={styles.sumIcon}>🏆</div>
                    <div className={styles.sumVal}>{Object.keys(badges).length}</div>
                    <div className={styles.sumLabel}>Badge Types</div>
                </div>
            </div>

            {Object.keys(badges).length > 0 && (
                <div className={styles.badgeGrid}>
                    <h4>Badge Distribution</h4>
                    {Object.entries(badges).sort((a, b) => b[1] - a[1]).map(([badge, count]) => (
                        <div key={badge} className={styles.badgeRow}>
                            <span className={styles.badgeName}>{badge.replace(/_/g, ' ')}</span>
                            <div className={styles.badgeBar}>
                                <div className={styles.badgeFill} style={{
                                    width: `${Math.min((count / Math.max(...Object.values(badges))) * 100, 100)}%`
                                }} />
                            </div>
                            <span className={styles.badgeCount}>×{count}</span>
                        </div>
                    ))}
                </div>
            )}

            {Object.keys(categories).length > 0 && (
                <div className={styles.catGrid}>
                    <h4>Bonuses by Category</h4>
                    {Object.entries(categories).map(([cat, count]) => (
                        <div key={cat} className={styles.catItem}>
                            <span>{cat.replace(/_/g, ' ')}</span>
                            <strong>{count}</strong>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════
   6. RISK EXPOSURE
   ═══════════════════════════════════════ */
function RiskExposure({ data, leaderboard, onNavigate, onSelectSession }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No risk data yet" />;
    const cohorts = Object.keys(data);
    const [metric, setMetric] = useState('avg_carbon_intensity');
    const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];
    const METRICS = [
        { key: 'avg_carbon_intensity', label: '🏭 Carbon Intensity', unit: '', title: 'Average metric tons of CO2e emitted per $1M revenue.' },
        { key: 'avg_natural_capital_debt', label: '🌍 Natural Capital Debt', unit: '', title: 'Unmitigated ecological damages demanding future environmental remediation.' },
        { key: 'avg_social_license', label: '🤝 Social License', unit: '', title: 'Level of ongoing community trust and stakeholder approval.' },
        { key: 'avg_governance_risk', label: '⚖️ Governance Risk', unit: '', title: 'Exposure to regulatory fines, internal corruption, or oversight failure.' },
    ];

    const maxVal = Math.max(...cohorts.flatMap(c => data[c].map(d => d[metric] || 0)), 1);

    const handleDrillDown = (cohortName) => {
        if (!leaderboard || !onNavigate || !onSelectSession) return;
        const cohort = leaderboard.find(c => c.cohort_name === cohortName || c.session_id.startsWith(cohortName));
        if (cohort) {
            onSelectSession(cohort.session_id);
            onNavigate('session_viewer');
        }
    };

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Risk Exposure Trends</h3>
            <div className={styles.metricToggle}>
                {METRICS.map(m => (
                    <button key={m.key} className={`${styles.metricBtn} ${metric === m.key ? styles.metricActive : ''}`}
                        onClick={() => setMetric(m.key)} title={m.title}>
                        {m.label}
                    </button>
                ))}
            </div>
            {/* Risk chart */}
            <div className={styles.riskTable}>
                {cohorts.map((cname, ci) => (
                    <div key={cname} className={styles.riskCohort}>
                        <div 
                            className={styles.riskName}
                            onClick={() => handleDrillDown(cname)}
                            title="Click to view cohort in Session Viewer"
                            style={{ cursor: 'pointer', textDecoration: 'underline', textDecorationColor: 'var(--border-subtle)' }}
                        >
                            <span className={styles.legendDot} style={{ background: COLORS[ci % COLORS.length] }} />
                            {cname}
                        </div>
                        <div className={styles.riskBars}>
                            {data[cname].map(d => (
                                <div key={d.round} className={styles.riskBarWrap} title={`R${d.round}: ${(d[metric] || 0).toFixed(1)}`}>
                                    <div className={styles.riskBar} style={{
                                        height: `${maxVal > 0 ? ((d[metric] || 0) / maxVal) * 100 : 0}%`,
                                        background: COLORS[ci % COLORS.length],
                                    }} />
                                    <span className={styles.riskRound}>Y{d.round}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   7. CALIBRATION (PLAN_Calibration_Analytics Phase 4)
   Self-fetching: the calibration aggregate lives on its own endpoint so the
   heavy /god/analytics payload is untouched. Auth-scoped server-side
   (facilitators see only their own cohorts).
   ═══════════════════════════════════════ */
function CalibrationAnalytics() {
    const [cal, setCal] = useState(null);
    const [calLoading, setCalLoading] = useState(true);
    useEffect(() => {
        fetch(`${API}/api/admin/calibration-analytics`, { credentials: 'include' })
            .then(r => (r.ok ? r.json() : null))
            .then(d => setCal(d))
            .catch(() => {})
            .finally(() => setCalLoading(false));
    }, []);

    if (calLoading) return <div className={styles.loading}>Loading calibration…</div>;
    if (!cal || !cal.teams?.length) {
        return <EmptyState msg="No scored predictions yet. Enable 🔮 Predictions (and 🎰 Confidence) in Pedagogical Scaffolding — data appears after teams commit their first predicted round." />;
    }

    const withConf = cal.teams.filter(t => t.mean_confidence != null && t.hit_rate != null);
    const sorted = [...cal.teams].filter(t => t.overconfidence != null).sort((a, b) => b.overconfidence - a.overconfidence);
    const W = 420, H = 280, padL = 46, padB = 40, padT = 16, padR = 16;
    const iw = W - padL - padR, ih = H - padT - padB;
    const xOf = c => padL + ((c - 0.5) / 0.5) * iw;
    const yOf = h => padT + (1 - h) * ih;

    return (
        <div>
            {/* Teleprompter line — read this aloud in the debrief */}
            <div style={{ padding: '10px 14px', borderRadius: 10, marginBottom: 14, background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.3)', fontSize: '0.82rem', color: '#fbbf24', fontWeight: 600 }}
                 data-tooltip="A ready-to-read debrief prompt generated from the latest round's prediction results.">
                📢 {cal.teleprompter_line}
            </div>

            {withConf.length > 0 && (
                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                    <div>
                        <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#8899a6', marginBottom: 6 }}>
                            Confidence vs accuracy (one dot per team)
                        </div>
                        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: 460 }} aria-label="Team calibration scatter">
                            <line x1={padL} y1={yOf(0)} x2={W - padR} y2={yOf(0)} stroke="rgba(148,163,184,0.35)" />
                            <line x1={padL} y1={yOf(0)} x2={padL} y2={padT} stroke="rgba(148,163,184,0.35)" />
                            {[0, 0.5, 1].map(v => (
                                <text key={v} x={padL - 6} y={yOf(v) + 3} textAnchor="end" fontSize="9" fill="#8899a6">{Math.round(v * 100)}%</text>
                            ))}
                            {[0.5, 0.75, 1].map(v => (
                                <text key={v} x={xOf(v)} y={H - padB + 14} textAnchor="middle" fontSize="9" fill="#8899a6">{Math.round(v * 100)}%</text>
                            ))}
                            <text x={padL + iw / 2} y={H - 8} textAnchor="middle" fontSize="9" fill="#64748b">mean stated confidence</text>
                            <text x={12} y={padT + ih / 2} textAnchor="middle" fontSize="9" fill="#64748b" transform={`rotate(-90 12 ${padT + ih / 2})`}>realised hit-rate</text>
                            <line x1={xOf(0.5)} y1={yOf(0.5)} x2={xOf(1)} y2={yOf(1)} stroke="rgba(52,211,153,0.5)" strokeDasharray="4 4" />
                            <text x={xOf(0.98)} y={yOf(1) + 12} textAnchor="end" fontSize="8.5" fill="#34d399">perfect calibration</text>
                            {withConf.map((t, i) => (
                                <g key={i}>
                                    <circle cx={xOf(t.mean_confidence)} cy={yOf(t.hit_rate)} r="6"
                                        fill={t.overconfidence > 0.1 ? '#f87171' : t.overconfidence < -0.1 ? '#fbbf24' : '#34d399'} fillOpacity="0.8">
                                        <title>{t.cohort_name} · {t.player_id} — {Math.round(t.mean_confidence * 100)}% confident, {Math.round(t.hit_rate * 100)}% right over {t.rounds_predicted} round(s)</title>
                                    </circle>
                                </g>
                            ))}
                        </svg>
                        <div style={{ fontSize: 'var(--type-caption)', color: '#8899a6', marginTop: 4 }}>
                            🔴 above the line = overconfident · 🟡 below = underconfident · 🟢 on it = calibrated
                        </div>
                    </div>

                    <div style={{ minWidth: 240 }}>
                        <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#8899a6', marginBottom: 6 }}>
                            Cohort hit-rate by round
                        </div>
                        {(cal.round_trend || []).map(r => (
                            <div key={r.round} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '2px 0', fontSize: '0.76rem' }}>
                                <span style={{ width: 28, color: '#8899a6' }}>R{r.round}</span>
                                <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(148,163,184,0.15)' }}>
                                    <div style={{ width: `${Math.round((r.hit_rate || 0) * 100)}%`, height: '100%', borderRadius: 4, background: (r.hit_rate || 0) >= 0.6 ? '#34d399' : (r.hit_rate || 0) >= 0.35 ? '#fbbf24' : '#f87171' }} />
                                </div>
                                <span style={{ width: 60, textAlign: 'right', color: '#cbd5e1' }}>{r.hit_rate == null ? '—' : `${Math.round(r.hit_rate * 100)}%`} <span style={{ color: '#64748b' }}>({r.n})</span></span>
                            </div>
                        ))}
                        <div style={{ fontSize: 'var(--type-caption)', color: '#64748b', marginTop: 6, fontStyle: 'italic' }}>
                            A rising bar = the cohort's mental model of the system is sharpening.
                        </div>
                    </div>
                </div>
            )}

            {sorted.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#8899a6', marginBottom: 6 }}>
                        Most over- / under-confident
                    </div>
                    {[...sorted.slice(0, 3), ...sorted.slice(-2).filter(t => !sorted.slice(0, 3).includes(t))].map((t, i) => (
                        <div key={i} style={{ display: 'flex', gap: 10, fontSize: '0.78rem', color: '#cbd5e1', padding: '3px 0' }}>
                            <span style={{ color: t.overconfidence > 0.1 ? '#f87171' : t.overconfidence < -0.1 ? '#fbbf24' : '#34d399', fontWeight: 800, width: 56 }}>
                                {t.overconfidence >= 0 ? '+' : ''}{Math.round(t.overconfidence * 100)} pts
                            </span>
                            <span>{t.cohort_name} · {t.player_id}</span>
                            <span style={{ color: '#64748b' }}>({Math.round((t.mean_confidence || 0) * 100)}% conf → {Math.round((t.hit_rate || 0) * 100)}% hit, {t.rounds_predicted} rounds)</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}


function EmptyState({ msg }) {
    return (
        <div className={styles.empty}>
            <span className={styles.emptyIcon}>📭</span>
            <p>{msg}</p>
            <p className={styles.emptyHint}>Play through some rounds to generate analytics data.</p>
        </div>
    );
}
